"""Check for overlapping tracks between two JSON files."""
import json
import glob

# Get all JSON files sorted by timestamp
json_files = sorted(glob.glob('data/spotify_plays_*.json'))

if len(json_files) < 2:
    print("Need at least 2 files to compare!")
    exit()

# Load the last two files
file1 = json_files[-2]
file2 = json_files[-1]

with open(file1) as f:
    data1 = json.load(f)
    tracks1 = data1['tracks']

with open(file2) as f:
    data2 = json.load(f)
    tracks2 = data2['tracks']

print(f"File 1: {file1}")
print(f"  Tracks: {len(tracks1)}")
print(f"  Range: {tracks1[0]['played_at']} → {tracks1[-1]['played_at']}")

print(f"\nFile 2: {file2}")
print(f"  Tracks: {len(tracks2)}")
print(f"  Range: {tracks2[0]['played_at']} → {tracks2[-1]['played_at']}")

# Check for overlaps using played_at timestamp (unique identifier)
timestamps1 = set(t['played_at'] for t in tracks1)
timestamps2 = set(t['played_at'] for t in tracks2)

overlap = timestamps1 & timestamps2

print(f"\n{'='*60}")
print(f"Overlap: {len(overlap)} tracks")
print(f"Expected: 0 tracks (incremental should have NO overlap)")
print(f"{'='*60}")

if overlap:
    print("\n⚠️  WARNING: Found overlapping tracks!")
    print("This shouldn't happen with incremental fetch.")
    print("\nOverlapping tracks:")
    for ts in sorted(overlap)[:5]:
        track = next(t for t in tracks1 if t['played_at'] == ts)
        print(f"  - {track['track_name']} at {track['played_at']}")
else:
    print("\n✅ No overlap - incremental fetch working correctly!")
