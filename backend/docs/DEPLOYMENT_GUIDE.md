# Deployment Guide

Use Gunicorn with an async worker class compatible with Flask-SocketIO.

Recommended production steps:

1. Set environment variables for secrets and PostgreSQL.
2. Apply database migrations.
3. Run Gunicorn behind HTTPS termination.
4. Store logs outside the application container if containerized.
# Deployment Guide

## Production Checklist

1. Set strong values for `SECRET_KEY` and `JWT_SECRET_KEY`.
2. Use PostgreSQL and run migrations before first start.
3. Set `FLASK_ENV=production`.
4. Serve the application through Gunicorn.
5. Terminate TLS at a reverse proxy such as Nginx or a managed load balancer.
6. Keep logs outside the web root and rotate them.

## Run Command

```bash
gunicorn -w 4 -k eventlet run:app
```
