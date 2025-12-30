with plays as (
    select * from {{ ref('stg_plays') }}
),

artists as (
    select * from {{ ref('dim_artists') }}
)

select
    plays.played_at,
    plays.track_id,
    plays.track_name,
    plays.album_id,
    plays.album_name,
    plays.release_date,
    plays.duration_ms,
    plays.popularity as track_popularity,
    plays.artist_id,
    plays.artist_name,
    artists.genres as artist_genres,
    artists.followers as artist_followers,
    artists.popularity as artist_popularity
from plays
inner join artists on plays.artist_id = artists.artist_id