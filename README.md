# Automated Pitch Boundary Pipeline

This project productionizes the starter pitch-boundary prototype into a small backend pipeline. It keeps the provided green-mask detector as the default implementation, but moves the surrounding workflow into validated configuration, reusable pipeline modules, progress reporting, Docker-ready service files, and focused documentation.

## What It Does

- Generates or reads a synthetic match video.
- Samples frames instead of processing every frame.
- Detects pitch boundaries with the provided mask-based detector.
- Separates valid detections from invalid or missing boundaries.
- Tracks pipeline metrics such as frames seen, sampled, skipped, valid detections, invalid detections, and failed frames.
- Reports progress and completion to the provided mock API over HTTP.

## Project Structure

```text
.
├── Dockerfile
├── docker-compose.yml
├── DECISIONS.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── synthetic_generator.py
├── synthetic_field_prototype.py
├── src/
│   └── pitch_pipeline/
│       ├── config.py
│       ├── constants.py
│       ├── detector.py
│       ├── errors.py
│       ├── models.py
│       ├── pipeline.py
│       ├── reporting.py
│       └── runner.py
└── mock_api/
    ├── app.py
    ├── Dockerfile
    └── requirements.txt
```

## Local Setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r mock_api/requirements.txt
```

PowerShell may require this for the current shell session before activating the virtual environment:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run Locally

Terminal 1:

```bash
cd mock_api
python app.py
```

Terminal 2:

```powershell
$env:PYTHONPATH="D:\others\Github\acme_ai\src"
python -m pitch_pipeline.runner
```

Expected behavior:

- The runner generates `synthetic_pitch_feed.mp4` if it does not exist.
- The pipeline samples the video.
- The mock API receives progress events at `/api/v1/jobs/progress`.
- The mock API receives a final completion event at `/api/v1/jobs/events`.

## Docker

The repository includes Docker-ready service files:

```bash
docker compose up --build
```

The compose setup starts:

- `mock_api` on port `5000`
- `runner`, configured with `MOCK_API_URL=http://mock_api:5000`

Docker Compose execution could not be verified on this local machine because WSL/Docker is unavailable. The equivalent service communication path was verified locally with Python by running the Flask mock API and the pipeline runner separately.

## Configuration

The runner loads safe defaults and supports these environment overrides:

| Variable | Purpose | Default |
| --- | --- | --- |
| `MOCK_API_URL` | Reporting service base URL | `http://localhost:5000` |
| `JOB_ID` | Job identifier included in reporting payloads | `local-run` |
| `VIDEO_PATH` | Input/output video path | `synthetic_pitch_feed.mp4` |

Configuration is validated with Pydantic. Unknown fields, unsupported detector/crop settings, missing reporting URL, and invalid numeric values fail at startup.

## Development Checks

Install development tools:

```bash
python -m pip install -r requirements-dev.txt
```

Run syntax checks:

```bash
python -m compileall src
```

Run Ruff for linting:

```bash
python -m ruff check src tests
```

Ruff checks style and common Python issues such as unused imports, import ordering, avoidable complexity, unsafe patterns, and simple refactors. The Ruff settings live in `pyproject.toml`.

Run tests:

```bash
python -m pytest
```

Test coverage is added under `tests/` and focuses on configuration validation, detector behavior, pipeline metrics, and reporting payloads.

## Key Decisions

See `DECISIONS.md` for assumptions, validation choices, performance tradeoffs, reporting behavior, Docker verification notes, and AI/LLM disclosure.

## Original Prototype

The original starter script is preserved as `synthetic_field_prototype.py` for comparison with the productionized pipeline.
