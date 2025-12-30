with artists as (
    select * from {{ ref('stg_artists') }}
)

select
    artist_id,
    artist_name,
    genres,
    followers,
    popularity,
    image_url
from artists