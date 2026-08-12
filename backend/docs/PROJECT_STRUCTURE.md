# Project Structure

The backend uses Flask's application factory pattern with blueprints grouped by domain:

- `app/api/auth`
- `app/api/devices`
- `app/api/commands`
- `app/api/profile`
- `app/api/activity`
- `app/api/notifications`
- `app/api/health`
- `app/sockets`
# Project Structure

## Layout

- `app/api/` - Flask blueprints
- `app/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic request/response schemas
- `app/services/` - business logic
- `app/sockets/` - Socket.IO connection and event handling
- `app/middleware/` - error handlers and security middleware
- `app/config/` - environment configuration
- `tests/` - pytest suite
- `docs/` - operational documentation
