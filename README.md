# Marketplace API

A multi-vendor marketplace backend built with Django and Django REST Framework. It covers JWT authentication, role-based access (admin, vendor, customer) and a vendor onboarding flow where users apply for a store and an admin approves or rejects it.

## Features

- Email-based custom user model (no username) with three roles: `ADMIN`, `VENDOR`, `CUSTOMER`
- JWT auth with SimpleJWT: register, login, token refresh, logout (refresh token blacklisting), rotating refresh tokens
- Vendor onboarding: any authenticated user can apply for a store, the owner can view and update it, an admin approves or rejects it
- Store states: `PENDING`, `APPROVED`, `REJECTED`, with a conflict response (409) on invalid state changes
- Business logic kept in a service layer (`apps/vendors/services.py`), separate from views
- OpenAPI schema support through drf-spectacular
- Filtering support through django-filter, CORS through django-cors-headers
- Configuration through environment variables (django-environ), PostgreSQL ready (SQLite fallback)
- Tooling: Poetry, pytest + pytest-django + coverage, factory-boy, Ruff, pre-commit

## Tech stack

Python 3.12+, Django 6, Django REST Framework, SimpleJWT, drf-spectacular, django-filter, django-cors-headers, django-environ, PostgreSQL (psycopg 3).

## Getting started

```bash
git clone https://github.com/omarshaabandev-hub/marketplace-api.git
cd marketplace-api

# install dependencies (including dev tools)
poetry install

# configure environment
cp .env.example .env   # then edit SECRET_KEY and DATABASE_URL

# create the database schema and an admin user
poetry run python manage.py migrate
poetry run python manage.py createsuperuser

poetry run python manage.py runserver
```

### Environment variables

| Variable | Description | Example |
| --- | --- | --- |
| `SECRET_KEY` | Django secret key (required) | `change-me` |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `127.0.0.1,localhost` |
| `DATABASE_URL` | Database connection URL (defaults to SQLite) | `postgres://postgres:postgres@localhost:5432/marketplace_db` |

## API endpoints

Base path: `/api/v1/`

| Method | Endpoint | Access | Description |
| --- | --- | --- | --- |
| POST | `/users/register/` | Public | Create an account |
| POST | `/users/login/` | Public | Get access and refresh tokens |
| POST | `/users/token/refresh/` | Public | Refresh the access token |
| POST | `/users/logout/` | Authenticated | Blacklist the refresh token |
| GET | `/users/me/` | Authenticated | Current user profile |
| POST | `/vendors/apply/` | Authenticated | Apply to open a store |
| GET, PUT, PATCH | `/vendors/me/` | Vendor owner | View or update your store |
| POST | `/vendors/<id>/review/` | Admin | Approve or reject a store (`action`: `approve` or `reject`) |

Send the access token as `Authorization: Bearer <token>`. Access tokens last 60 minutes, refresh tokens 1 day.

## Project structure

```
config/           project settings (split settings), urls, wsgi/asgi
apps/
  users/          custom user model, auth views, permissions
  vendors/        vendor model, views, services, permissions
```

## Development

```bash
poetry run pytest          # tests with coverage
poetry run ruff check .    # lint
poetry run ruff format .   # format
poetry run pre-commit install
```

## Roadmap

- Products and categories
- Cart and orders
- Payments integration
- Docker setup and CI pipeline

## Author

Omar Shaaban - omarshaaban.dev@gmail.com
 README-babacc12.md…]()
