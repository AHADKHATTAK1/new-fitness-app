# Fitness Management (Gym Manager)

A Flask-based gym management system with member management, fee tracking, imports/exports, analytics, subscriptions, payments, webhooks, and automation workflows.

## What this project includes

- Member onboarding and profile management
- Payment and fee tracking (paid/unpaid/history)
- Bulk member import with preview and duplicate strategies
- Export center for operational reports
- Dashboard, analytics, and reports views
- Authentication, forgot/reset password, Google login support
- Subscription tiers and upgrade routes
- Webhook management and webhook delivery logs
- Background scheduler support (daily summary + automation jobs when APScheduler is available)

## Tech stack

- Python 3.x
- Flask
- SQLAlchemy
- Jinja2 templates + static assets
- Stripe + JazzCash integration hooks
- Google OAuth / Google Wallet support

## Project structure

Key files and folders:

- `app.py` – main Flask application and routes
- `models.py` – database models and session helpers
- `gym_manager.py` – core gym/business logic
- `auth_manager.py` – auth/session logic
- `payment_manager.py` – payment workflows
- `automation_manager.py` – automation orchestration
- `webhook_manager.py` – webhook and delivery logic
- `tier_routes.py` / `subscription_tiers.py` – plans and upgrade routing
- `templates/` – all UI templates
- `static/` – CSS/JS/icons/uploads/PWA files
- `gym_data/` – app data folder

## Quick start (Windows)

1) Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

Use the pinned dependencies file:

```powershell
pip install -r requirements.txt
```

3) Configure environment variables

Create a `.env` file in the project root (example below).

4) Run the app

```powershell
.\.venv\Scripts\python.exe app.py
```

App runs locally at:

- `http://127.0.0.1:5000`

## Environment variables

Create `.env` with at least:

```env
FLASK_SECRET_KEY=change-this-in-production

# Optional billing/auth providers
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
GOOGLE_CLIENT_ID=

# Optional JazzCash
JAZZCASH_MERCHANT_ID=
JAZZCASH_PASSWORD=
JAZZCASH_INTEGRITY_SALT=
JAZZCASH_RETURN_URL=http://localhost:5000/jazzcash_return

# Optional admin controls
ADMIN_EMAILS=admin@gym.com
```

## Common routes

- `/` → root redirect logic
- `/auth` → login/signup
- `/dashboard` → main dashboard
- `/add_member` → create member
- `/fees` → payment center
- `/bulk_import` → import workflow
- `/reports` → analytics reports
- `/webhooks` → webhook management

## Helper scripts in repo

- `create_admin.py` – create admin account
- `run_migrations.py` – migration helper
- `add_tier_columns.py` – tier-related DB update helper
- `test_db_connection.py` – DB connectivity check

## Troubleshooting

- If login-protected routes return `302`, authenticate first at `/auth`.
- If `APScheduler` is missing, the app still starts; background jobs are simply disabled.
- If payment providers are not configured, keep provider keys empty and use non-provider flows locally.

## Reproducible setup

This repository includes a pinned `requirements.txt` to keep local and deployment environments consistent.