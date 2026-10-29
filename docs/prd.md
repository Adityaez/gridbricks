# WindSight --- Product Requirements Document (PRD)

**Product:** WindSight --- Day-Ahead Wind Forecast Intelligence\
**Document:** `prd.md`\
**Version:** 1.1\
**Status:** Development blueprint\
**Project type:** Hiring assignment / working pilot\
**Time budget:** Maximum 16 hours\
**Frontend:** React + Vite\
**Backend:** Python + FastAPI\
**Deployment:** Frontend on Vercel; backend on a Python-compatible
hosting platform\
**Data scope:** Elexon national wind actuals and wind forecasts for
January 2026 only

------------------------------------------------------------------------

## 1. Product Summary

WindSight is a web application for a UK electricity utility's day-ahead
procurement team. It helps users:

1.  Inspect the wind generation forecast that was available by a defined
    purchasing-decision cutoff.
2.  Compare the selected forecast with actual wind generation once
    delivery data is available.
3.  Quantify forecast accuracy using transparent statistical metrics.
4.  Understand missing data, forecast publication times, and assumptions
    behind the analysis.

This is a historical pilot for January 2026. It is **not** a live
trading system, an electricity-demand forecast, or a complete
procurement optimizer.

## 2. Problem Statement

Wind generation is weather-dependent and changes over time. Forecasts
may be published multiple times for the same delivery interval. To
evaluate what the procurement team could reasonably have known at
decision time, the application must select a forecast using its
publication timestamp and must not use later revisions.

The application must also compare selected forecasts with actual
generation and report accuracy quantitatively. It must not infer total
electricity demand, required procurement volume, trading cost, or
savings from wind generation data alone.

## 3. Scope

### In scope

-   National-level Elexon wind actual generation from `FUELHH`, filtered
    to `fuelType = WIND`.
-   National-level Elexon wind forecast records from `WINDFOR`.
-   Delivery intervals at the source's 30-minute resolution.
-   Delivery dates in January 2026.
-   Decision-time forecast selection using `publishTime`.
-   Forecast-versus-actual time series and interval table.
-   MAE, RMSE, signed bias, and WAPE.
-   Coverage and missing-data reporting.
-   Forecast evolution, if historical publication records are available.
-   React frontend, Python backend, tests, Docker, public GitHub
    repository, deployment, README, and a video demo.

### Out of scope

-   Any dataset beyond the two Elexon datasets specified in the
    assignment.
-   Forecasting with a new machine-learning model.
-   Consumer demand prediction or total supply-demand balancing.
-   Thermal plant dispatch optimization or procurement-volume
    recommendations.
-   Wholesale/imbalance prices, trading execution, financial P&L, or
    claimed savings.
-   Other fuels, countries, or months in the initial release.
-   Authentication and multi-user account management unless required by
    the hosting platform.

## 4. Data Sources

### Actual generation

-   Dataset: `FUELHH`
-   Documentation:
    <https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream>
-   Required fields: `startTime`, `generation`, `fuelType`
-   Filter: `fuelType == "WIND"`

### Forecast generation

-   Dataset: `WINDFOR`
-   Documentation:
    <https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream>
-   Required fields: `startTime`, `publishTime`, `generation`

### Data validation requirements

Before implementing the dashboard, verify the current API response
shape, query parameters, pagination/streaming behaviour, timestamp
timezone, generation units, record volume, and availability of
historical records. Do not assume a unit or timezone without checking
the source documentation and sample records.

Normalize timestamps consistently. Match records by the same delivery
interval (`startTime`) after timezone handling. Preserve `publishTime`
for forecast selection and display.

------------------------------------------------------------------------

# 5. Phased Development Plan

Development must proceed phase by phase. Do not begin a later phase
until the exit criteria of the current phase are satisfied. The time
estimates total 15 hours, leaving 1 hour of buffer within the 16-hour
assignment limit.

## Phase 0 --- Project setup and scope confirmation

**Time budget:** 30 minutes

### Tasks

-   [ ] Create a project directory named `windsight` or another suitable
    local name.
