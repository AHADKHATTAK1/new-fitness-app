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

Copy the template and fill values:

```powershell
Copy-Item .env.example .env
```

4) Run the app

```powershell
.\.venv\Scripts\python.exe app.py
```

App runs locally at:

- `http://127.0.0.1:5000`

## Environment variables

Use `.env.example` as the full source of truth. Minimum required keys in `.env` are:

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
- `/healthz` → health/uptime probe endpoint
- `/create_billing_portal_session` → Stripe customer billing self-service portal
- `/backup/download/json` → full JSON backup (restore-compatible)
- `/backup/download/excel` → full Excel backup (old structure)
- `/backup/download/template` → sample Excel template (old structure)

## Helper scripts in repo

- `create_admin.py` – create admin account
- `run_migrations.py` – migration helper
- `add_tier_columns.py` – tier-related DB update helper
- `test_db_connection.py` – DB connectivity check

## Troubleshooting

- If login-protected routes return `302`, authenticate first at `/auth`.
- If `APScheduler` is missing, the app still starts; background jobs are simply disabled.
- If payment providers are not configured, keep provider keys empty and use non-provider flows locally.

## SaaS mode checklist

- Configure Stripe keys in `.env`: `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, and `STRIPE_WEBHOOK_SECRET`.
- Use `/subscription_plans` for upgrade flow and `/create_billing_portal_session` for customer self-service billing.
- Keep `SESSION_COOKIE_SECURE=1` in production (HTTPS).

## Production publish checklist

- Set strong secrets and runtime mode:
	- `FLASK_SECRET_KEY` to a long random value
	- `SESSION_COOKIE_SECURE=1` behind HTTPS
	- `DATABASE_URL` to production Postgres (non-placeholder)
- Configure billing/webhooks:
	- `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
	- Verify `/stripe/webhook` is reachable by Stripe
- Configure email notifications (staff share/revoke/resend + password reset):
	- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_EMAIL`, `SMTP_PASSWORD`
- Configure optional auth/admin:
	- `GOOGLE_CLIENT_ID`
	- `ADMIN_EMAILS`
- Use production server process:
	- `Procfile` included: `web: gunicorn --bind 0.0.0.0:$PORT app:app`
	- `gunicorn` is included in `requirements.txt`
- Verify core routes after deploy:
	- `/auth`, `/dashboard`, `/settings`, `/subscription_plans`, `/webhooks`, `/healthz`

Note: local VS Code task output may show `exit code: 1` after stopping/restarting the task terminal; startup is healthy when you see `Running on http://127.0.0.1:5000`.

## Reproducible setup

This repository includes a pinned `requirements.txt` to keep local and deployment environments consistent.

## Recent update history (March 2026)

- Subscription and access flow improvements:
	- Added/updated referral + VIP activation handling.
	- Enforced trial-aware feature access and post-payment unlock behavior.
	- Expanded plan and market handling (US/PK), including mini plan support.
	- Added staff sharing controls in settings (share, revoke, resend invite) with email notifications.
	- Added owner-visible recent staff access activity log in settings for operational audit visibility.
	- Enforced per-plan staff seat limits in sharing flow and added seat usage visibility in settings.

- Payment reliability updates:
	- Improved payment initiation user/email resolution.
	- Hardened callback/webhook processing paths and subscription extension updates.
	- Prevented avoidable 500 responses for missing Stripe webhook secret (safe ignored response).

- Webhook module stability:
	- Added safer webhook table/schema handling for older databases.
	- Added defensive counter updates for null/legacy values.
	- Verified `/webhooks`, create, test, logs, and delete flows end-to-end.

- Analytics and routing fixes:
	- Added advanced analytics route alias support.
	- Fixed missing template context values causing analytics errors.
	- Added global 500 fallback behavior and safer route error handling.

- Dashboard visibility and UI fixes:
	- Reworked dashboard stat rendering to ensure data is visible server-side and client-side.
	- Added no-cache handling for dynamic HTML responses and updated service worker caching strategy.
	- Standardized gradient text compatibility by adding `background-clip: text;` alongside `-webkit-background-clip: text;` across templates.
	- Replaced fixed month dropdown windows with data-driven month generation across key pages (dashboard, fees, expenses, bulk operations, add member, member details).
	- Enabled past month/year selection without a hardcoded historical limit.

- Import and operations enhancements:
	- Extended bulk import to support historical paid months/amount data.
	- Improved duplicate/member update handling during imports.

- Backup enhancements:
	- Added old-structure Excel backup download and restore support.
	- Added Excel template download to standardize backup file format.
	- Improved Excel restore parsing with alias support for common column names.