# 基金组合实验室 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first local Fund Portfolio Lab skeleton, then implement the MVP research loop for 75/15/10 multi-asset fund portfolio backtesting.

**Architecture:** Start with a Python-first local monolith. FastAPI exposes local HTTP APIs, calculation services stay in focused Python modules, PostgreSQL is the local runtime database, SQLite or in-memory fixtures are used for tests.

**Tech Stack:** Python 3.10+, FastAPI, pandas/numpy, SQLAlchemy, Alembic, PostgreSQL, local Web UI, unittest/pytest-compatible tests.

---

## File Structure

- `app/main.py`: FastAPI application entrypoint and router registration.
- `app/api/`: HTTP route modules split by resource: funds, experiment groups, experiments, backtests, stress periods, reports.
- `app/models/`: database model definitions for funds, experiments, backtests, and stress periods.
- `app/services/`: calculation and orchestration modules: NAV loading, metrics, rebalancing, contribution, data quality, reports.
- `app/importers/`: CSV, AKShare, and Tushare import boundaries.
- `tests/`: calculation and service tests.
- `docs/progress.md`: current project progress and completed work.
- `docs/roadmap.md`: near-term implementation sequence.
- `docker-compose.yml`: local PostgreSQL service.
- `pyproject.toml`: Python package and dependency metadata.

## Task 1: Repository And Skeleton

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `README.md`
- Create: `app/main.py`
- Create: `app/api/*.py`
- Create: `app/models/*.py`
- Create: `app/services/*.py`
- Create: `app/importers/*.py`
- Create: `tests/test_metrics.py`
- Create: `docs/progress.md`
- Create: `docs/roadmap.md`

- [x] **Step 1: Initialize git repository**

Run: `git init`
Expected: `.git/` is created in the project root.

- [x] **Step 2: Write failing metric tests**

Create `tests/test_metrics.py`:

```python
import unittest

from app.services.metrics import calculate_daily_returns, calculate_max_drawdown


class MetricsTest(unittest.TestCase):
    def test_calculates_daily_returns_from_nav_series(self):
        self.assertEqual(calculate_daily_returns([1.0, 1.1, 1.21]), [0.1, 0.1])

    def test_calculates_max_drawdown_from_nav_series(self):
        self.assertAlmostEqual(calculate_max_drawdown([1.0, 1.2, 0.9, 1.1]), -0.25)


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 3: Run test to verify it fails**

Run: `python3 -m unittest tests/test_metrics.py`
Expected: FAIL because `app.services.metrics` does not exist yet.

- [x] **Step 4: Create skeleton modules and minimal metric implementation**

Create package directories and implement `calculate_daily_returns` and `calculate_max_drawdown` in `app/services/metrics.py`.

- [x] **Step 5: Run test to verify it passes**

Run: `python3 -m unittest tests/test_metrics.py`
Expected: PASS.

- [x] **Step 6: Run syntax verification**

Run: `python3 -m compileall app tests`
Expected: all Python files compile successfully.

- [x] **Step 7: Commit skeleton**

```bash
git add .
git commit -m "chore: scaffold fund portfolio lab"
```

## Task 2: Database Models And Migrations

**Files:**
- Modify: `app/models/fund.py`
- Modify: `app/models/experiment.py`
- Modify: `app/models/backtest.py`
- Modify: `app/models/stress_period.py`
- Create: `app/db/session.py`
- Create: `app/db/base.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`

- [ ] **Step 1: Add model tests for required table names and fields**

Create model metadata tests that assert the fund, experiment group, portfolio experiment, stress period, backtest result, and backtest nav daily tables expose the fields listed in the design spec.

- [ ] **Step 2: Run model tests and verify they fail**

Run: `python3 -m unittest tests/test_models.py`
Expected: FAIL because SQLAlchemy models are not implemented.

- [ ] **Step 3: Implement SQLAlchemy models**

Implement focused model files matching the spec fields.

- [ ] **Step 4: Run model tests and verify they pass**

Run: `python3 -m unittest tests/test_models.py`
Expected: PASS.

## Task 3: CSV NAV Import

**Files:**
- Modify: `app/importers/csv_importer.py`
- Modify: `app/services/nav_loader.py`
- Create: `tests/test_csv_importer.py`

- [ ] **Step 1: Write CSV importer tests**

Cover fund code, NAV date, unit NAV, accumulated NAV, adjusted NAV, and source parsing.

- [ ] **Step 2: Run importer tests and verify they fail**

Run: `python3 -m unittest tests/test_csv_importer.py`
Expected: FAIL because importer behavior is missing.

- [ ] **Step 3: Implement CSV importer**

Use Python CSV parsing first. Add pandas only when bulk import behavior requires it.

- [ ] **Step 4: Run importer tests and verify they pass**

Run: `python3 -m unittest tests/test_csv_importer.py`
Expected: PASS.

## Task 4: Backtest Engine Core

**Files:**
- Modify: `app/services/backtest_engine.py`
- Modify: `app/services/rebalance.py`
- Modify: `app/services/contribution.py`
- Modify: `app/services/data_quality.py`
- Create: `tests/test_rebalance.py`
- Create: `tests/test_nav_alignment.py`
- Create: `tests/test_backtest_engine.py`

- [ ] **Step 1: Write tests for NAV alignment, rebalance, turnover, and data quality**

Use small hand-calculable NAV fixtures.

- [ ] **Step 2: Run tests and verify they fail**

Run: `python3 -m unittest tests/test_rebalance.py tests/test_nav_alignment.py tests/test_backtest_engine.py`
Expected: FAIL because engine behavior is missing.

- [ ] **Step 3: Implement the minimal backtest engine**

Implement common-date alignment, NAV policy selection, portfolio return, monthly/quarterly rebalance, turnover, cost, and data quality output.

- [ ] **Step 4: Run tests and verify they pass**

Run: `python3 -m unittest tests/test_rebalance.py tests/test_nav_alignment.py tests/test_backtest_engine.py`
Expected: PASS.

## Task 5: Reports And Local API

**Files:**
- Modify: `app/services/report_generator.py`
- Modify: `app/api/*.py`
- Create: `tests/test_report_generator.py`

- [ ] **Step 1: Write report language guard tests**

Assert reports include metrics, NAV policy, missing-data diagnostics, and data quality. Assert reports do not contain `买入`, `卖出`, `推荐`, or `保证收益`.

- [ ] **Step 2: Run report tests and verify they fail**

Run: `python3 -m unittest tests/test_report_generator.py`
Expected: FAIL because report generation is missing.

- [ ] **Step 3: Implement report generator and API route stubs**

Return structured JSON for APIs and Markdown for reports.

- [ ] **Step 4: Run report tests and syntax checks**

Run: `python3 -m unittest discover`
Expected: PASS after project dependencies are installed.

## Self-Review

- The plan covers repository setup, database structure, CSV import, core backtest behavior, report generation, and API boundaries.
- The first executable task is intentionally small and testable without network dependency installation.
- The plan follows the approved design: experiment groups, stress periods, backtest daily NAV table, data quality, strict NAV policy, and explicit rebalance cost formulas.
