# Spotify Data Pipeline

End-to-end data engineering project showcasing modern data stack for portfolio and job applications.

## Project Overview

**Goal:** Build production-grade data pipeline to analyze personal Spotify listening patterns and music discovery behavior.

**Timeline:** 8 weeks (Dec 23, 2024 - Feb 16, 2025)  
**Daily Commitment:** 3-4 hours

## Architecture
```
Spotify API → Lambda (fetch) → S3 (raw) → Lambda (process) → S3 (processed)
                                              ↓
                                    Step Functions (orchestrate)
                                              ↓
                                    dbt (transform) → Snowflake
                                              ↓
                                    Airflow (schedule daily)
                                              ↓
                                    Visualization (future)
```

## Tech Stack

- **Data Source:** Spotify Web API
- **Compute:** AWS Lambda (Python)
- **Orchestration:** AWS Step Functions, Apache Airflow
- **Storage:** AWS S3, Snowflake
- **Transformation:** dbt
- **Infrastructure:** Terraform (Week 5)
- **Languages:** Python, SQL

## Weekly Plan

### Week 1: API → Lambda → S3 (Dec 23-29)
**Deliverable:** Lambda function fetching Spotify listening history to S3 on schedule

- Day 1-2: Project setup ✅, Spotify API authentication, test data fetch locally
- Day 3-4: Lambda function development and deployment, write to S3
- Day 5-7: Production code - error handling, logging, retries, tests

**Skills:** Python, boto3, AWS Lambda, S3, Spotify API, error handling

### Week 2: Step Functions Orchestration (Dec 30 - Jan 5)
**Deliverable:** Working Step Functions workflow orchestrating data ingestion

- Day 1-3: Design and implement Step Functions workflow
- Day 4-5: Error handling, retry logic, dead letter queues, SNS notifications
- Day 6-7: Deploy infrastructure, test failure scenarios, document

**Skills:** AWS Step Functions, IAM roles, SNS, CloudWatch, orchestration patterns

### Week 3: dbt Transformation Layer (Jan 6-12)
**Deliverable:** dbt project with 10+ models analyzing listening trends

- Day 1-2: Snowflake setup (30-day trial), dbt project initialization, source configuration
- Day 3-5: Build dbt models - staging → intermediate → marts
- Day 6-7: Add tests, documentation, incremental models

**Skills:** dbt, Snowflake, dimensional modeling, SQL, data quality testing

### Week 4: Airflow Integration (Jan 13-19)
**Deliverable:** Complete pipeline running end-to-end on daily schedule

- Day 1-3: Airflow setup (local), configure connections
- Day 4-5: Build DAG orchestrating Step Functions + dbt runs
- Day 6-7: Add monitoring, alerting, scheduling

**Skills:** Airflow, DAGs, operators, scheduling, monitoring

### Week 5: Infrastructure as Code (Jan 20-26)
**Deliverable:** All infrastructure defined in Terraform

- Day 1-3: Learn Terraform basics, define infrastructure for Lambda + Step Functions
- Day 4-5: Add S3 buckets, IAM roles, SNS topics to Terraform
- Day 6-7: Test deployment from scratch, refine configuration

**Skills:** Terraform, Infrastructure as Code, AWS resource management

### Week 6: Documentation & Polish (Jan 27 - Feb 2)
**Deliverable:** GitHub repo that looks professional and portfolio-ready

- Day 1-2: Comprehensive README with architecture diagrams
- Day 3-4: Code cleanup, add comments, improve structure
- Day 5-6: Create architecture diagram (draw.io or Mermaid)
- Day 7: Write blog post explaining the project

**Skills:** Technical writing, documentation, system design

### Week 7-8: Job Search Prep (Feb 3-16)
**Deliverable:** Updated CV, optimized LinkedIn, interview readiness

- Week 7: CV rewrite, LinkedIn optimization, practice project demo
- Week 8: SQL interview prep, system design practice

## Analytics Use Cases

**Data to Collect:**
- Recently played tracks (timestamp, track ID, artist, album)
- Track audio features (tempo, danceability, energy, valence)
- Artist information (genres, popularity)
- User's top tracks and artists (short/medium/long term)

**Questions to Answer:**
1. **Listening Trends:** How do my listening patterns change over time? (daily, weekly, seasonal)
2. **Discovery Patterns:** How do I discover new music? (recommendations vs playlists vs radio)
3. Genre evolution, mood analysis, artist diversity, skip behavior

## dbt Models Structure

**Staging Layer:**
- `stg_spotify__tracks`
- `stg_spotify__artists`
- `stg_spotify__listening_history`

**Intermediate Layer:**
- `int_tracks_enriched` (join track features)
- `int_listening_patterns` (aggregations by time)
- `int_discovery_events` (new artists/tracks)

**Marts Layer:**
- `fct_daily_listening` (daily aggregates)
- `dim_artists` (SCD Type 2)
- `dim_tracks`
- `rpt_listening_trends`
- `rpt_discovery_analysis`

## Project Status

### Completed ✅
- [x] Homebrew installed
- [x] Git configured
- [x] GitHub repo created
- [x] Project structure initialized
- [x] SSH key setup

### In Progress 🚧
- [ ] Python environment setup
- [ ] VSCode configuration
- [ ] AWS account and credentials
- [ ] Spotify Developer account

### Upcoming 📋
- [ ] Lambda function development
- [ ] Step Functions workflow
- [ ] dbt models
- [ ] Airflow DAGs
- [ ] Terraform infrastructure
- [ ] Documentation and blog post

## Development Setup

### Prerequisites
- Python 3.11+
- AWS CLI v2
- Terraform
- dbt-core
- Docker (optional)

### Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_secret
AWS_REGION=eu-west-1
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
```

## Skills Self-Assessment

Current → Target (by Week 8):
- API handling with error handling/pagination: 1 → 4
- AWS Lambda deployment: 3 → 4
- AWS Step Functions: 3 → 4
- boto3 (S3, CloudWatch): 3 → 4
- dbt models and best practices: 4 → 5
- Airflow DAG creation: 3 → 4
- Terraform/Infrastructure as Code: 1 → 3
- Production Python patterns: 3 → 4

*Scale: 1=Seen it, 3=Can do with docs/AI, 5=Comfortable and confident*

## Resources

- [Spotify API Docs](https://developer.spotify.com/documentation/web-api)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [dbt Learn](https://courses.getdbt.com/collections)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [DataTalks.Club](https://datatalks.club/)

## Author

**Ivan Polakovic**
- LinkedIn: [linkedin.com/in/ivanpolakovic](https://linkedin.com/in/ivanpolakovic)
- GitHub: [github.com/ipolakovic](https://github.com/ipolakovic)

---

*Last updated: Dec 22, 2024*
