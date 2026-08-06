# NuDM

面向粒子物理研究者与科研爱好者的论文追踪与辅助研究平台。首期聚焦**暗物质**与**中微子**方向，自动抓取 arXiv / INSPIRE-HEP 等数据源的论文，经 AI 生成结构化摘要、专题分类与相关度/热度评分，帮助研究人员持续跟进领域最新动态。

## 核心功能

- **论文抓取与去重**：定时从 arXiv、INSPIRE-HEP 抓取论文并清洗、去重入库
- **AI 解读**：生成结构化中文/英文摘要、提取关键词、自动归纳贡献与方法
- **专题聚合**：内置暗物质直接/间接探测、WIMP、Axion、Light-Mediator DM、CEvNS、0νββ、Sterile Neutrino 等专题
- **搜索与筛选**：关键词搜索、专题/实验组过滤、相关度与热度排序
- **收藏与订阅**：收藏论文、订阅专题/关键词/实验组，通知中心触达
- **后台审核**：数据源管理、抓取任务监控、论文与 AI 摘要纠错修正

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Next.js (React + TypeScript) |
| 后端 | FastAPI (Python) |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| 搜索/缓存 | Elasticsearch / Redis |
| 任务队列 | Celery + Redis |
| 部署 | Docker / Docker Compose / Nginx |

## 快速开始（开发环境）

开发环境使用 SQLite + 直接运行前后端进程，无需 Docker / Redis / PostgreSQL。

```bash
./start-dev.sh
```

脚本会自动安装依赖、初始化数据库与种子数据，并启动前后端：

- 前端：http://localhost:3001
- 后端 API：http://localhost:8080
- API 文档：http://localhost:8080/docs
- 默认管理员：`admin@nudm.dev` / `admin123`

## 生产部署

使用 Docker Compose 一键拉起全套服务（PostgreSQL、Redis、Elasticsearch、后端、前端、Nginx）：

```bash
# 含 Elasticsearch 的完整模式
docker-compose --profile full up -d
```

详见 [`docs/deployment-guide.md`](docs/deployment-guide.md)。

## 项目文档

- [`docs/program-introduce.md`](docs/program-introduce.md) — 项目定位、范围与功能大纲
- [`docs/data-model.md`](docs/data-model.md) — 数据库设计
- [`docs/deployment-guide.md`](docs/deployment-guide.md) — 部署指引
- [`docs/development-report.md`](docs/development-report.md) — 研发报告

## 目录结构

```
├── backend/            # FastAPI 后端
│   ├── app/            # 业务代码（api / core / models / services）
│   ├── alembic/        # 数据库迁移
│   └── .env.example    # 环境变量模板
├── frontend/           # Next.js 前端
├── nginx/              # 反向代理配置
├── docs/               # 项目文档
└── docker-compose.yml  # 生产部署编排
```

## 许可证

未指定。请咨询项目维护者。
