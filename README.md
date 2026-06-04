# 基金组合实验室

本项目是一个本地自用的多资产基金组合研究工具，第一版聚焦进取型 `75/15/10` 组合：

```text
权益 / QDII：75%
债券基金：15%
黄金基金：10%
```

目标是维护个人基金池、导入历史净值、创建组合实验组、运行回测、诊断防守资产效果，并生成 Markdown 研究报告。

## 当前状态

当前已完成：

- 初始化 Git 仓库。
- 完成中文产品设计文档。
- 完成实施计划文档。
- 搭建 Python-first 项目骨架。
- 增加最小指标计算测试与实现。

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

运行测试：

```bash
python3 -m unittest discover
```

依赖安装完成后可启动 API：

```bash
uvicorn app.main:app --reload
```

## 文档

- 产品设计：[docs/superpowers/specs/2026-06-04-fund-portfolio-lab-design.md](docs/superpowers/specs/2026-06-04-fund-portfolio-lab-design.md)
- 实施计划：[docs/superpowers/plans/2026-06-04-fund-portfolio-lab-implementation.md](docs/superpowers/plans/2026-06-04-fund-portfolio-lab-implementation.md)
- 当前进度：[docs/progress.md](docs/progress.md)
- 后续计划：[docs/roadmap.md](docs/roadmap.md)

