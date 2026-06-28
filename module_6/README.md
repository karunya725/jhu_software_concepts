Name: Karunya, knaraya7

Module Info: Module 6 - Deploy Anywhere / Docker Microservice Application
Due Date: 28 Jun 2026, 11:59PM

GitHub SSH URL:
git@github.com:karunya725/jhu_software_concepts.git

Docker Hub Repository:
https://hub.docker.com/r/karunya725/module_6

Docker Hub Images:
- `karunya725/module_6:web`
- `karunya725/module_6:worker`

## Overview

In this module, I refactored the Grad Café PostgreSQL + Flask analysis project into a Docker Compose microservice application. The project now runs as separate `web`, `worker`, `db`, and `rabbit` services. The Flask web service handles the dashboard and publishes task messages, while the worker service consumes RabbitMQ messages and runs the long-running data pipeline outside the web tier.

The main goal of this module was to make the application reproducible, containerized, and closer to a cloud-native microservice design.

## Architecture

The application is split into four Docker Compose services:

- `web`: Flask dashboard and HTTP endpoints
- `worker`: RabbitMQ consumer that runs background data tasks
- `db`: PostgreSQL database
- `rabbit`: RabbitMQ message broker with management UI

The task flow is:

```text
Browser
  -> Flask web service
  -> RabbitMQ task queue
  -> Worker service
  -> scrape / clean / LLM / insert pipeline
  -> PostgreSQL database
  -> Flask dashboard queries updated data
```

## Important Notes

Real secrets should not be committed to GitHub. The application reads runtime settings from environment variables. A local `.env` file is used for Docker Compose, and real secrets should remain ignored by Git.

The local LLM model file is also not committed because it is a large binary file. The `.gitignore` excludes `.gguf` files and local model folders. The worker pipeline still includes the LLM enrichment step, but the model file must exist locally in the expected model directory when running the full LLM workflow.

## Docker Installation Check

Docker Desktop should be installed before running this module.

To confirm Docker is working:

```powershell
docker run hello-world
```

A successful `hello-world` run confirms that the Docker client and Docker daemon are working.

## Fresh Install Instructions

These commands should be run from inside the `module_6` folder.

### 1. Create a local `.env` file

Create:

```text
module_6/.env
```

### 2. Build and start the services

```powershell
docker compose up -d --build
```

This starts:

```text
gradcafe_db
gradcafe_rabbit
gradcafe_web
gradcafe_worker
```

### 3. Confirm services are running

```powershell
docker compose ps
```

Expected result:

- `gradcafe_db` is running and healthy
- `gradcafe_rabbit` is running and healthy
- `gradcafe_web` is running on port `8080`
- `gradcafe_worker` is running

The web service is exposed as:

```text
http://localhost:8080/analysis
```

The RabbitMQ management UI is exposed as:

```text
http://localhost:15672
```

RabbitMQ login:

```text
guest / guest
```

## Database Setup and Seed Data

The Docker PostgreSQL service initializes the schema through:

```text
sql/initdb/01_create_tables.sql
```

The seed data file is:

```text
data/applicant_data.json
```

This file contains a small subset of the cleaned Grad Café applicant dataset so the Docker application can be run reproducibly without committing the full generated dataset.

To load the seed data into the Docker PostgreSQL database:

```powershell
docker compose run --rm worker python load_data.py
```

The seed loader reads from:

```text
/data/applicant_data.json
```

inside the worker container.

The loader inserts records idempotently using:

```sql
ON CONFLICT (p_id) DO NOTHING
```

This prevents duplicate applicant rows from being inserted if the loader is run more than once.

## Running the Flask App

After Docker Compose is running, open:

```text
http://localhost:8080/analysis
```

The dashboard displays analysis results from the PostgreSQL database.

The Flask app runs inside the `web` container on port `5000`, and Docker maps it to host port `8080`:

```text
8080:5000
```

## RabbitMQ Task Queue

The web service publishes messages to RabbitMQ instead of running long-running tasks directly.
The worker consumes from `tasks_q` and processes one task at a time.

