# Australian Mortgage Repayment Calculator — Backend

## Planning

### Concept

The Australian Mortgage Repayment Calculator is a tool that helps Australians understand and compare their home loan options. Users can calculate repayments for variable and fixed rate loans, model offset accounts and split loans across multiple rate types. Authenticated users can save and revisit scenarios over time.

### User Types

| User | Description |
|------|-------------|
| **Visitor** | Unauthenticated. Can use the calculator and view results, but cannot save scenarios. |
| **Authenticated User** | Logged in via Auth0. Can save, view, update, and delete their own mortgage scenarios. |

### Database Schema

```
┌──────────────────────┐         ┌──────────────────────────────────────┐
│       User           │         │           SavedScenario              │
│──────────────────────│         │──────────────────────────────────────│
│ id (PK)              │ 1     * │ id (PK)                              │
│ username             │─────────│ user (FK → User)                     │
│ email                │         │ name                                 │
│ auth0_sub            │         │ created_at                           │
└──────────────────────┘         │ updated_at                           │
                                 └──────────────────┬───────────────────┘
                                                    │ 1
                                                    │
                                                    │ *
                                 ┌──────────────────┴───────────────────┐
                                 │              LoanSplit               │
                                 │──────────────────────────────────────│
                                 │ id (PK)                              │
                                 │ scenario (FK → SavedScenario)        │
                                 │ order                                │
                                 │ loan_amount                          │
                                 │ annual_rate                          │
                                 │ rate_type (variable / fixed)         │
                                 │ repayment_type (P&I / interest only) │
                                 │ repayment_frequency                  │
                                 │ loan_term_years                      │
                                 │ fixed_rate_period_years              │
                                 │ revert_rate                          │
                                 │ offset_amount                        │
                                 │ repayment_amount                     │
                                 │ total_interest                       │
                                 │ total_repayment                      │
                                 └──────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.12
- PostgreSQL

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/nictsc/australian-mortgage-repayment-calculator-backend.git
cd australian-mortgage-repayment-calculator-backend
```

**2. Create and activate a virtual environment**

*Mac/Linux:*
```bash
python3 -m venv venv
source venv/bin/activate
```

*Windows:*
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

Create a `.env` file in the project root:

```
DATABASE_URL=postgres://user:password@localhost:5432/mortgage_calculator
AUTH0_DOMAIN=your-tenant.au.auth0.com
AUTH0_AUDIENCE=your-api-identifier
SECRET_KEY=your-django-secret-key
DEBUG=True
```

**5. Apply migrations**

```bash
cd calculator
python manage.py migrate
```

**6. Run the development server**

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

Interactive API docs are available at:
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`

---

## API Spec

### Mortgage

| Method | URL | Description | Auth Required | Success | Failure |
|--------|-----|-------------|:---:|---------|---------|
| `POST` | `/api/mortgage/calculate/` | Calculate mortgage repayments | No | 200 | 400 |
| `GET` | `/api/mortgage/scenarios/` | List all saved scenarios | Yes | 200 | 401 |
| `POST` | `/api/mortgage/scenarios/` | Save a new scenario | Yes | 201 | 400, 401 |
| `GET` | `/api/mortgage/scenarios/{id}/` | Retrieve a saved scenario | Yes | 200 | 401, 404 |
| `PUT` | `/api/mortgage/scenarios/{id}/` | Update a saved scenario | Yes | 200 | 400, 401, 404 |
| `PATCH` | `/api/mortgage/scenarios/{id}/` | Partially update a saved scenario | Yes | 200 | 400, 401, 404 |
| `DELETE` | `/api/mortgage/scenarios/{id}/` | Delete a saved scenario | Yes | 204 | 401, 404 |

### Users

| Method | URL | Description | Auth Required | Success | Failure |
|--------|-----|-------------|:---:|---------|---------|
| `GET` | `/api/users/me/` | Retrieve the current user's profile | Yes | 200 | 401 |
| `PATCH` | `/api/users/me/` | Update the current user's profile | Yes | 200 | 400, 401 |

### Calculate Request Body

```json
{
  "loan_amount": 600000,
  "annual_rate": 6.25,
  "rate_type": "fixed",
  "repayment_type": "principal_and_interest",
  "repayment_frequency": "monthly",
  "loan_term_years": 30,
  "fixed_rate_period_years": 2,
  "revert_rate": 7.00,
  "offset_amount": 20000
}
```

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `loan_amount` | decimal | Yes | Loan amount in AUD |
| `annual_rate` | decimal | Yes | Annual interest rate (%) |
| `rate_type` | string | Yes | `variable` or `fixed` |
| `repayment_type` | string | Yes | `principal_and_interest` or `interest_only` |
| `repayment_frequency` | string | Yes | `weekly`, `fortnightly`, or `monthly` |
| `loan_term_years` | integer | Yes | Loan term in years (max 40) |
| `fixed_rate_period_years` | integer | No | Fixed period length (required if `rate_type` is `fixed`) |
| `revert_rate` | decimal | No | Variable rate applied after fixed period expires |
| `offset_amount` | decimal | No | Offset account balance (variable rate loans only) |
