# WindSight --- Technology Stack

**File:** `techstack.md`\
**Purpose:** Document the selected tools, responsibilities, and
implementation choices for the WindSight assignment.\
**Project:** Day-Ahead Wind Forecast Intelligence for UK Electricity
Procurement\
**Constraints:** January 2026 only; Elexon FUELHH actual wind generation
and WINDFOR forecasts; maximum 16-hour build.

------------------------------------------------------------------------

## 1. Stack Overview

  ------------------------------------------------------------------------
  Layer                   Technology              Purpose
  ----------------------- ----------------------- ------------------------
  Frontend framework      React                   Build the interactive
                                                  dashboard UI.

  Frontend tooling        Vite                    Local development server
                                                  and production build.

  Language                TypeScript              Catch common UI/API
                          (recommended)           integration errors
                                                  early. Plain JavaScript
                                                  is acceptable if
                                                  TypeScript would slow
                                                  delivery significantly.

  Styling                 CSS Modules or plain    Build a responsive,
                          CSS                     consistent dashboard
                                                  without unnecessary
                                                  setup. Tailwind CSS is
                                                  optional.

  Charts                  Recharts                Display
                                                  forecast-versus-actual
                                                  series and forecast
                                                  evolution.

  Backend framework       Python + FastAPI        Expose typed REST
                                                  endpoints and serve
                                                  processed data to React.

  Data processing         Pandas                  Normalize, join, filter,
                                                  and aggregate
                                                  time-series records.

  HTTP client             HTTPX                   Call Elexon APIs with
                                                  timeouts and explicit
                                                  error handling.

  Validation / schemas    Pydantic (via FastAPI)  Validate query
                                                  parameters and response
                                                  structures.

  Testing                 Pytest                  Test cutoff selection,
                                                  metric calculations,
                                                  missing data, and API
                                                  behaviour.

  API documentation       FastAPI OpenAPI /       Make backend endpoints
                          Swagger UI              easy to inspect during
                                                  development and review.

  Containerization        Docker + Docker Compose Reproduce local
                                                  development/runtime and
                                                  run frontend/backend
                                                  together.

  Source control          Git + GitHub            Version history and
                                                  public assignment
                                                  repository.

  Frontend hosting        Vercel                  Deploy the React
                                                  frontend.

  Backend hosting         A Python-compatible     Deploy the API
                          host supporting FastAPI separately from the
                          or Docker               frontend if needed.
                                                  Confirm current provider
                                                  limits before selecting
                                                  one.

  Data source             Elexon BMRS API         Retrieve FUELHH actuals
                                                  and WINDFOR forecast
                                                  history.
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 2. Frontend

### React + Vite

React owns the presentation layer: date selection, KPI cards, charts,
forecast interval tables, coverage summaries, and loading/error states.
Vite provides a fast development loop and a production build suitable
for static hosting.

### TypeScript

Use TypeScript if comfortable with it. Define API response types in one
place so the frontend and backend contract stays clear. If TypeScript
would materially slow the assignment, use JavaScript and keep the
response shapes documented.

### Recharts

Use Recharts for: - Forecast versus actual generation over delivery
intervals. - Forecast evolution by publication time, if historical
records are available. - Optional error-over-time visualization.

Charts must render backend data, not fabricated placeholder values. If
the API returns no data, show an explicit empty state.

### Styling

Use plain CSS/CSS Modules or Tailwind CSS. Choose one approach and avoid
spending time building a complex design system. Prioritize readable
axes, units, timestamps, responsive layout, and accessible labels.

------------------------------------------------------------------------

## 3. Backend

### Python + FastAPI

FastAPI provides REST endpoints, query validation, generated OpenAPI
documentation, and a clean separation between transport and business
logic.

Suggested endpoints:

  ----------------------------------------------------------------------------------------
  Endpoint                                             Purpose
  ---------------------------------------------------- -----------------------------------
  `GET /api/health`                                    Health check for local and deployed
                                                       service.

  `GET /api/dashboard?date=YYYY-MM-DD`                 Return interval data, daily
                                                       metrics, and coverage for one
                                                       delivery date.

  `GET /api/analytics?from=YYYY-MM-DD&to=YYYY-MM-DD`   Return aggregate accuracy metrics
                                                       for a date range.

  `GET /api/forecast-evolution?date=YYYY-MM-DD`        Return forecast publication
                                                       history, if the source provides it.
  ----------------------------------------------------------------------------------------

Restrict assignment analysis to delivery dates in January 2026. Return
useful errors for invalid dates, upstream failures, and empty results.

### HTTPX

Use HTTPX for Elexon requests: - Set explicit connection/read
timeouts. - Check HTTP status codes. - Handle network failures and
malformed responses. - Use bounded retries only where appropriate. -
Avoid retrying indefinitely. - Request bounded date ranges and follow
documented pagination/stream behaviour.

### Pandas

Use Pandas for: - Parsing and normalizing timestamps. - Filtering
`FUELHH` to `fuelType == "WIND"`. - Joining forecasts and actuals by
normalized delivery interval. - Selecting the latest eligible forecast
before the decision cutoff. - Calculating error metrics and coverage
counts.

Keep the analytics functions separate from FastAPI route handlers so
they can be unit-tested without making network calls.

### Pydantic

Define response schemas for: - Interval rows. - Accuracy metrics. -
Coverage counts. - Forecast evolution records. - Error responses where
helpful.

