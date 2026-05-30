# 酷里 Kuli 官网与订单系统

酷里是一个面向公开发布的服务官网与订单管理系统。当前主线技术栈已经切换为 Nuxt / Vue 3 / TypeScript 前端 + FastAPI / Python 后端，围绕“先把说不清的需求收进来，再把订单推进清楚”设计。

系统支持服务详情、小纸条咨询、邮箱密码登录、用户订单工作台、管理员订单管理台、附件对象存储、人工报价/付款/交付、订单自动化建议、知识库检索和 3D 小猫服务助手“小酷”。

## 当前功能

- 官网首页、服务列表、服务详情页和交易规则说明。
- `/services/:slug` 服务详情路由，覆盖 AI 工具、文档处理、小工具开发、部署配置、API/token 和“不知道怎么分”。
- 游客可浏览首页、服务详情、文档中心、产品页、法律页面和登录页；写小纸条、我的订单、个人主页、设置、邀请和通知中心需要登录。
- 邮箱密码登录/注册，支持邮箱验证、密码重置，区分管理员账号和一般账号。
- 登录后右上角进入账号菜单，可访问个人主页、我的订单、设置、积分邀请、通知中心和退出登录。
- 普通账号只能查看自己的订单、进度、沟通、附件、报价、付款和交付物。
- 管理员可查看全部订单，并维护状态、优先级、报价、成本、利润、公开备注、内部备注、付款记录和交付物。
- 管理员公开回复会创建通知事件和站内通知；普通用户可在通知中心查看、标记已读，邮件失败不影响站内提醒。
- 公开页面补齐 title/description、canonical、Open Graph、FAQ structured data、`sitemap.xml` 和 `robots.txt`。
- 小酷 3D 小猫助手支持页面引导、服务问答、需求整理、订单状态解释、减少动画、静音、隐藏本页等控制。
- 后端提供需求润色、订单自动化建议、小酷会话、知识库检索、管理员搜索接口、local/S3/R2/OSS 预签名上传适配和 LLM/RAG fallback 入口。

## 目录结构

```text
.
├── apps/                         # 前后端应用
│   ├── api/                      # Python + FastAPI 后端
│   │   ├── app/
│   │   │   ├── api/              # HTTP 路由：auth、services、orders、admin、docs、agent、health
│   │   │   ├── agents/           # 小酷 Agent、提示词、知识库检索与业务边界
│   │   │   ├── core/             # 配置、环境变量、通用基础设施
│   │   │   ├── models/           # SQLAlchemy 数据模型
│   │   │   ├── notifications/    # 站内通知、邮件模板和通知事件
│   │   │   ├── repositories/     # 数据访问层
│   │   │   ├── schemas/          # Pydantic 请求/响应模型
│   │   │   ├── services/         # 订单、附件、对象存储、知识库、AI 自动化等业务服务
│   │   │   └── tasks/            # Celery worker 与后台任务
│   │   ├── alembic/              # 数据库 migration
│   │   ├── knowledge/docs/       # 文档中心与小酷 RAG 共用的 Markdown 知识库
│   │   └── tests/                # API、权限、通知、小酷和脚本测试
│   └── web/                      # Vue 3 + Nuxt + TypeScript 前端
│       ├── app/
│       │   ├── pages/            # 官网、服务详情、文档中心、订单、后台、个人中心等路由页面
│       │   ├── components/       # 页面组件、订单组件、后台组件、小酷 3D/对话组件
│       │   ├── stores/           # Pinia 状态：登录用户、订单、小酷等
│       │   ├── composables/      # API client、SEO、业务复用逻辑
│       │   ├── middleware/       # 登录/管理员路由守卫
│       │   └── assets/css/       # 全局视觉样式
│       ├── public/               # OG 图片等静态资源
│       └── nuxt.config.ts        # Nuxt runtime config 与构建配置
├── packages/contracts/           # FastAPI OpenAPI 输出和前端类型合同
├── scripts/                      # 一键启动、停止、知识库索引、合同生成、烟测和生产栈验证
├── docs/                         # 技术架构、2.0/3.0 计划和设计文档
├── openspec/                     # OpenSpec changes、proposal、design、spec deltas 和 tasks
├── docker-compose.yml            # 本地 Postgres/pgvector + Redis
├── .env.example                  # 本地完整环境变量模板，带逐项填写说明
├── .env.production.example       # 生产环境变量模板
└── package.json                  # npm workspace 与根命令入口
```

