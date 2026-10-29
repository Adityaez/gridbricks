# WindSight --- Day-Ahead Wind Forecast Intelligence

> A focused analytical platform for UK electricity day-ahead procurement desks to evaluate historical wind generation forecasts against realized Elexon settlement actuals without look-ahead bias.

---

## 1. Project Overview

In power procurement and balancing operations, electricity utilities need to assess how accurately day-ahead wind forecasts anticipated actual generation at the exact moment purchase decisions were finalized. Because weather forecasts update continuously, comparing actuals with late forecast revisions introduces **look-ahead bias**, masking the true uncertainty faced at decision cutoff.

**WindSight** reconstructs the historical forecast state for **January 2026** using:
- **`WINDFOR`**: Half-hourly national wind generation forecasts published by Elexon BMRS.
- **`FUELHH`**: Realized half-hourly national generation filtered strictly to `fuelType = WIND`.

### Key Capabilities
- **Look-Ahead Bias Elimination:** Evaluates only forecasts published at or before a documented decision cutoff $C(t)$ (e.g., Day-Ahead 17:00 UTC).
- **Transparent Accuracy Metrics:** Formulates MAE, RMSE, Signed Bias, and WAPE with strict handling of edge cases (e.g., zero denominators).
- **Data Coverage & Integrity Audit:** Explicitly tracks missing forecasts and unobserved delivery intervals instead of fabricating default values.

---

## 2. Temporal & Data Scope Constraints

- **Evaluation Window:** Strictly January 1, 2026 00:00 UTC to January 31, 2026 23:59 UTC.
- **Resolution:** 30-minute UK settlement intervals (48 settlement periods per day).
- **Geography:** National UK transmission system wind generation.
- **Out of Scope:** Demand forecasting, pricing / imbalance trading settlements, machine learning retraining, and cross-fuel portfolio optimization.

---

## 3. Architecture & Tech Stack

- **Frontend:** React 18, Vite, TypeScript, Recharts, Tailwind CSS.
- **Backend:** Python 3.11, FastAPI, Pydantic, Pandas, HTTPX, Pytest.
- **Containerization:** Docker & Docker Compose.
- **Target Deployments:** Frontend on Vercel; Backend on Python-compatible container host.

---

## 4. Quickstart

### Prerequisites
- Node.js >= 18
- Python >= 3.11
- Docker & Docker Compose (optional)

### Running with Docker Compose
```bash
cp .env.example .env
docker compose up --build
```
- Access Frontend: `http://localhost:5173`
- Access Backend API Docs: `http://localhost:8000/docs`

---

## 5. Mathematical Metrics

Given $n$ valid matched pairs of selected forecast $F$ and actual generation $A$:
- **Signed Error:** $F - A$
- **MAE:** $\frac{1}{n} \sum |F - A|$
- **RMSE:** $\sqrt{\frac{1}{n} \sum (F - A)^2}$
- **Signed Bias:** $\frac{1}{n} \sum (F - A)$
- **WAPE:** $\frac{\sum |F - A|}{\sum A} \times 100\%$ (returned as `null` if $\sum A = 0$)

---

## 6. AI-Use Disclosure

Development of WindSight is assisted by AI coding assistants (Google Antigravity / Gemini 3.8 Flash) for scaffolding, documentation, and test-case structuring. All mathematical logic, cutoff mechanisms, and data schemas are strictly validated with automated deterministic unit tests.