-   [ ] Initialize Git.
-   [ ] Create `frontend/` and `backend/` directories.
-   [ ] Create `.gitignore` and `.env.example`.
-   [ ] Confirm the supported delivery period is 1--31 January 2026.
-   [ ] Record the decision-cutoff assumption as configurable because
    the assignment does not specify an exact cutoff.
-   [ ] Create this `prd.md` at the repository root.

### Deliverables

-   Initial project structure.
-   Documented assumptions and scope.
-   No secrets or personal files committed.

### Exit criteria

The project can be initialized locally and the team can explain what is
in and out of scope.

------------------------------------------------------------------------

## Phase 1 --- Elexon API research and data feasibility

**Time budget:** 1 hour

### Tasks

-   [ ] Read the FUELHH and WINDFOR endpoint documentation.
-   [ ] Retrieve a small sample of January 2026 actual records.
-   [ ] Retrieve a small sample of January 2026 forecast records,
    including historical publication timestamps.
-   [ ] Inspect response structure, timestamp format, units, filtering,
    pagination, and rate limits.
-   [ ] Confirm how to request the full January period without silently
    truncating records.
-   [ ] Record a few example records in development notes, not as
    hardcoded production data.

### Deliverables

-   A working API request or small exploratory script.
-   Confirmed data schema and request strategy.
-   Notes on any API limitations or gaps.

### Exit criteria

The developer can retrieve real records from both datasets and explain
how the records will be normalized and joined.

### Blocker rule

If the API cannot return the required historical period through the
selected endpoint, investigate the documented Elexon
historical/evolution endpoint before building UI components. Do not
replace unavailable data with invented values.

------------------------------------------------------------------------

## Phase 2 --- Backend data ingestion and normalization

**Time budget:** 2 hours

### Tasks

-   [ ] Create the FastAPI application.
-   [ ] Implement a dedicated Elexon client in
    `backend/app/services/elexon.py`.
-   [ ] Fetch FUELHH actuals and filter to `fuelType = WIND`.
-   [ ] Fetch WINDFOR forecasts with `startTime`, `publishTime`, and
    `generation`.
-   [ ] Parse and normalize timestamps using one documented timezone
    convention.
-   [ ] Validate required fields and numeric generation values.
-   [ ] Handle duplicate records deterministically and document the
    rule.
-   [ ] Handle empty responses, timeouts, HTTP errors, and malformed
    records.
-   [ ] Use bounded date queries and avoid unnecessarily downloading the
    entire dataset for every request.
-   [ ] Add an in-process cache only if useful and safe for the chosen
    deployment.

### Suggested files

``` text
backend/
  app/
    main.py
    api/
      routes.py
    services/
      elexon.py
      analytics.py
    schemas.py
  tests/
  requirements.txt
  Dockerfile
```

### Deliverables

-   Backend can retrieve and normalize actual and forecast records.
-   Clear separation between API access, analytics, and HTTP route
    handlers.

### Exit criteria

A script or endpoint can return normalized January records from both
sources, or provide an explicit and useful error if the upstream data is
unavailable.

------------------------------------------------------------------------

## Phase 3 --- Decision-time forecast selection and analytics

**Time budget:** 2 hours

### Core rule: avoid look-ahead bias

For each delivery interval `t`, define a decision cutoff `C(t)`.
Eligible forecast records must satisfy:

``` text
publishTime <= C(t)
```

For records with the same delivery `startTime`, select the eligible
record with the latest `publishTime`.

The assignment does not specify the actual business cutoff. Therefore,
make it configurable, document the chosen pilot assumption, and display
the cutoff in the UI. Do not describe an illustrative cutoff as an
official market deadline.

If no eligible forecast exists, mark the interval as missing. Never
silently substitute a forecast published after the cutoff.

### Tasks

-   [ ] Implement cutoff-based forecast selection in `analytics.py`.
-   [ ] Match the selected forecast to actual generation by normalized
    delivery interval.
-   [ ] Calculate signed error: `forecast - actual`.
-   [ ] Calculate MAE.
-   [ ] Calculate RMSE.
-   [ ] Calculate signed bias.
-   [ ] Calculate WAPE when the sum of actual generation is non-zero.
-   [ ] Count expected intervals, matched pairs, missing forecasts,
    missing actuals, and excluded/duplicate records where possible.