已经迁移出的旧目录：

- `frontend/`：旧 Vite/React 前端，已由 `apps/web` 替代。
- `backend/`：旧 Node.js 后端，已由 `apps/api` 替代。

## 前后端入口

| 部分 | 目录 | 技术栈 | 主要职责 |
| --- | --- | --- | --- |
| 前端 | `apps/web` | Vue 3 + Nuxt + TypeScript + Pinia + Three.js | 官网、服务详情、文档中心、产品页、登录、个人中心、订单工作台、管理后台、小酷 3D 组件 |
| 后端 | `apps/api` | Python + FastAPI + SQLAlchemy + Alembic + Redis/Celery | 登录鉴权、权限控制、订单、附件、通知、知识库、小酷 Agent、健康检查和后台任务 |
| 合同 | `packages/contracts` | FastAPI OpenAPI + TypeScript 类型 | 让前端按后端响应模型消费 API |

当前公开和受保护路由：

| 路由 | 说明 |
| --- | --- |
| `/`、`/services`、`/services/:slug` | 官网与服务详情 |
| `/help`、`/help/:slug` | 文档中心和五个固定文档 |
| `/products` | 公开产品 / 工具导航 |
| `/login` | 登录、注册、邮箱验证和密码重置入口 |
| `/legal/privacy`、`/legal/terms`、`/legal/upload-policy` | 隐私、服务条款和上传说明 |
| `/note` | 登录后写小纸条 |
| `/me`、`/settings`、`/referrals`、`/notifications` | 登录后个人主页、设置、积分邀请和通知中心 |
| `/orders`、`/orders/:orderNumber` | 普通账号订单列表和订单工作台 |
| `/admin`、`/admin/orders/:orderNumber` | 管理员订单管理台 |

## 环境准备

需要本机已安装 Node.js、npm 和 uv。Python 依赖使用 uv 管理，不要混用系统 Python、Homebrew Python 和 sudo pip。

推荐第一次启动前先显式安装依赖并复制环境变量模板：

```bash
npm install
uv sync --project apps/api
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
```

根目录 `.env` 是从仓库根目录启动时的主配置；`apps/api/.env` 方便单独进入 `apps/api` 启动 FastAPI；`apps/web/.env` 方便单独进入 `apps/web` 启动 Nuxt。不要把真实 `.env` 提交到 git。

如果直接运行 `npm run start:local`，脚本也会在缺失时自动复制这些 `.env` 文件。

本地默认端口：

- Nuxt 前端：`http://127.0.0.1:3000`
- FastAPI 后端：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/api/health`
- 依赖健康检查：`http://127.0.0.1:8000/api/health/deps`

## 启动方式

### 一键启动完整本地环境

推荐本地联调使用：

```bash
npm run start:local
```

它会自动安装依赖、创建缺失的 `.env`、启动 Postgres/pgvector 和 Redis、创建本地 `kuli_runtime` 数据库、运行 migration、索引知识库、构建 Nuxt，并用 tmux 启动 API、Web 和 worker。

启动完成后访问：

- Web：`http://127.0.0.1:3000`
- API 健康检查：`http://127.0.0.1:8000/api/health`
- 依赖健康检查：`http://127.0.0.1:8000/api/health/deps`

查看后台日志：

```bash
tmux attach -t kuli-api
tmux attach -t kuli-web
tmux attach -t kuli-worker
```

如果默认端口被占用，可以覆盖端口启动：

