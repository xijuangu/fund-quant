# 使用说明

日期：2026-06-04

本文记录第一版本地研究工具的常用操作。当前项目定位为本地自用的基金组合研究工具，只做历史数据导入、组合回测、风险分析和研究报告，不做交易执行。

## 0. 与 fund-trace 的关系

本项目依赖 [xijuangu/fund-trace](https://github.com/xijuangu/fund-trace) 提供第一版历史净值来源，两者职责分工如下：

```text
fund-trace：
  - 维护被跟踪的基金清单
  - 添加单只基金
  - 抓取并回填历史净值
  - 将原始数据保存在 fund-trace.db

fund-quant：
  - 从 fund-trace.db 导入基金基础信息和历史净值
  - 维护资产桶、实验组、组合实验和压力区间
  - 运行组合回测、计算指标、生成研究报告
  - 提供本地 Web UI 做组合研究
```

因此，第一版的数据流是：

```text
fund-trace 抓取/回填历史净值
  -> scripts/import_fund_trace.py 导入 fund-quant
  -> fund-quant 创建实验、运行回测、生成报告
```

注意：`fund-quant` 的基金池页面“添加基金”只创建研究侧基金基础信息，不会自动抓取历史净值。需要可回测历史数据时，应先在 `fund-trace` 中添加基金并回填历史净值，再重新导入 `fund-quant`。

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
export FUND_TRACE_DB=/path/to/fund-trace/fund-trace.db
.venv/bin/python scripts/import_fund_trace.py "$FUND_TRACE_DB"
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

## 3. 单独添加新基金与历史数据

第一版推荐把 fund-trace 作为历史净值来源，fund-quant 只负责导入和回测。

### 3.1 在 fund-trace 添加单只基金

```bash
cd /path/to/fund-trace
./fund-trace add 110037
```

`fund-trace add <code>` 会自动发现基金名称，并写入 fund-trace 的 `funds` / `assets` 表。

### 3.2 拉取这只基金的历史净值

```bash
./fund-trace history 110037 --days 5000
```

说明：

- `history` 会优先读取 fund-trace 本地 SQLite。
- 如果本地没有历史净值，或最新历史净值已过期，会从东方财富历史净值接口拉取并写入 `nav_snapshots`。
- `--days 5000` 表示最多拉取约 5000 条历史净值记录。

如果刚添加了一批基金，也可以批量回填所有已跟踪基金：

```bash
./fund-trace backfill --days 5000 --sleep-ms 500
```

### 3.3 重新导入 fund-quant

回到 fund-quant 项目：

```bash
cd /path/to/fund-quant
export FUND_TRACE_DB=/path/to/fund-trace/fund-trace.db
.venv/bin/python scripts/import_fund_trace.py "$FUND_TRACE_DB"
```

导入脚本使用 `merge` 语义，可以重复执行：

- 已存在的 `fund_basic` 会更新。
- 已存在的 `fund_nav_daily` 同基金同日期记录会更新。
- 新基金和新净值会追加。

导入后检查：

```bash
.venv/bin/python - <<'PY'
from app.db.session import SessionLocal
from app.models.fund import FundBasic, FundNavDaily

code = "110037"
db = SessionLocal()
fund = db.query(FundBasic).filter(FundBasic.fund_code == code).first()
count = db.query(FundNavDaily).filter(FundNavDaily.fund_code == code).count()
first = db.query(FundNavDaily.nav_date).filter(FundNavDaily.fund_code == code).order_by(FundNavDaily.nav_date.asc()).first()
last = db.query(FundNavDaily.nav_date).filter(FundNavDaily.fund_code == code).order_by(FundNavDaily.nav_date.desc()).first()
print(fund.fund_code, fund.fund_name, fund.asset_bucket)
print("nav rows:", count, "range:", first[0] if first else None, "to", last[0] if last else None)
db.close()
PY
```

### 3.4 在 fund-quant 中调整资产桶

fund-trace 导入时会根据基金名称轻量推断资产桶。如果不准确，可以在基金池页面编辑，或直接调用 API 修改：

```bash
curl -X PUT http://localhost:8000/funds/110037 \
  -H 'Content-Type: application/json' \
  -d '{"asset_bucket":"bond"}'
```

当前支持的资产桶：

```text
a_share_equity    A股权益
overseas_qdii     海外/QDII权益
bond              债券
gold_commodity    黄金/商品
money_market      货币/现金替代
```

注意：基金池页面的“添加基金”只创建 `fund_basic`，不会自动拉取历史净值。没有足够历史净值的基金无法参与正式回测。

## 4. 运行 75/15/10 smoke 回测

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

## 5. 本次 smoke 回测结果

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

## 6. 运行服务

启动 API：

```bash
uvicorn app.main:app --reload
```

启动前端：

```bash
cd web
npm run dev
```

## 7. 测试

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