Do not silently convert missing or invalid values to zero.

------------------------------------------------------------------------

## 4. Data and Analytics Rules

### Required source datasets

**FUELHH actual generation** - Documentation:
<https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream> -
Fields: `startTime`, `generation`, `fuelType` - Filter:
`fuelType = WIND`

**WINDFOR forecast generation** - Documentation:
<https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream> -
Fields: `startTime`, `publishTime`, `generation`

Validate the current schema, timezone conventions, generation units,
historical availability, query parameters, and pagination behaviour
before relying on them.

### Forecast selection

For each delivery interval, define a configurable decision cutoff
`C(t)`. Eligible forecasts satisfy:

``` text
publishTime <= C(t)
```

Select the eligible record with the latest `publishTime` for that
delivery interval. The assignment does not specify the exact business
cutoff, so document the chosen pilot assumption and display it in the
UI. Never use a later forecast revision in the decision-time view.

### Metrics

Let `F` be the selected forecast, `A` actual generation, and `n` valid
matched intervals.

-   **Signed error:** `F - A`
-   **MAE:** mean of `abs(F - A)`
-   **RMSE:** square root of mean of `(F - A)^2`
-   **Bias:** mean of `F - A`
-   **WAPE:** `sum(abs(F - A)) / sum(A) * 100`, if the denominator is
    non-zero

Calculate metrics only over valid matched pairs. Display the matched
sample count and report missing intervals. Return WAPE as not applicable
when its denominator is zero.

------------------------------------------------------------------------

## 5. Testing

### Pytest

Create deterministic tests for the analytics layer without calling
Elexon. At minimum, test:

-   Latest forecast before cutoff is selected.
-   Forecast published after cutoff is excluded.
-   No eligible forecast is marked missing.
-   Actuals are filtered to wind.
-   Forecast and actual timestamps are matched correctly.
-   MAE, RMSE, bias, and WAPE match hand-calculated examples.
-   WAPE handles a zero denominator.
-   Duplicate records follow the documented deterministic policy.
-   Missing/invalid numeric values do not become fabricated zeros.
-   API errors and empty responses produce useful outcomes.

Run tests before deployment and do not claim tests passed unless they
were actually run.

------------------------------------------------------------------------

## 6. Docker and Local Development

Use Docker Compose to start the frontend and backend together.

Suggested files:

``` text
windsight/
├── frontend/
│   ├── Dockerfile
│   └── package.json
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── prd.md
├── techstack.md
└── README.md
```

### Docker requirements

-   Frontend container serves the React development server or production
    build, according to the chosen setup.
-   Backend container runs FastAPI using an ASGI server such as Uvicorn.
-   Docker Compose connects the services and configures local
    environment variables.
-   `.env.example` documents variable names using safe placeholder
    values.
-   `.env`, credentials, tokens, and private local files must not be
    committed.
-   Confirm that Docker Compose starts the application from a clean
    checkout using the README instructions.

------------------------------------------------------------------------

## 7. Deployment

### Frontend --- Vercel

Deploy the React/Vite frontend to Vercel. Configure a production
environment variable such as:

``` text
VITE_API_BASE_URL=https://your-deployed-backend.example
```

Use the real deployed backend URL in production; do not leave localhost
URLs in the deployed build.

### Backend --- Python-compatible hosting

Deploy FastAPI on a platform that supports Python web services or Docker
containers. Confirm current free-tier limits, sleep/cold-start
behaviour, build requirements, and public access before choosing a
provider.

Configure CORS to allow the deployed frontend origin. Verify the backend
health endpoint and complete dashboard flow after deployment.

------------------------------------------------------------------------

## 8. Repository and Documentation

Use Git for version control and GitHub for the public assignment
repository. The assignment requests an anonymous/random-looking
repository name.

The README should contain: - Product overview and screenshots. -
Architecture and request/data flow. - Data sources and timestamp/cutoff
assumptions. - Metric definitions and coverage policy. - File/folder
descriptions. - Local setup and Docker commands. - Test commands. -
Deployment URLs. - Known limitations. - An accurate disclosure of AI
tools used, as required by the assignment.

------------------------------------------------------------------------

## 9. What Not to Add

To stay within the 16-hour timebox, avoid introducing these unless a
core requirement cannot be met otherwise:

-   A database or message queue.
-   Microservices.
-   Authentication and user management.
-   Machine-learning model training.
-   State management libraries for a small dashboard.
-   Complex CI/CD pipelines.
-   Financial or trading integrations.
-   Additional data sources.

Use a small in-process cache only if repeated API requests or hosting
constraints make it useful. A database is not required for the first
version unless testing shows the source data cannot be fetched reliably
at runtime and local persistence is necessary.

------------------------------------------------------------------------

## 10. Definition of Done

The stack is implemented successfully when:

-   React displays real API-backed data.
-   FastAPI retrieves and normalizes the two required Elexon datasets.
-   Cutoff selection prevents look-ahead bias.
-   Metrics and coverage are tested and explained.
-   Loading, empty, and error states are handled.
-   Docker Compose runs the application locally.
-   The frontend and backend are publicly deployed and communicate
    correctly.
-   The public GitHub repository documents setup, tests, deployment, and
    AI use.
-   The required unlisted YouTube video and final submission are
    complete.

**Guiding principle:** choose the simplest stack that supports correct
data handling, a clear user experience, reproducible testing, and a
credible technical review.
