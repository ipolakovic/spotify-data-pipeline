# Spotify Artist Enrichment Lambda

## Purpose
Fetches artist details (genres, followers, popularity) for all unique artists found in the plays data.

## Schedule
Runs weekly (artists data doesn't change frequently)

## Data Flow
1. Read all plays from S3
2. Extract unique artist IDs
3. Fetch artist details from Spotify API (batch requests)
4. Save to s3://bucket/artists/artist_data_YYYYMMDD.json

## Output Schema
```json
{
  "artist_id": "6qqNVTkY8uBg9cP3Jd7DAH",
  "artist_name": "Billie Eilish",
  "genres": ["pop", "electropop"],
  "followers": 123456789,
  "popularity": 98,
  "images": [...],
  "fetched_at": "2025-12-25T10:00:00Z"
}
```