```bash
API_PORT=8010 WEB_PORT=3010 npm run start:local
```

如果想隔离另一套本地数据库：

```bash
KULI_LOCAL_DB_NAME=kuli_runtime_dev2 npm run start:local
```

### 停止本地环境

停止本地完整服务：

```bash
npm run stop:local
```

默认会同时关闭 tmux 服务和 Docker stack；如果想保留 Postgres/Redis 容器：

```bash
bash scripts/stop-local.sh --keep-stack
```

### 开发模式启动

只用热更新开发模式启动前后端：

```bash
npm run dev
```

分别手动启动 API 和 Web：

```bash
PYTHONPATH=apps/api uv run --project apps/api uvicorn app.main:app --reload --reload-dir apps/api/app --reload-dir apps/api/alembic --host 0.0.0.0 --port 8000
npm run dev --workspace @kuli/web
```

数据库迁移和后台任务：

```bash
npm run db:migrate
npm run worker
```

### 生产相近验证

本地拉起 Postgres/pgvector 和 Redis 后，可运行生产栈 smoke test：

```bash
npm run stack:up
npm run verify:production-stack
npm run stack:down
```

`verify:production-stack` 默认只允许验证本地数据库；如果要验证远程预发/生产库，需要显式设置 `ALLOW_NONLOCAL_PRODUCTION_VERIFY=true`。

生产构建：

```bash
npm run build
```

## Demo 账号

| 角色 | 邮箱 | 密码 |
| --- | --- | --- |
| 管理员 | `admin@kuli.local` | `KuliAdmin123!` |
| 一般账号 | `demo@kuli.local` | `KuliUser123!` |
| 一般账号 | `other@kuli.local` | `KuliOther123!` |

`demo` 与 `other` 用于验证普通账号只能看到自己的订单；管理员可以看到全部订单和内部字段。

## 环境变量

变量来自根目录 `.env.example`、`apps/api/.env.example` 和 `apps/web/.env.example`：

