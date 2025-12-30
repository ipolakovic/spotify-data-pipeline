with source as (
    select * from {{ source('raw', 'raw_artists') }}
),

flattened as (
    select
        source.source_file,
        source.loaded_at,
        source.raw_json:fetched_at::timestamp_ntz as batch_fetched_at,
        artist.value:artist_id::string as artist_id,
        artist.value:artist_name::string as artist_name,
        artist.value:genres::array as genres,
        artist.value:followers::number as followers,
        artist.value:popularity::number as popularity,
        artist.value:image_url::string as image_url
    from source,
    lateral flatten(input => source.raw_json:artists) as artist
),

deduplicated as (
    select *,
        row_number() over (
            partition by artist_id
            order by batch_fetched_at desc
        ) as row_num
    from flattened
)

select * from deduplicated where row_num = 1