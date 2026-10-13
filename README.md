# NuDM

面向粒子物理研究者与科研爱好者的论文追踪与辅助研究平台。首期聚焦**暗物质**与**中微子**方向，自动抓取 arXiv / INSPIRE-HEP 等数据源的论文，经 AI 生成结构化摘要、专题分类与相关度/热度评分，帮助研究人员持续跟进领域最新动态。

## 核心功能

- **论文抓取与去重**：定时从 arXiv、INSPIRE-HEP 抓取论文并清洗、去重入库
- **AI 解读**：生成结构化中文/英文摘要、提取关键词、自动归纳贡献与方法
- **专题聚合**：内置暗物质直接/间接探测、WIMP、Axion、Light-Mediator DM、CEvNS、0νββ、Sterile Neutrino 等专题
- **搜索与筛选**：Elasticsearch 全文检索（结果高亮、相关度/热度排序）、专题/实验组过滤
- **收藏与订阅**：收藏论文、订阅专题/关键词/实验组，通知中心触达
- **后台审核**：数据源管理、抓取任务监控、论文与 AI 摘要纠错修正

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Next.js (React + TypeScript) |
| 后端 | FastAPI (Python) |
| 数据库 | SQLite（轻量开发）/ PostgreSQL（主环境） |
| 搜索/缓存 | Elasticsearch / Redis |
| 任务队列与定时 | Celery + Celery Beat + Redis |
| 部署 | Docker / Docker Compose / Nginx |

## 快速开始（开发环境，SQLite 轻量模式）

不依赖 Docker / Redis / PostgreSQL，使用 SQLite 直接运行前后端进程：

```bash
./start-dev.sh
```

脚本会自动安装依赖、初始化数据库与种子数据，并启动前后端：

- 前端：http://localhost:3001
- 后端 API：http://localhost:8080
- API 文档：http://localhost:8080/docs

> 说明：开发环境的访问地址与默认管理员账号仅由开发脚本在本地生成，请勿在生产环境使用，并妥善管理相关密钥。

## 完整运行（推荐，Docker Compose 全栈）

使用 Docker Compose 拉起完整服务（PostgreSQL、Redis、Elasticsearch、后端、前端、Nginx、Celery worker + beat）：

```bash
docker-compose --profile full up -d --build
```

统一入口（Nginx）为 `http://127.0.0.1:9152`，API 经 `/api/*` 反代到后端（内部路由在根路径）。后台组件：

| 服务 | 说明 |
| --- | --- |
| `postgres` / `redis` / `elasticsearch` | 数据库 / 缓存与消息队列 / 全文检索 |
| `backend` / `frontend` / `nginx` | API / 前端 / 统一入口 |
| `celery_worker` / `celery_beat` | 异步任务执行与定时调度（每日抓取 arXiv + INSPIRE，每小时处理新论文分类与摘要） |

详见 [`docs/deployment-guide.md`](docs/deployment-guide.md)。

## AI 解读接入（OpenAI 兼容）

AI 摘要/分类使用 OpenAI 兼容接口，可对接 OpenAI 或国产模型（如 DeepSeek）。在 `backend/.env` 配置（该文件已被 git 忽略，请勿提交密钥）：

```ini
OPENAI_API_KEY=你的-key
OPENAI_BASE_URL=https://api.deepseek.com/v1   # 或 https://hpc-api.westlake.edu.cn/v1 等网关
OPENAI_MODEL=deepseek-chat                     # 默认 gpt-4o-mini，按所用服务配置
```

生成/重新生成摘要可在后台「AI 摘要审核」页触发，或由 Celery 定时任务自动对新论文生成。

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