| 变量 | 默认值 | 说明 | 获取方式 |
| --- | --- | --- |
| `APP_ENV` | `local` | 运行环境；staging/production 会把更多依赖视为必需 | 自己按环境填写 |
| `APP_SECRET_KEY` | 示例值 | 登录 token、邮箱验证和密码重置 token 的签名密钥 | `openssl rand -hex 32` 生成 |
| `DATABASE_URL` | `postgresql+psycopg://kuli:kuli@localhost:5432/kuli_runtime` | Postgres/pgvector 连接；local 也可临时用 SQLite fallback | 本地 Docker 或云数据库控制台 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis/Celery 队列连接 | 本地 Docker 或云 Redis |
| `CORS_ORIGINS` | 本地前端地址 | 后端允许访问的前端域名 | 本地地址和正式官网域名 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 登录 token 有效期 | 自己按安全策略填写 |
| `NUXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` | Nuxt 请求 FastAPI 的基础地址 | 本地 API 地址或线上 API 域名 |
| `NUXT_PUBLIC_SITE_URL` | `http://127.0.0.1:3000` | sitemap、robots、canonical 和 Open Graph 使用的站点地址 | 本地前端地址或正式官网域名 |
| `NUXT_PUBLIC_APP_NAME` | `Kuli` | 前端展示和元信息中的应用名 | 自己填写 |
| `NUXT_PUBLIC_ENABLE_XIAOKU` | `true` | 是否显示小酷浮层 | true/false |
| `OBJECT_STORAGE_PROVIDER` | `local` | 对象存储 provider；`local`/`s3`/`r2`/`oss` | 本地用 local；线上按云厂商选择 |
| `OBJECT_STORAGE_ENDPOINT` | 空 | R2/S3 endpoint；OSS 可填 `https://oss-cn-hangzhou.aliyuncs.com` | 对象存储控制台 |
| `OBJECT_STORAGE_BUCKET` | `kuli-order-files` | 附件 bucket 名称 | 对象存储控制台创建 |
| `OBJECT_STORAGE_REGION` | `auto` | 存储区域 | 对象存储控制台 |
| `OBJECT_STORAGE_LOCAL_DIR` | `apps/api/data/uploads` | local provider 的本地附件保存目录 | 本地保持默认；线上用对象存储 |
| `OBJECT_STORAGE_ACCESS_KEY_ID` | 空 | 对象存储 access key | 云厂商 IAM/RAM 创建最小权限 key |
| `OBJECT_STORAGE_SECRET_ACCESS_KEY` | 空 | 对象存储 secret key | 云厂商 IAM/RAM 创建 |
| `OBJECT_STORAGE_PUBLIC_BASE_URL` | 空 | 可选 CDN 或 bucket 公开基础地址；私有下载可留空 | CDN / 对象存储域名 |
| `OBJECT_STORAGE_PRESIGN_EXPIRES_SECONDS` | `3600` | 上传/下载签名有效期 | 自己按安全策略填写 |
| `LLM_PROVIDER` | `local-rules` | AI provider；配置 key 后可走 OpenAI-compatible Chat Completions | OpenAI 或兼容服务 |
| `LLM_MODEL` | `local-rules` | 后端通用 LLM 模型名 | 服务商模型列表 |
| `LLM_API_KEY` | 空 | 通用 LLM API Key | 服务商控制台 |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API 地址 | 服务商文档 |
| `OPENAI_API_KEY` | 空 | 小酷远程 LLM / embedding key | OpenAI 或兼容服务控制台 |
| `OPENAI_MODEL` | `gpt-5.5` | 小酷远程回答模型；未填 key 时走本地 fallback | 服务商模型列表，需填真实可用模型 |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API 地址 | 服务商文档 |
| `LLM_TIMEOUT_SECONDS` | `20` | LLM 请求超时 | 自己按体验要求填写 |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 知识库 embedding 模型 | 服务商模型列表 |
| `VECTOR_DIMENSION` | `1536` | embedding 向量维度 | 与 embedding 模型文档保持一致 |
| `KNOWLEDGE_ROOT` | `apps/api/knowledge/docs` | 文档中心和小酷 RAG 的 Markdown 知识库目录 | 当前仓库目录 |
| `XIAOKU_AGENT_ENABLED` | `true` | 是否启用小酷 Agent | true/false |
| `XIAOKU_REQUIRE_CITATIONS` | `true` | 小酷回答是否要求引用知识来源 | true/false |
| `MAIL_PROVIDER` | 空 | 邮件 provider；local 可留空，邮件事件失败但站内通知仍可见 | SMTP 或邮件 API 服务商 |
| `MAIL_FROM` / `MAIL_REPLY_TO` | 空 | 发件人和回复地址 | 邮件服务商配置 |
| `SMTP_HOST` / `SMTP_PORT` | 空 / `587` | SMTP 连接配置 | 邮件服务商后台 |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | 空 | SMTP 凭据 | 邮件服务商后台 |
| `EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES` | `60` | 邮箱验证链接过期时间 | 自己按安全策略填写 |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | `30` | 密码重置链接过期时间 | 自己按安全策略填写 |
| `NOTIFICATION_MAX_RETRIES` | `3` | 通知 worker 最大重试次数 | 自己按邮件服务稳定性填写 |

OSS provider 已支持表单直传 policy 和短期签名下载；正式发布时需要使用生产 bucket、最小权限 access key 和私有读写策略。

## 正式版配置状态

仓库已提供 `.env.production.example` 作为正式环境模板。正式发布时还需要你填入真实值：

