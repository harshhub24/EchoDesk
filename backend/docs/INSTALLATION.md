# Installation

1. Create a Python 3.12+ virtual environment.
2. Install backend dependencies from `requirements.txt`.
3. Provision PostgreSQL and set `DATABASE_URL`.
4. Copy `.env.example` to `.env`.
5. Run database migrations once Alembic revisions are added.
# Installation

## Requirements

- Python 3.12 or newer
- PostgreSQL 15+ recommended
- A virtual environment manager

## Steps

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and configure `DATABASE_URL`, `SECRET_KEY`, and `JWT_SECRET_KEY`.
4. Initialize migrations:
   - `flask --app run.py db init`
   - `flask --app run.py db migrate -m "initial schema"`
   - `flask --app run.py db upgrade`
5. Start the app:
   - Development: `python run.py`
   - Production: `gunicorn run:app`