-   [ ] Ensure metrics use valid matched numeric pairs only.
-   [ ] Return `null`/not applicable for WAPE if its denominator is
    zero.
-   [ ] Add unit tests using small deterministic fixtures.

### Metric definitions

Let `F` be the selected forecast, `A` be actual generation, and `n` be
the number of valid matched pairs.

-   **Signed error:** `F - A`. Positive means over-forecasting; negative
    means under-forecasting.
-   **MAE:** mean of `abs(F - A)`.
-   **RMSE:** square root of mean of `(F - A)^2`.
-   **Bias:** mean of `F - A`.
-   **WAPE:** `sum(abs(F - A)) / sum(A) * 100`, where the denominator is
    valid and non-zero.

Report the source generation unit alongside MW-labelled metrics only
after confirming that the API's generation unit is MW.

### Deliverables

-   Tested analytics functions.
-   Explicit data coverage and metric semantics.
-   No use of future-published forecasts in decision-time evaluation.

### Exit criteria

Automated tests prove the cutoff selection and metric calculations work
for normal, missing, duplicate, and zero-denominator cases.

------------------------------------------------------------------------

## Phase 4 --- Backend API endpoints

**Time budget:** 1 hour

### Required endpoints

  ----------------------------------------------------------------------------------------
  Endpoint                                             Purpose
  ---------------------------------------------------- -----------------------------------
  `GET /api/health`                                    Health check

  `GET /api/dashboard?date=YYYY-MM-DD`                 Forecast/actual intervals and daily
                                                       metrics

  `GET /api/analytics?from=YYYY-MM-DD&to=YYYY-MM-DD`   Aggregate metrics for a selected
                                                       date range

  `GET /api/forecast-evolution?date=YYYY-MM-DD`        Publication history for forecast
                                                       evolution, if available
  ----------------------------------------------------------------------------------------

### Tasks

-   [ ] Define typed request and response schemas.
-   [ ] Validate date parameters and restrict analysis to January 2026
    for this assignment.
-   [ ] Return timestamps, values, publication times, errors, metrics,
    and coverage counts.
-   [ ] Return useful HTTP error codes and readable error messages.
-   [ ] Configure CORS for local development and the deployed frontend.
-   [ ] Test endpoints with real data and empty/error cases.
-   [ ] Document example requests and response fields in the README.

### Exit criteria

All required endpoints respond with a predictable JSON contract and pass
manual/API tests.

------------------------------------------------------------------------

## Phase 5 --- React dashboard and visual design

**Time budget:** 3 hours

### Suggested stack

-   React + Vite.
-   TypeScript if practical within the time budget.
-   Recharts or another suitable charting library.
-   Plain CSS or Tailwind CSS.
-   A small API service module for backend requests.

### Dashboard requirements

-   [ ] Product title: **WindSight --- Day-Ahead Wind Forecast
    Intelligence**.
-   [ ] Clearly label the application as a historical January 2026
    pilot.
-   [ ] Date selector for January 2026.
-   [ ] Visible decision cutoff and forecast publication timestamp.
-   [ ] KPI cards for selected forecast, MAE, RMSE, and bias.
-   [ ] Forecast-versus-actual time-series chart.
-   [ ] Forecast evolution view if the data supports it.
-   [ ] Interval table with `startTime`, forecast, `publishTime`,
    actual, signed error, and data status.
-   [ ] Coverage summary and metric definitions.
-   [ ] Loading, empty-data, and error states.
-   [ ] Responsive layout and readable labels/units.
-   [ ] No hardcoded illustrative values in the production dashboard.

### Suggested components

``` text
frontend/src/
  components/
    MetricCard.tsx
    ForecastChart.tsx
    ForecastTable.tsx
    CoverageSummary.tsx
  pages/
    Dashboard.tsx
  services/
    api.ts
  App.tsx
  main.tsx
```

### Exit criteria