## Web Endpoints

### Pull Data

Endpoint:

```http
POST /pull-data
```

Example test command:

```powershell
Invoke-RestMethod -Method Post http://localhost:8080/pull-data
```

Expected response includes:

```text
status : queued
task   : scrape_new_data
```

This publishes a `scrape_new_data` task to RabbitMQ. The worker consumes the task and runs the full Pull Data pipeline:

```text
scrape.py
clean_new_data.py
run_llm_on_new_data.py
insert_new_data.py
```

The worker performs the long-running work, not the Flask web process.

### Update Analysis

Endpoint:

```http
POST /update-analysis
```

Example test command:

```powershell
Invoke-RestMethod -Method Post http://localhost:8080/update-analysis
```

Expected response includes:

```text
status : queued
task   : recompute_analytics
```

The current dashboard computes analytics dynamically from PostgreSQL, so no materialized summary refresh is needed in this version. The worker still handles the task so the endpoint follows the same asynchronous microservice pattern as Pull Data.

## Worker Pipeline

The worker handles the `scrape_new_data` task by running:

```text
worker/module_2_code/pull_new_data.py
```

That script runs the following pipeline:

```text
scrape.py
clean_new_data.py
run_llm_on_new_data.py
insert_new_data.py
```

The pipeline:

1. Scrapes recent Grad Café pages.
2. Cleans newly scraped raw records.
3. Runs LLM enrichment on newly cleaned records.
4. Inserts new LLM-enriched records into PostgreSQL.

The insert step uses parameterized SQL and idempotent inserts.

## Local LLM Model

The worker pipeline includes LLM enrichment through:

```text
worker/module_2_code/run_llm_on_new_data.py
```

The local model file is expected under:

```text
worker/module_2_code/llm_hosting/models/
```

## Non-Root Containers

The `web` and `worker` Dockerfiles create and run as a non-root user named:

```text
appuser
```

To verify this:

```powershell
docker compose exec web whoami
docker compose exec worker whoami
```

Expected output:

```text
appuser
appuser
```

## Verifying RabbitMQ

Open:

```text
http://localhost:15672
```

Go to **Queues and Streams** and check:

```text
tasks_q
```

Expected indicators:

- Queue is durable
- Consumers: `1`
- Prefetch count: `1`
- Ready: `0` after tasks are processed
- Unacked: `0` after tasks are processed

## Verifying Worker Logs

After clicking **Pull Data**, run:

```powershell
docker compose logs worker --since 5m
```

Expected log sequence:

```text
Received task scrape_new_data
Running Pull Data pipeline in worker...
Running: scrape.py
Running: clean_new_data.py
Running: run_llm_on_new_data.py
Running: insert_new_data.py
Pull Data pipeline complete.
```

After clicking **Update Analysis**, run:

```powershell
docker compose logs worker --since 1m
```

Expected log sequence:

```text
Received task recompute_analytics
Update analysis requested. Current dashboard queries are dynamic.
No materialized summary refresh is needed for this version.
```

## Stopping the Application

To stop the running containers:

```powershell
docker compose down
```

To stop the containers and remove the PostgreSQL volume:

```powershell
docker compose down -v
```

Use `docker compose down -v` only when you want to reset the database.

## Docker Compose Summary

The Compose stack includes:

- PostgreSQL with a named `pgdata` volume
- RabbitMQ with the management UI exposed on port `15672`
- Flask web service exposed on port `8080`
- Worker service connected to RabbitMQ and PostgreSQL
- A read-only bind mount for the local `data/` folder

## Testing the Main Workflow

A typical verification workflow is:

```powershell
docker compose up -d --build
docker compose ps
docker compose run --rm worker python load_data.py
Invoke-RestMethod -Method Post http://localhost:8080/pull-data
Invoke-RestMethod -Method Post http://localhost:8080/update-analysis
docker compose logs worker --since 5m
```

Then open:

```text
http://localhost:8080/analysis
```

and confirm that the dashboard loads from PostgreSQL.