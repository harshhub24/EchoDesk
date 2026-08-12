# EchoDesk Backend

Production-oriented Flask backend for a personal remote device management system.

## Stack

- Flask 3.x
- SQLAlchemy 2.0 / Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- Flask-SocketIO
- Pydantic v2
- PostgreSQL

## Run locally

1. Copy `.env.example` to `.env` and set `DATABASE_URL`, `SECRET_KEY`, and `JWT_SECRET_KEY`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run the app with `python run.py` from the `backend/` directory.

## API

All responses use the shape:

```json
{
  "success": true,
  "message": "",
  "data": {}
}
```

and errors use:

```json
{
  "success": false,
  "message": "",
  "error": {}
}
```
# EchoDesk Backend

EchoDesk is a production-oriented Flask backend for managing personally owned and explicitly authorized devices.

## Stack

- Flask 3.x
- Python 3.12+
- PostgreSQL
- SQLAlchemy 2.0 + Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- Flask-SocketIO
- Pydantic v2
- pytest

## Quick Start

1. Create a virtual environment and install dependencies from `requirements.txt`.
2. Copy `.env.example` to `.env` and set secure secrets.
3. Initialize the database with Flask-Migrate.
4. Run `python run.py` for development or `gunicorn run:app` in production.

## API Base

All REST endpoints live under `/api/v1`.

## Notes

- The backend only models legitimate remote device management workflows for authorized devices.
- No stealth, persistence, hidden execution, or unauthorized access logic is implemented.