A user can select a date, load real backend data, inspect forecast
publication times, and understand the metrics and missing-data status.

------------------------------------------------------------------------

## Phase 6 --- Integration, quality checks, and Docker

**Time budget:** 1.5 hours

### Tasks

-   [ ] Connect the React API client to FastAPI.
-   [ ] Verify loading and error states.
-   [ ] Test local frontend/backend CORS configuration.
-   [ ] Add or complete backend unit tests.
-   [ ] Run a full manual workflow for at least one delivery date.
-   [ ] Add `backend/Dockerfile`.
-   [ ] Add `frontend/Dockerfile`.
-   [ ] Add `docker-compose.yml`.
-   [ ] Add `.env.example` with variable names and safe placeholder
    values.
-   [ ] Verify the app starts using Docker Compose.
-   [ ] Confirm secrets and local environment files are excluded from
    Git.

### Exit criteria

A clean local startup works from the documented commands, the dashboard
is connected to the backend, and the core analytical logic is tested.

------------------------------------------------------------------------

## Phase 7 --- README and public GitHub repository

**Time budget:** 1 hour

### Tasks

-   [ ] Create a public GitHub repository with an
    anonymous/random-looking repository name, as requested.
-   [ ] Push source code, tests, Docker files, and `prd.md`.
-   [ ] Write a clear `README.md`.
-   [ ] Explain the problem, features, architecture, data sources, and
    assumptions.
-   [ ] Document local setup and Docker commands.
-   [ ] Document API endpoints and metric formulas.
-   [ ] Include the deployed application URL when available.
-   [ ] Include the AI-use disclosure requested by the assignment.
-   [ ] Add screenshots if they improve understanding.
-   [ ] Confirm no API secrets, tokens, or private files are committed.

### AI-use disclosure

Accurately list the AI tools used and the tasks they assisted with, such
as planning, code assistance, debugging, or documentation. Only claim
that code was tested or validated if you actually performed those
checks.

### Exit criteria

The public repository is readable without signing in and another
developer can follow the setup instructions.

------------------------------------------------------------------------

## Phase 8 --- Deployment

**Time budget:** 1 hour

### Recommended deployment shape

-   Frontend: Vercel.
-   Backend: a Python-compatible hosting platform with suitable FastAPI
    or Docker support.

Check current platform limits and availability before choosing a host.
Do not assume that the frontend host will run the backend container
unchanged.

### Tasks

-   [ ] Deploy the backend and verify `/api/health`.
-   [ ] Configure the frontend's production API base URL.
-   [ ] Deploy the frontend.
-   [ ] Configure production CORS to allow the deployed frontend.
-   [ ] Test the complete workflow on the public URL.
-   [ ] Check API timeouts, cold starts, missing data, and browser
    console errors.
-   [ ] Update README with working deployment links.

### Exit criteria

The public frontend loads and successfully retrieves real data from the
deployed backend.

------------------------------------------------------------------------

## Phase 9 --- Video demo and submission

**Time budget:** 2 hours

### Video limit

Create one unlisted YouTube video of no more than 10 minutes. The
customer-facing overview and technical-review overview must each be no
longer than five minutes.

### Part 1 --- Customer pitch (maximum 5 minutes)

1.  Introduce the procurement problem and WindSight.
2.  Select a January delivery date.
3.  Show the selected forecast and its publication time/cutoff.
4.  Demonstrate the forecast-versus-actual chart and accuracy metrics.
5.  Explain how the results inform review of forecast uncertainty.
6.  State limitations: the pilot does not include demand, prices, or a
    complete procurement calculation.

### Part 2 --- Technical review (maximum 5 minutes)

1.  Show the architecture and repository structure.
2.  Explain Elexon ingestion and timestamp normalization.
3.  Demonstrate cutoff-based forecast selection.
4.  Explain metric calculations and tests.
5.  Show Docker setup, deployment, and error handling.
6.  Summarize assumptions and trade-offs.

### Final submission tasks

-   [ ] Upload the video as Unlisted.
-   [ ] Open the video URL in a private/incognito window and verify
    playback.