- 生产域名和 API 域名：用于 `NUXT_PUBLIC_SITE_URL`、`NUXT_PUBLIC_API_BASE_URL`、`CORS_ORIGINS`。
- 强 `APP_SECRET_KEY`：不能使用示例值。
- Postgres + pgvector：不要使用 SQLite 或 demo 数据库。
- Redis：用于 worker、通知、知识索引和后续队列能力。
- 私有对象存储 bucket：S3/R2/OSS 均可，建议最小权限 key、私有 ACL、短期签名下载。
- 邮件 provider：用于邮箱验证、密码重置和订单通知。当前代码已有事件、模板和 worker 边界，真实 provider 发送逻辑上线前仍需实测。
- LLM / embedding key：未配置时小酷会使用本地规则 fallback；配置后才会走远程模型和 embedding。
- 管理员账号：当前 seed demo 管理员只适合本地验证，正式生产应改为一次性初始化管理员或手动后台创建，并删除 demo 密码。

上线前至少执行：

```bash
npm run stack:up
npm run db:migrate
npm run verify:production-stack
npm run contracts:check
npm run typecheck
npm run test
npm run build
```

并在填好真实对象存储、邮件和 LLM key 后做一次端到端手工测试：注册/验证邮箱、写小纸条、上传附件、管理员报价和回复、通知中心、密码重置、小酷问答。

## 常用命令

```bash
npm run contracts:generate
npm run contracts:check
npm run typecheck
npm run test
npm run build
```

浏览器联调烟测需要先保持 `npm run dev` 运行，然后另开终端执行：

```bash
npm run smoke:browser
```

它会用本机 Chrome 覆盖桌面/移动页面、小酷面板、SEO 元数据、sitemap/robots、服务详情跳转、登录门禁、密码重置入口、小纸条提交、普通用户订单权限、通知中心和管理员搜索。

生产栈联调需要先确保 Docker/OrbStack 正在运行：

```bash
npm run stack:up
npm run verify:production-stack
npm run stack:down
```

`verify:production-stack` 会验证 Postgres 连接、Alembic migration、pgvector extension、核心表、生产模式 API 初始化，以及 Redis ping / 写入 / 读取。

`GET /api/health/deps` 会返回数据库、Redis、对象存储、邮件 provider、LLM 和 RAG 的状态。local 环境允许 Redis、邮件和远程 LLM 降级；staging/production 会把 Redis、对象存储、邮件等发布依赖标记为必需项，用于上线前检查。

文档中心和小酷知识库使用同一组 Markdown 源文件。每次修改 `apps/api/knowledge/docs/` 后运行：

```bash
PYTHONPATH=apps/api uv run --project apps/api python scripts/index_knowledge.py
PYTHONPATH=apps/api uv run --project apps/api python scripts/knowledge_doctor.py
```

文档 frontmatter 必须包含 `slug`、`title`、`description`、`tags`、`order`、`updated_at`、`status`；第一版只向前端和小酷发布 `status: published` 的文档。

如需验证 OpenSpec 变更：

```bash
openspec validate add-kuli-order-portal --strict
```

## 数据与附件

- 本地 SQLite fallback 默认写入 `apps/api/data/kuli-v2.sqlite`；正式目标是 Postgres + pgvector。
- 本地附件 fallback 默认写入 `apps/api/data/uploads/`。
- `docker-compose.yml` 可用于启动 Postgres/pgvector 和 Redis，配合 `npm run verify:production-stack` 做生产栈 smoke test。
- 附件文件进入对象存储，数据库只保存 metadata、权限归属、文件状态、checksum 和 storage key。
- local provider 支持本地上传与签名下载；S3/R2 provider 使用预签名上传/下载；OSS provider 使用表单 policy 直传和短期签名下载。
- `.env`、`apps/api/data/`、`apps/web/.nuxt/`、`apps/web/.output/`、`node_modules/`、`.codex/` 等本地或生成文件已加入 `.gitignore`。

## 更多文档

- [技术架构](docs/TECHNICAL_ARCHITECTURE.md)
- [3.0 正式发布升级计划](docs/3.0plan.md)
- [2.0 功能迭代计划](docs/2.0pan.md)
- [2.0 订单自动化与小酷 agent 设计](docs/superpowers/specs/2026-05-29-kuli-v2-order-automation-xiaoku-agent-design.md)
