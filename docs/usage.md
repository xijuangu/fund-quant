# 使用说明

日期：2026-06-04

本文记录第一版本地研究工具的常用操作。当前项目定位为本地自用的基金组合研究工具，只做历史数据导入、组合回测、风险分析和研究报告，不做交易执行。

## 1. 准备环境

在项目根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

启动本地 PostgreSQL：

```bash
docker compose up -d postgres
```

执行数据库迁移：

```bash
.venv/bin/alembic upgrade head
```

当前默认数据库连接为：

```text
postgresql+psycopg://fund_lab:fund_lab@localhost:5432/fund_lab
```

如需修改，设置环境变量 `DATABASE_URL`。

## 2. 从 fund-trace 导入基金数据

先在 fund-trace 项目中完成基金添加和历史净值回填，再回到本项目导入：

```bash
.venv/bin/python scripts/import_fund_trace.py /Users/xijuangu/Developer/Personal/fund-trace/fund-trace.db
```

导入规则：

- `funds` 导入到 `fund_basic`。
- `nav_snapshots` 导入到 `fund_nav_daily`。
- 基金资产桶根据基金名称做轻量推断：黄金、QDII、债券、货币、A 股权益。
- 默认跳过已经不在 fund-trace 当前基金池中的 orphan 净值。
- 如需导入 orphan 净值，追加 `--include-orphans`。

当前已导入数据：

```text
基金数量：24 只
净值数量：35459 条
覆盖区间：2013-08-22 至 2026-06-03
债券基金：110037、110038、003547
复权净值：fund-trace 暂未提供，当前统一使用累计净值回测
```

## 3. 运行 75/15/10 smoke 回测

默认 smoke 组合：

```text
001595 天弘中证银行ETF联接C：45%
012349 天弘恒生科技ETF联接C：30%
110037 易方达纯债债券A：15%
000217 华安黄金ETF联接C：10%
```

运行命令：

```bash
.venv/bin/python scripts/run_smoke_backtest.py
```

默认回测设置：

```text
区间：2021-07-06 至 2026-06-03
再平衡：monthly
角色：main
报告：自动生成并写入 backtest_result.report_markdown
```

可以自定义基金和权重：

```bash
.venv/bin/python scripts/run_smoke_backtest.py \
  --start-date 2021-07-06 \
  --end-date 2026-06-03 \
  --rebalance-rule quarterly \
  --position 001595:0.45 \
  --position 012349:0.30 \
  --position 110037:0.15 \
  --position 000217:0.10
```

要求：

- 权重合计必须为 1.0。
- 基金必须已经存在于 `fund_basic`。
- 回测区间内必须有足够的共同有效净值。

## 4. 本次 smoke 回测结果

2026-06-04 已完成一次真实落库回测：

```text
实验组 ID：674b753b-fb94-4e9a-b34d-7a1ae1825cd1
实验 ID：45a7a6c3-0b36-4e94-a265-bc34a7e45385
结果 ID：4e4a7bb5-4c4d-4801-80fd-9d83b1b1f4e5
日度回测净值：1185 条
数据质量：A
报告长度：1155 字符
```

核心指标：

```text
累计收益：32.50%
年化收益：6.17%
年化波动：15.21%
最大回撤：-25.64%
夏普比率：0.4693
卡玛比率：0.2405
交易日数：1185
```

这些结果只代表当前基金池和当前净值口径下的历史回测，不构成投资建议。

## 5. 运行服务

启动 API：

```bash
uvicorn app.main:app --reload
```

启动前端：

```bash
cd web
npm run dev
```

## 6. 测试

后端测试：

```bash
.venv/bin/python -m pytest -q
```

前端类型检查和构建：

```bash
cd web
npm run build
```

说明：当前 `build` 脚本已包含 `tsc -b && vite build`，因此会同时执行 TypeScript 类型检查和 Vite 构建。
