# 当前进度

日期：2026-06-04

## 已完成

### 阶段 0：项目骨架
- 创建并确认中文产品设计文档。
- 创建实施计划文档。
- 初始化当前目录为 Git 仓库。
- 搭建 FastAPI + Python service 的项目骨架。
- 创建 PostgreSQL `docker-compose.yml`。
- 创建 Python 包配置 `pyproject.toml`。
- 创建基础 API 路由模块和服务模块边界。
- 用 `unittest` 增加并通过最小指标计算测试。

### 阶段 1：数据库模型与迁移
- 实现 8 张表的 SQLAlchemy 模型：`fund_basic`、`fund_nav_daily`、`experiment_group`、`portfolio_experiment`、`portfolio_position`、`stress_period`、`backtest_result`、`backtest_nav_daily`。
- 创建 `app/db/base.py` 和 `app/db/session.py`。
- 配置 Alembic，创建初始迁移脚本 `0001_initial_schema.py`。
- 8 个模型元数据测试全部通过。

### 阶段 2：CSV 净值导入
- 实现 `app/importers/csv_importer.py`：解析基金代码、日期、单位净值、累计净值、复权净值、来源。
- 实现 `app/services/nav_loader.py`：从数据库加载净值数据为 DataFrame。
- 10 个 CSV 导入测试全部通过。

### 阶段 3：核心回测引擎
- 实现 `app/services/rebalance.py`：不再平衡、月度、季度、阈值触发、换手率和成本计算。
- 实现 `app/services/nav_alignment.py`：共同日期对齐、净值口径选择、前向填充、缺失数据诊断。
- 实现 `app/services/backtest_engine.py`：日度模拟、组合净值计算、回撤计算、指标汇总。
- 实现 `app/services/contribution.py`：日度收益贡献计算。
- 实现 `app/services/data_quality.py`：A/B/C/D 数据质量评分。
- 扩展 `app/services/metrics.py`：年化收益、年化波动率、夏普比率、卡玛比率。
- 28 个回测引擎测试全部通过。

### 阶段 4：报告与本地 API
- 实现 `app/services/report_generator.py`：Markdown 研究报告生成，含语言安全防护（屏蔽 "买入"、"卖出"、"推荐"、"保证收益"）。
- 实现所有 API 路由：基金 CRUD、实验组 CRUD、实验创建（含仓位）、回测运行和结果查询、报告生成、压力区间管理。
- 5 个报告测试全部通过。

### 阶段 5：本地 Web UI
- 使用 React + TypeScript + Vite + Ant Design + Recharts 搭建前端项目。
- 实现基金池页面：展示、添加基金。
- 实现实验组页面：创建实验组、查看实验列表。
- 实现实验详情页面：创建实验（含多基金仓位配置）、运行回测。
- 实现回测看板页面：展示所有回测结果对比、查看 Markdown 研究报告。
- 实现压力区间页面：添加和管理压力区间。
- TypeScript 类型检查通过，Vite 构建成功。

## 测试覆盖

53 个单元测试全部通过，覆盖：
- 模型元数据（8 个）
- CSV 导入器（10 个）
- 指标计算（2 个）
- 再平衡逻辑（9 个）
- 净值对齐（6 个）
- 回测引擎 + 数据质量（14 个）
- 报告生成（5 个）

## 当前约束

- 依赖已安装，虚拟环境可用。
- Docker 未运行，PostgreSQL 尚未启动，数据库迁移尚未执行。
- 前端依赖已安装，构建通过，但尚未启动 dev server 验证。
- AKShare 和 Tushare 导入器尚未实现（等待后续需求）。

## 下一步

- 启动 Docker PostgreSQL，运行 Alembic 迁移创建表。
- 导入第一批基金净值的 CSV 数据。
- 创建第一个 75/15/10 实验组并运行回测。
- 人工校验回测结果与 Excel 手工计算结果。
