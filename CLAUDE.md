# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django REST API backend for an Australian mortgage repayment calculator. Visitors can calculate repayments without an account; Auth0-authenticated users can save/manage scenarios. Pairs with a separate frontend repo (see `..\australian-mortgage-repayment-calculator-frontend`).

## Commands

All Django management commands run from the `calculator/` subdirectory (it contains `manage.py`), not the repo root.

```powershell
venv\Scripts\activate
cd calculator

python manage.py runserver
python manage.py migrate
python manage.py makemigrations

# Run the full test suite (pytest-django, uses conftest.py at calculator/ to bootstrap Django)
pytest

# Single file / single test
pytest mortgage/tests/test_mortgages.py
pytest mortgage/tests/test_scenarios_api.py::test_name -v
```

No `pytest.ini`/`pyproject.toml` config exists — pytest-django picks up settings via `calculator/conftest.py`, which calls `django.setup()` against `calculator.settings`. Tests default to SQLite unless `DB_ENGINE`/`DATABASE_URL` env vars are set.

Env vars are loaded from a `.env` file at the repo root (`python-dotenv`, loaded in `settings.py`). Required keys: `DATABASE_URL` (or `DB_ENGINE=postgresql` + `DB_*`), `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `SECRET_KEY`, `DEBUG`.

## Architecture

Two Django apps: `mortgage` (calculation + saved scenarios) and `users` (Auth0-backed user model).

### Calculation layering — read this before touching calculation code

There are **two parallel calculation implementations** with a strict unit-conversion boundary between them:

- `mortgage/calculators.py` — `MortgageCalculator` ABC with `PrincipalAndInterest`/`InterestOnly` strategy classes. **Not used by the live API path.** Expects `annual_rate` as a decimal fraction (0.065 = 6.5%) and never divides by 100.
- `mortgage/services.py` — `MortgageCalculatorService`, the actual implementation behind `/api/mortgage/calculate/`. Reimplements the P&I/I-O amortisation formulas itself (does not call `calculators.py`). Expects `annual_rate` as a **percent** (6.5) and does the `/100` conversion internally in `_calculate_standard`/`_calculate_fixed_with_revert` only — never in views, serializers, or `calculators.py`.

When changing rate handling, check which layer you're in — mixing the two unit conventions silently doubles or nullifies interest calculations.

`MortgageCalculatorService.calculate()` also handles:
- Fixed-rate loans that revert to a variable rate after `fixed_rate_period_years` (`_calculate_fixed_with_revert`)
- Offset accounts (variable-rate loans only) — computed by re-running the calculation with `offset_amount=0` and diffing total interest (`offset_savings`)
- Rate sensitivity analysis (`_calculate_rate_sensitivity`) — reruns the calculation at `annual_rate ± rate_change_step` (default 0.25%). For fixed/interest-only loans the *revert* rate is varied instead of the quoted rate, since that's the rate actually exposed to future changes.
- Amortisation schedules are built to the cent (`ROUND_HALF_UP`), then totals are summed from the schedule rows rather than computed independently, so a returned `total_interest`/`total_repayment` always ties out to the `schedule` array. The final period's principal/closing balance is nudged to force the balance to exactly `0.00` (rounding residue from per-period quantization).

### Auth

`users/auth0.py` (`Auth0JWTAuthentication`) validates Auth0 RS256 JWTs against the tenant's JWKS endpoint (cached in-process for 300s), then gets-or-creates a local `User` keyed on `auth0_id` (the JWT `sub` claim). This is the `DEFAULT_AUTHENTICATION_CLASSES` for all of DRF (`settings.py`), so `CalculateView` explicitly opts out with `authentication_classes = []` / `permission_classes = [AllowAny]` to stay anonymous-accessible — any new public endpoint needs the same override, since the global default is `IsAuthenticated`.

### Data model

`SavedScenario` (belongs to a `User`) has many `LoanSplit` rows (ordered, unique on `scenario + order`) — this is how split loans (e.g. 70% fixed / 30% variable) are represented. Each `LoanSplit` stores both the calculation inputs and the resulting `repayment_amount`/`total_interest`/`total_repayment` (computed once at save time, not recalculated on read).

### API surface

- `POST /api/mortgage/calculate/` — anonymous, stateless calculation (no DB write)
- `/api/mortgage/scenarios/` — `SavedScenarioViewSet`, standard DRF router CRUD, scoped to `request.user` via `get_queryset`
- `/api/users/me/` — current user profile
- `/api/schema/swagger-ui/`, `/api/schema/redoc/` — drf-spectacular interactive docs

## Deployment

Deployed to Digital Ocean via `Procfile`: gunicorn with `--chdir calculator` (app code lives in the `calculator/` subdirectory, not repo root) and `release: migrate --pythonpath calculator`. `DATABASE_URL` (injected by DO) takes precedence over `DB_ENGINE`/`DB_*` vars over the SQLite fallback — see the precedence comment in `settings.py`.
