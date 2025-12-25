# Learning Documentation - Spotify Data Pipeline

A record of technical concepts, decisions, and lessons learned while building this project.

---

## Table of Contents
1. [AWS Concepts](#aws-concepts)
2. [Python Best Practices](#python-best-practices)
3. [Data Engineering Patterns](#data-engineering-patterns)
4. [Debugging & Troubleshooting](#debugging--troubleshooting)
5. [Interview Talking Points](#interview-talking-points)

---

## AWS Concepts

### Lambda Deployment Package
**What:** A .zip file containing your code + all dependencies
**Why:** Lambda is a blank environment - you must provide everything
**How:**
```bash
pip install -r requirements.txt -t package/  # Install TO a folder
cp src/*.py package/                          # Add your code
zip -r lambda.zip package/                    # Zip it all
```

**Key Learning:** Lambda doesn't install packages at runtime. They're pre-installed in the .zip and extracted when Lambda starts.

### IAM Roles & Permissions
**Concept:** Lambda needs explicit permission to access other AWS services

**Created:**
- Role: `spotify-lambda-role`
- Permissions: S3 read/write, CloudWatch Logs

**Command:**
```bash
aws iam create-role --role-name spotify-lambda-role --assume-role-policy-document '{...}'
aws iam put-role-policy --role-name spotify-lambda-role --policy-name spotify-s3-access --policy-document '{...}'
```

**Interview Answer:** "I use IAM roles to grant Lambda least-privilege access. The role allows Lambda to assume it (trust policy), and attached policies define what actions it can perform on which resources."

### S3 Date Partitioning
**Pattern:** `s3://bucket/raw/year=2025/month=12/day=25/file.json`

**Why:**
- Efficient queries (scan only relevant partitions)
- Standard for data lakes
- Works with Athena, Spark, dbt

**Code:**
```python
now = datetime.now(timezone.utc)
s3_key = f"raw/year={now.year}/month={now.month:02d}/day={now.day:02d}/file.json"
```

### Lambda vs Step Functions
**Lambda:**
- Worker - does ONE task
- Max 15 minutes
- Triggered by events/schedule

**Step Functions:**
- Manager - orchestrates multiple Lambdas
- Visual workflow
- Handles retries, branching, parallel execution

**Use Lambda when:** Simple, single task
**Use Step Functions when:** Complex workflow with multiple steps

---

## Python Best Practices

### Timezone Handling (CRITICAL)
**Rule:** ALWAYS use UTC everywhere

**Wrong:**
```python
datetime.now()  # Uses local timezone - BAD
datetime.fromtimestamp(ts / 1000)  # Local timezone - BAD
```

**Correct:**
```python
datetime.now(timezone.utc)  # Always UTC
datetime.fromtimestamp(ts / 1000, tz=timezone.utc)  # Explicit UTC
```

**Formatting:**
```python
# Best practice - clean and consistent
now.strftime("%Y-%m-%dT%H:%M:%SZ")  
# Returns: "2025-12-25T08:00:00Z"
```

**Why Z?** "Zulu time" = UTC (military/aviation term)

### Exception Handling with boto3
**Wrong:**
```python
except s3.exceptions.NoSuchKey:  # s3 is a client, doesn't have .exceptions
```

**Correct:**
```python
from botocore.exceptions import ClientError

try:
    s3.get_object(Bucket=bucket, Key=key)
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchKey':
        # Handle missing file
    else:
        raise  # Re-raise other errors
```

### Dependency Injection Pattern
**Problem:** Creating `boto3.client('s3')` in every function is wasteful

**Solution Options:**

**Option A - Global (not recommended):**
```python
_s3_client = boto3.client('s3')  # Global state, hard to test
```

**Option B - Dependency Injection (recommended):**
```python
def save_to_s3(data, bucket, s3_client=None):
    s3 = s3_client or boto3.client('s3')  # Allow mocking for tests
    s3.put_object(...)
```

**Option C - Class (best for grouped functions):**
```python
class S3Storage:
    def __init__(self, bucket):
        self.bucket = bucket
        self.s3 = boto3.client('s3')  # Created once
```

---

## Data Engineering Patterns

### Incremental Loading
**Concept:** Only fetch new data since last run (don't re-fetch everything)

**Pattern:**
1. Track state (last processed timestamp)
2. Fetch only data after that timestamp
3. Update state with newest timestamp

**Code:**
```python
# Load state
last_ts = load_state_from_s3(bucket)

# Fetch incrementally
if last_ts:
    tracks = client.get_recent_plays_since(last_ts)  # Only new
else:
    tracks = client.get_recently_played(limit=50)  # First run

# Update state
latest_ts = max(track['played_at_timestamp'] for track in tracks)
save_state_to_s3(latest_ts, bucket)
```

**Benefits:**
- Efficient (less data transferred)
- No duplicates (if state management is correct)
- Standard pattern in data pipelines

### State Management
**Purpose:** Remember what was already processed

**Storage options:**
- Local file (dev/testing)
- S3 (serverless, simple)
- DynamoDB (more robust, queryable)
- Database (production systems)

**Our choice:** S3 JSON file
**Why:** Simple, cheap, survives Lambda restarts

---

## Debugging & Troubleshooting

### CloudWatch Logs for Lambda
**View real-time logs:**
```bash
aws logs tail /aws/lambda/function-name --follow --region eu-west-1
```

**Common issues:**
- `timeout` - Lambda ran longer than timeout setting
- `No module named 'X'` - Missing dependency in .zip
- `Permission denied` - IAM role missing permission

### Terminal Pager (`:` prompt)
**What:** Output too long, terminal uses a pager (like `less`)

**Controls:**
- `Space` - Next page
- `q` - Quit
- `/search` - Search for text
- `G` - Go to end
- `g` - Go to beginning

### OAuth Token Refresh in Lambda
**Problem:** Tokens expire after 1 hour

**How spotipy handles it:**
1. Downloads cached token from S3 (may be expired)
2. Checks if `access_token` is expired
3. If yes: uses `refresh_token` to get new `access_token`
4. Updates cache file in `/tmp/`

**The bug:** `/tmp/` is deleted when Lambda finishes, refreshed token is lost

**The fix:** Upload refreshed token back to S3 after authentication
```python
if is_lambda:
    s3.upload_file(cache_path, bucket, 'secrets/spotify_token')
```

### Spotify API Limitations
**Recently Played Endpoint:**
- Returns max 50 plays per request
- NOT time-based (despite docs saying "~2 weeks")
- For heavy listeners: 50 plays ≈ 1 day

**Implication:** Run pipeline every 12-24 hours to avoid data loss

**Pagination:**
- `after` parameter: Get plays AFTER timestamp (going forward)
- `before` parameter: Get plays BEFORE timestamp (going backward)

---

## Interview Talking Points

### How do you handle secrets in Lambda?
"For development, I use environment variables stored encrypted at rest by AWS. For production, I'd use AWS Secrets Manager to store credentials with automatic rotation. Lambda fetches secrets at runtime using boto3. I never commit secrets to git and use IAM policies to restrict who can view Lambda configurations."

### How do you deploy Lambda functions with dependencies?
"I create a deployment package by installing dependencies into a local directory using `pip install -t`, then copying my code into the same directory, and zipping it all together. Lambda extracts this .zip in its execution environment. For larger projects, I'd use Lambda Layers for shared dependencies or containerize with Docker."

### How do you ensure data quality in pipelines?
"I implement incremental loading with state management to prevent duplicates. All timestamps are stored in UTC to avoid timezone issues. I use proper error handling with specific exception catching, and log all operations to CloudWatch for debugging. Data is partitioned by date in S3 for efficient querying."

### Explain your pipeline architecture
"The pipeline runs on AWS Lambda triggered by EventBridge on a schedule. It authenticates with Spotify using OAuth with token refresh, fetches recently played tracks incrementally based on saved state in S3, transforms the data to a simplified schema, saves it to S3 with date partitioning, and updates the state for the next run. All code is version controlled and deployed via AWS CLI."

---

## Commands Reference

### AWS CLI Common Commands
```bash
# Lambda
aws lambda invoke --function-name NAME response.json
aws lambda update-function-code --function-name NAME --zip-file fileb://package.zip

# S3
aws s3 ls s3://bucket/prefix/
aws s3 cp s3://bucket/key - | python -m json.tool  # View JSON from S3
aws s3 mb s3://bucket-name  # Create bucket

# CloudWatch Logs
aws logs tail /aws/lambda/function-name --follow

# IAM
aws iam create-role --role-name NAME --assume-role-policy-document '{...}'
aws iam put-role-policy --role-name NAME --policy-name POLICY --policy-document '{...}'

# Get current user
aws sts get-caller-identity
```

### Python Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
deactivate
```

### Git
```bash
git add -A
git commit -m "message"
git push origin main
```

---

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| Python 3.11.7 | Lambda compatibility, stable ecosystem |
| eu-west-1 region | Close to Barcelona, mature region |
| S3 for storage | Simple, cheap, standard for data lakes |
| State in S3 | Survives Lambda restarts, simple |
| Environment variables for secrets | Simple for learning, will migrate to Secrets Manager later |
| 12-hour schedule | Balance between data loss risk and cost |
| Incremental loading | Efficient, prevents duplicates |
| UTC everywhere | Consistent, no DST issues |

---

## Mistakes & Lessons

### Timezone Hell (Day 3)
**Mistake:** Mixed `datetime.now()` (local) with `datetime.utcnow()` and manual string formatting

**Lesson:** Pick ONE approach and use it everywhere. We chose: `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`

**Time wasted:** ~3 hours debugging inconsistent timestamps

### Token Refresh Not Uploaded
**Mistake:** Assumed spotipy's token refresh would persist in Lambda

**Lesson:** Lambda's `/tmp/` is ephemeral. Anything that changes must be explicitly saved to S3.

**Impact:** Would fail after refresh_token expires (months later, but bad)

### Exception Class Error
**Mistake:** Used `s3.exceptions.NoSuchKey` (doesn't exist)

**Lesson:** boto3 exceptions are in `botocore.exceptions.ClientError`. Always import and check error codes.

**Impact:** Code would crash if state file missing (on first run)

---

## Next Steps

- [ ] Add EventBridge scheduling (every 12 hours)
- [ ] Test automated runs
- [ ] Week 2: dbt transformation layer
- [ ] Week 5: Migrate to Secrets Manager
- [ ] Week 5: Refactor to S3Storage class