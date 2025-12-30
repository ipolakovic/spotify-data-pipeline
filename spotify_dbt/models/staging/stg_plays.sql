{{
    config(
        materialized='incremental',
        unique_key=['track_id', 'played_at']
    )
}}

with source as (
    select * from {{ source('raw', 'raw_plays') }}
    {% if is_incremental() %}
    where loaded_at > (select max(loaded_at) from {{ this }})
    {% endif %}
),

flattened as (
    select
        source.source_file,
        source.loaded_at,
        source.raw_json:fetched_at::timestamp_ntz as batch_fetched_at,
        track.value:played_at::timestamp_ntz as played_at,
        track.value:track_id::string as track_id,
        track.value:track_name::string as track_name,
        track.value:artist_id::string as artist_id,
        track.value:artist_name::string as artist_name,
        track.value:album_id::string as album_id,
        track.value:album_name::string as album_name,
        track.value:release_date::string as release_date,
        track.value:duration_ms::number as duration_ms,
        track.value:popularity::number as popularity
    from source,
    lateral flatten(input => source.raw_json:tracks) as track
),

deduplicated as (
    select *,
        row_number() over (
            partition by track_id, played_at
            order by loaded_at desc
        ) as row_num
    from flattened
)

select * from deduplicated where row_num = 1