-   [ ] Open the public GitHub repository in a private/incognito window.
-   [ ] Open the deployed application in a private/incognito window and
    test it.
-   [ ] Verify that README links are correct.
-   [ ] Complete the submission form:
    <https://forms.cloud.microsoft/r/FTX6K2bbnU>.
-   [ ] Submit the requested repository, app, and video details.

### Exit criteria

All required URLs are publicly accessible to the intended reviewer, and
the submission form is completed.

------------------------------------------------------------------------

# 6. Acceptance Criteria

The project is ready for submission when all of the following are true:

-   [ ] It supports the January 2026 delivery period.
-   [ ] Actual data is filtered to `fuelType = WIND`.
-   [ ] Forecast records retain `startTime`, `publishTime`, and
    `generation`.
-   [ ] Forecast selection uses the latest eligible publication at or
    before the documented cutoff.
-   [ ] No forecast published after the cutoff is used in the
    decision-time view.
-   [ ] Actual and forecast records are matched by normalized delivery
    interval.
-   [ ] MAE, RMSE, signed bias, and WAPE are calculated correctly and
    explained.
-   [ ] Missing records and coverage are visible.
-   [ ] The frontend uses backend data rather than fabricated display
    values.
-   [ ] Error and empty states are understandable.
-   [ ] Tests cover core analytics and cutoff behaviour.
-   [ ] Docker-based local startup is documented and verified.
-   [ ] A public GitHub repository and README are available.
-   [ ] The application is deployed and publicly accessible.
-   [ ] An unlisted YouTube demo is no longer than 10 minutes.
-   [ ] The submission form is completed and URLs are checked in
    incognito mode.

# 7. Suggested Repository Structure

``` text
windsight/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   │   ├── elexon.py
│   │   │   └── analytics.py
│   │   ├── main.py
│   │   └── schemas.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
├── prd.md
└── README.md
```

# 8. Risks and Assumptions

  -----------------------------------------------------------------------
  Risk or unknown                     Mitigation
  ----------------------------------- -----------------------------------
  Exact decision cutoff is not        Make it configurable and document
  specified                           the pilot assumption.

  Historical API response may be      Validate request limits early and
  large or paginated                  use bounded queries.

  Timezone/unit conventions may be    Verify the current schema and
  unclear                             document normalization.

  Missing or duplicate records        Report gaps and apply
                                      deterministic, documented duplicate
                                      handling.

  Forecast history may not be         Show missing coverage; do not
  available for every interval        substitute a later forecast.

  Hosting free tiers may sleep or     Verify deployment behaviour and
  impose limits                       test public links before
                                      submission.

  Wind alone cannot determine         Clearly state that demand and price
  required procurement                datasets are out of scope.
  -----------------------------------------------------------------------

# 9. Time Budget

  Workstream                                 Budget
  ------------------------------------ ------------
  Phase 0 --- Setup                           0.5 h
  Phase 1 --- API research                    1.0 h
  Phase 2 --- Ingestion                       2.0 h
  Phase 3 --- Analytics                       2.0 h
  Phase 4 --- Backend API                     1.0 h
  Phase 5 --- Frontend                        3.0 h
  Phase 6 --- Integration and Docker          1.5 h
  Phase 7 --- GitHub and README               1.0 h
  Phase 8 --- Deployment                      1.0 h
  Phase 9 --- Video and submission            2.0 h
  **Total**                              **15.0 h**
  **Remaining buffer**                    **1.0 h**

If time runs short, prioritize real data, correct forecast selection,
correct metrics, a working end-to-end dashboard, and the required demo.
Defer optional visual polish or forecast-evolution enhancements if
necessary.

------------------------------------------------------------------------

# 10. Definition of Done

WindSight is done when a reviewer can open the deployed application,
select a date in January 2026, see the eligible forecast and its
publication time, compare it with actual wind generation, understand the
accuracy metrics and coverage, inspect the public code and README,
reproduce the app locally with Docker, and watch the complete
customer/technical demo.

**Guiding principle:** correctness and transparency come before visual
polish. Never present assumptions, illustrative values, unavailable
records, or inferred financial outcomes as verified facts.
