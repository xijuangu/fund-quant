# 基金组合实验室

本项目是一个本地自用的多资产基金组合研究工具，第一版聚焦进取型 `75/15/10` 组合：

```text
权益 / QDII：75%
债券基金：15%
黄金基金：10%
```

目标是维护个人基金池、导入历史净值、创建组合实验组、运行回测、诊断防守资产效果，并生成 Markdown 研究报告。

## 与 fund-trace 的关系

本项目与 [xijuangu/fund-trace](https://github.com/xijuangu/fund-trace) 是上下游关系：

- `fund-trace`：负责基金跟踪、单只基金添加、历史净值抓取和本地 SQLite 数据沉淀。
- `fund-quant`：负责把 `fund-trace` 的基金与净值导入 PostgreSQL，并在此基础上做组合实验、回测、压力区间诊断和研究报告。

第一版不在 `fund-quant` 中直接抓取基金历史净值。新增基金和历史数据时，建议先在 `fund-trace` 中执行 `add` / `history` / `backfill`，再通过 `scripts/import_fund_trace.py` 导入本项目。这样可以保持数据采集职责集中在 `fund-trace`，组合研究职责集中在 `fund-quant`。

## 当前状态

当前已完成：

- Python-first 后端骨架：FastAPI、SQLAlchemy、Alembic、PostgreSQL。
- 8 张核心表：基金、净值、实验组、组合实验、持仓、压力区间、回测结果、日度回测净值。
- fund-trace SQLite 导入脚本，当前已导入 24 只基金、35459 条历史净值。
- 核心回测引擎：净值口径选择、日期对齐、再平衡、回撤、收益风险指标、数据质量评分。
- Markdown 报告生成和本地 API。
- React + TypeScript + Vite + Ant Design 本地 Web UI。
- 已完成一次真实 `75/15/10` smoke 回测并落库。

## 本地开发

创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

启动 PostgreSQL：

```bash
docker compose up -d postgres
```

执行数据库迁移：

```bash
.venv/bin/alembic upgrade head
```

从 fund-trace 导入数据：

```bash
.venv/bin/python scripts/import_fund_trace.py /Users/xijuangu/Developer/Personal/fund-trace/fund-trace.db
```

运行默认 `75/15/10` smoke 回测：

```bash
.venv/bin/python scripts/run_smoke_backtest.py
```

运行测试：

```bash
.venv/bin/python -m pytest -q
```

依赖安装完成后可启动 API：

```bash
uvicorn app.main:app --reload
```

启动前端：

```bash
cd web
npm run dev
```

## 文档

- 产品设计：[docs/superpowers/specs/2026-06-04-fund-portfolio-lab-design.md](docs/superpowers/specs/2026-06-04-fund-portfolio-lab-design.md)
- 实施计划：[docs/superpowers/plans/2026-06-04-fund-portfolio-lab-implementation.md](docs/superpowers/plans/2026-06-04-fund-portfolio-lab-implementation.md)
- 使用说明：[docs/usage.md](docs/usage.md)
- 当前进度：[docs/progress.md](docs/progress.md)
- 后续计划：[docs/roadmap.md](docs/roadmap.md)
