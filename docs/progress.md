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
- 添加迁移脚本 `0002_add_fund_basic_note.py`，修复 `fund_basic.note` 模型和数据库 schema 不一致问题。
- 本地 PostgreSQL 已通过 Docker 启动，数据库迁移已执行到 `0002 (head)`。
- 8 个模型元数据测试全部通过。

### 阶段 2：CSV 净值导入
- 实现 `app/importers/csv_importer.py`：解析基金代码、日期、单位净值、累计净值、复权净值、来源。
- 实现 `app/services/nav_loader.py`：从数据库加载净值数据为 DataFrame。
- 添加 `scripts/import_fund_trace.py`，支持从 `/Users/xijuangu/Developer/Personal/fund-trace/fund-trace.db` 复用导入已有 SQLite 数据。
- 已从 fund-trace 当前基金池导入 `fund_basic` 24 只基金、`fund_nav_daily` 35459 条净值。
- 已补充 3 只债券基金：`110037` 易方达纯债债券A、`110038` 易方达纯债债券C、`003547` 鹏华丰禄债券。
- 默认跳过 `nav_snapshots` 中已不在当前 `funds` 表里的 180 条 orphan 净值；脚本保留 `--include-orphans` 选项以便后续需要时导入。
- fund-trace 已完成批量历史回填，导入数据覆盖范围为 2013-08-22 到 2026-06-03。
- fund-trace 来源没有复权净值，导入后 `adjusted_nav` 为空。
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
- 修复回测结果持久化顺序：先 `flush` `backtest_result`，再写入 `backtest_nav_daily`，避免数据库外键插入顺序不确定。
- 回测参数或数据不足时返回 API 400，不再把 `ValueError` 冒泡为 500。
- 创建和更新实验时校验实验组、基金代码存在性，避免依赖数据库外键报 500。
- 删除被实验引用的基金时返回 409，要求先停用基金或删除相关实验，避免隐式删除实验和回测结果。
- 5 个报告测试全部通过。

### 阶段 5：本地 Web UI
- 使用 React + TypeScript + Vite + Ant Design + Recharts 搭建前端项目。
- 实现基金池页面：展示、添加基金。
- 实现实验组页面：创建实验组、查看实验列表。
- 实现实验详情页面：创建实验（含多基金仓位配置）、运行回测。
- 实现回测看板页面：展示所有回测结果对比、查看 Markdown 研究报告。
- 实现压力区间页面：添加和管理压力区间。
- 基金池创建、编辑、删除失败时展示后端错误详情；删除确认文案提示引用约束。
- TypeScript 类型检查通过，Vite 构建成功。

### 阶段 6：真实数据 smoke 回测
- 新增 `scripts/run_smoke_backtest.py`，支持创建本地 smoke 实验组、写入组合仓位、运行回测并生成报告。
- 已完成一次真实 `75/15/10` 月度再平衡回测并落库。
- 本次组合：
  - `001595` 天弘中证银行ETF联接C：45%
  - `012349` 天弘恒生科技ETF联接C：30%
  - `110037` 易方达纯债债券A：15%
  - `000217` 华安黄金ETF联接C：10%
- 本次回测区间：2021-07-06 至 2026-06-03。
- 本次结果：
  - 实验组 ID：`674b753b-fb94-4e9a-b34d-7a1ae1825cd1`
  - 实验 ID：`45a7a6c3-0b36-4e94-a265-bc34a7e45385`
  - 结果 ID：`4e4a7bb5-4c4d-4801-80fd-9d83b1b1f4e5`
  - 日度回测净值：1185 条
  - 数据质量：A
  - 报告长度：1155 字符
- 核心指标：
  - 累计收益：32.50%
  - 年化收益：6.17%
  - 年化波动：15.21%
  - 最大回撤：-25.64%
  - 夏普比率：0.4693
  - 卡玛比率：0.2405

## 测试覆盖

109 个单元测试全部通过，覆盖：
- 模型元数据（8 个）
- CSV 导入器（10 个）
- fund-trace SQLite 导入器（2 个）
- 指标计算（2 个）
- 再平衡逻辑（9 个）
- 净值对齐（6 个）
- 回测引擎 + 数据质量（14 个）
- 报告生成（5 个）
- 回测结果持久化顺序（1 个）
- API CRUD、错误处理和引用约束（53 个）

## 当前约束

- 依赖已安装，虚拟环境可用。
- Docker PostgreSQL 已运行，数据库迁移已执行。
- fund-trace 导入数据缺少复权净值，后续回测应统一使用累计净值或单位净值口径，并在报告中体现低于完整复权数据的置信度。
- 前端依赖已安装，构建通过，但尚未启动 dev server 做浏览器级验证。
- AKShare 和 Tushare 导入器尚未实现（等待后续需求）。

## 下一步

- 人工校验回测结果与 Excel 手工计算结果。
- 增加基准实验：100% 权益/QDII、75/25/0 无黄金、75/15/10 季度再平衡、不再平衡。
- 在前端启动 dev server，做一次浏览器级页面和图表验证。
