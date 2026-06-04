# 当前进度

日期：2026-06-04

## 已完成

- 创建并确认中文产品设计文档。
- 创建实施计划文档。
- 初始化当前目录为 Git 仓库。
- 搭建 FastAPI + Python service 的项目骨架。
- 创建 PostgreSQL `docker-compose.yml`。
- 创建 Python 包配置 `pyproject.toml`。
- 创建基础 API 路由模块：
  - funds
  - experiment_groups
  - experiments
  - backtests
  - stress_periods
  - reports
- 创建服务模块边界：
  - nav_loader
  - metrics
  - backtest_engine
  - rebalance
  - contribution
  - data_quality
  - report_generator
- 创建数据导入边界：
  - csv_importer
  - akshare_importer
  - tushare_importer
- 用 `unittest` 增加并通过最小指标计算测试。
- 通过 `python3 -m compileall app tests` 语法检查。

## 当前约束

- 本机当前没有安装 `pytest`，所以现阶段使用 Python 标准库 `unittest` 验证。
- FastAPI 等依赖已写入 `pyproject.toml`，但尚未安装。
- 数据库模型、迁移、CSV 导入和回测引擎还未实现。

## 最近验证

```bash
python3 -m unittest tests/test_metrics.py
python3 -m compileall app tests
```

## 下一步

进入数据库模型和迁移设计，实现 `fund_basic`、`fund_nav_daily`、`experiment_group`、`portfolio_experiment`、`portfolio_position`、`stress_period`、`backtest_result` 和 `backtest_nav_daily`。
