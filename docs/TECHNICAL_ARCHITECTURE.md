# 技术架构

本文档按当前代码实现同步，描述酷里官网与订单系统的前后端技术栈、运行结构、数据边界和已知限制。当前仓库主线已经切换为 Nuxt / Vue 3 / TypeScript 前端 + FastAPI / Python 后端。

## 总览

```mermaid
flowchart LR
  User["浏览器用户"] --> Nuxt["Nuxt / Vue 3 前端"]
  Nuxt --> FastAPI["FastAPI / Python API"]
  FastAPI --> SQL["SQLite fallback / Postgres + pgvector"]
  FastAPI --> Storage["local / S3 / R2 / OSS presign"]
  FastAPI --> Knowledge["知识库检索 / RAG fallback"]
  FastAPI --> Agent["小酷与订单自动化"]
  Agent --> LLM["local-rules / OpenAI-compatible LLM"]
  FastAPI --> Redis["Redis / Celery worker"]
```

前端通过 `NUXT_PUBLIC_API_BASE_URL` 调用 FastAPI；后端负责登录鉴权、角色权限、服务目录、订单、消息、附件、报价、付款记录、交付物、知识库检索、小酷会话和订单自动化建议。

## 技术栈

| 层 | 技术 | 当前用途 |
| --- | --- | --- |
| 前端 | Vue 3 + Nuxt + TypeScript | 官网、服务详情、小纸条、订单工作台、管理后台、小酷组件 |
| 前端状态 | Pinia + Nuxt composables | 登录态、API client、OpenAPI 类型消费 |
| 3D 交互 | Three.js | 小酷 3D 小猫形象、状态动画、轻量交互 |
| 后端 | Python + FastAPI | API、鉴权、订单领域、知识库、小酷 agent、管理员自动化 |
| 数据 | SQLAlchemy + Alembic | 本地 SQLite fallback，正式环境 Postgres/pgvector |
| 异步 | Redis + Celery | embedding、订单自动化、附件分析和通知任务入口 |
| 存储 | local / S3 / R2 / OSS presign | 文件对象存储，数据库仅保存 metadata 和 storage key |
| AI | local-rules / OpenAI-compatible LLM | 本地规则 fallback、RAG 知识检索、小酷回答入口 |
| 合同 | FastAPI OpenAPI + 生成 TS 类型 | 后端响应模型驱动前端类型 |
| 工程 | npm workspaces + uv + concurrently | 前后端依赖、本地并行启动、Python 环境管理 |

## 前端架构

主要文件：

- `apps/web/app/pages/`：Nuxt 文件路由，包含首页、服务列表、服务详情、文档中心、产品页、小纸条、登录、个人中心、普通用户订单、通知中心、管理员后台和法律页面。
- `apps/web/app/composables/useApi.ts`：封装 FastAPI 请求、附件上传和前端合同类型。
- `apps/web/app/stores/auth.ts`：Pinia 登录态和 token 恢复。
- `apps/web/app/components/xiaoku/XiaokuAvatar.vue`：小酷 3D 小猫形象、页面感知、动作状态、对话面板和用户控制。
- `apps/web/app/assets/css/main.css`：全局视觉样式、响应式布局和小酷浮层稳定性规则。
- `apps/web/app/types/api-contract.ts`：由 OpenAPI 生成的前端 API 类型。

当前路由：

| 路由 | 页面 |
| --- | --- |
| `/` | 官网首页 |
| `/services` | 服务列表 |
| `/services/[slug]` | 服务详情 |
| `/help` | 文档中心首页，默认展示快速开始 |
| `/help/[slug]` | 文档详情，包含快速开始、核心概念、FAQ、指南和联系我们 |
| `/products` | 公开产品 / 工具导航页 |
| `/note` | 写小纸条 |
| `/login` | 登录 |
| `/me` | 个人主页，展示邮箱、订单摘要、积分、邀请和最近通知 |
| `/settings` | 账号设置 |
| `/referrals` | 积分与邀请注册 |
| `/notifications` | 站内通知中心 |
| `/orders` | 普通账号订单列表 |
| `/orders/[orderNumber]` | 普通账号订单工作台 |
| `/admin` | 管理员订单搜索与列表 |
| `/admin/orders/[orderNumber]` | 管理员订单操作台 |
| `/legal/privacy` | 隐私政策 |
| `/legal/terms` | 服务条款 |
| `/legal/upload-policy` | 上传内容与敏感信息说明 |

## 后端架构

主要文件：

- `apps/api/app/main.py`：FastAPI app、路由、鉴权依赖、订单 DTO 输出。
- `apps/api/app/models/entities.py`：SQLAlchemy models、seed 数据、核心业务表。
- `apps/api/app/schemas/api.py`：请求/响应模型，作为 OpenAPI 合同源。
- `apps/api/app/services/catalog.py`：服务目录与知识库 seed 源。
- `apps/api/app/services/automation.py`：订单 intent 判断、缺失材料识别、自动化建议和待办生成。
- `apps/api/app/services/xiaoku.py`：小酷会话、订单状态回答、知识库回答。
- `apps/api/app/services/rag.py`：知识库检索 fallback。
- `apps/api/app/services/embeddings.py`：本地确定性 embedding fallback 和远程 embedding 入口。
- `apps/api/app/services/llm.py`：OpenAI-compatible Chat Completions 适配入口。
- `apps/api/app/services/storage.py`：local、S3/R2 和 OSS 预签名上传/下载适配。
- `apps/api/app/services/health.py`：数据库、Redis、对象存储、邮件、LLM 和 RAG 依赖健康检查。
- `apps/api/app/notifications/`：通知事件、邮件 provider 边界、站内通知和邮件模板目录。
- `apps/api/app/tasks/`：Celery worker、embedding、订单自动化、通知发送和附件分析任务入口。
- `apps/api/alembic/`：数据库迁移，包含 Postgres pgvector 扩展和 HNSW 索引。

## API 边界

当前 API 按以下领域组织：

- 健康检查：`GET /api/health`、`GET /api/health/deps`
- 服务目录：`GET /api/services`、`GET /api/services/:slug`
- 知识库：`GET /api/knowledge`、`GET /api/knowledge/search`
- 需求润色：`POST /api/ai/polish-demand`
- 登录注册：`POST /api/auth/login`、`POST /api/auth/register`、`GET /api/auth/me`
- 账号安全：`POST /api/auth/email-verification/request`、`POST /api/auth/email-verification/confirm`、`POST /api/auth/password-reset/request`、`POST /api/auth/password-reset/confirm`
- 游客兼容询单：`POST /api/inquiries` 保留为兼容 API；正式前端主流程要求登录后创建订单。
- 普通账号订单：`GET /api/orders`、`POST /api/orders`、`GET /api/orders/:orderNumber`
- 普通账号协作：`POST /api/orders/:orderNumber/messages`、`POST /api/orders/:orderNumber/attachments`、`POST /api/orders/:orderNumber/accept`
- 站内通知：`GET /api/notifications`、`GET /api/notifications/unread-count`、`PATCH /api/notifications/:id/read`、`PATCH /api/notifications/read-all`
- 附件上传：`POST /api/uploads/presign`、`POST /api/uploads/local/:objectKey`、`GET /api/uploads/local/:objectKey`
- 管理员订单：`GET /api/admin/orders`、`GET /api/admin/orders/:orderNumber`、`PATCH /api/admin/orders/:orderNumber`
- 管理员业务动作：报价、付款、交付物、消息、自动化建议、附件重试解析。
- 小酷会话：`POST /api/agent/sessions`、`POST /api/agent/chat`

权限边界：

- 未登录用户只能查看公开服务内容、文档中心、产品页、法律页面和登录页；正式前端不会让游客直接提交小纸条。
- 普通账号只能通过 `owner_user_id` 访问自己的订单。
- 管理员角色可以访问全部订单，并看到成本、利润、内部备注和自动化建议。
- 客户响应会过滤内部字段；管理员响应包含内部字段。
- 小酷用户侧只能读取公开知识和当前登录用户自己的订单摘要，不读取其他用户订单、成本、利润、管理员备注或内部标签。

## 数据模型

核心表由 SQLAlchemy models 和 Alembic migration 维护：

- `users`：用户账号、密码哈希、角色、展示名、邮箱验证状态、失败登录次数、积分和邀请码。
- `email_verification_tokens`、`password_reset_tokens`：邮箱验证和密码重置一次性 token 哈希、过期时间、使用时间和创建 IP。
- `service_categories`：服务分类和详情 JSON。
- `orders`：订单主表，包含归属用户、服务类型、需求、状态、报价、成本、利润、备注和时间戳。
- `order_events`：订单状态时间线。
- `order_messages`：订单沟通记录。
- `order_attachments`：附件 metadata、checksum、解析状态、重试次数和 storage key。
- `quotes`：报价记录。
- `payment_records`：人工收款记录。
- `deliverables`：交付物记录。
- `admin_audit_logs`：管理员审计日志。
- `notifications`、`notification_events`：用户站内通知、邮件/系统通知事件、发送状态和失败重试信息。
- `knowledge_articles`、`knowledge_chunks`、`knowledge_embeddings`：知识库与 embedding 数据。
- `agent_sessions`、`agent_messages`、`agent_tool_calls`：小酷会话与工具调用记录。
- `order_automation_suggestions`、`order_todos`、`order_ai_summaries`、`order_reply_drafts`：订单自动化数据。

本地 seed 会创建管理员和两个普通账号，并写入服务目录、知识库与示例订单，便于验证权限隔离。

## 存储策略

- 本地开发默认使用 SQLite fallback 和 local object storage。
- 正式发布目标是 Postgres + pgvector + Redis + S3/R2-compatible 或阿里云 OSS 对象存储。
- 附件上传流程为：前端请求 presign → 上传文件对象 → 记录附件 metadata → 后台/同步任务分析附件 metadata。
- local provider 支持本地上传与签名下载；S3/R2 provider 使用 S3-compatible 预签名表单上传和预签名下载；OSS provider 使用 OSS 表单 policy 直传和短期签名下载。
- 数据库只保存附件 metadata、上传者、可见性、文件大小、类型、checksum、解析状态和 storage key。

## 发布健康检查

- `/api/health` 只表示 API 进程存活。
- `/api/health/deps` 返回数据库、Redis、对象存储、邮件 provider、LLM 和 RAG 的结构化状态。
- local 环境允许 Redis、邮件和远程 LLM 降级，便于只跑前后端和 SQLite fallback。
- staging/production 环境把 Redis、对象存储、邮件等发布依赖标记为必需；任一必需项失败时 `ok` 为 `false`，但接口仍返回 200，便于监控系统采集完整故障原因。
- RAG 健康状态根据知识文章、chunk 和 embedding 数量区分 `remote-rag` 与 `local-rules-fallback`，知识索引失败时不阻塞主站启动，但会在依赖检查中暴露。

## 文档与知识库治理

- 文档中心源文件固定在 `apps/api/knowledge/docs/`，小酷 RAG、文档中心页面和搜索接口使用同一份 Markdown。
- 每个 Markdown frontmatter 必须包含 `slug`、`title`、`description`、`tags`、`order`、`updated_at`、`status`。
- `status` 允许 `published`、`draft`、`deprecated`；第一版 `GET /api/docs*` 只返回 `published` 文档。
- 发布后的 `slug` 不应随意修改；必须改名时通过 `aliases` 兼容旧路径，再逐步迁移入口。
- 修改文档后必须运行 `scripts/index_knowledge.py` 和 `scripts/knowledge_doctor.py`，doctor 会检查必需文档、必填 frontmatter、slug 重复、空文档、非法状态、chunk 数和 embedding 维度。
- 文档中涉及价格、周期、成功率时必须保持谨慎措辞，并以管理员确认为准；不得要求用户发送密码、验证码、私钥或支付凭证。

## 小酷 Agent

小酷是固定浮层的 3D 小猫服务助手，不参与页面布局计算。它根据当前页面切换 `idle`、`curious`、`thinking`、`happy`、`alert`、`sleep`、`hide`、`calm` 等状态。

稳定性规则：

- 不遮挡主 CTA、表单输入、订单列表、后台表格和付款/上传入口。
- 服务列表、小纸条、订单和后台等密集页面默认 mini/hide。
- 移动端默认收缩，密集页面贴边隐藏，打开后使用半屏对话面板。
- 用户可以关闭鼠标追随、减少动画、静音或隐藏本页。

## 安全与权限

- 密码使用 PBKDF2 哈希保存，不明文入库。
- 登录后端签发 HMAC token，前端以 Bearer token 调用受保护 API。
- 管理后台路由需要 `role === "admin"`。
- 普通账号订单查询使用用户 ID 与订单号共同过滤，避免跨账号访问。
- 附件 presign 和 metadata 写入会校验订单归属；本地下载链接带过期签名。
- 生产环境必须替换 `APP_SECRET_KEY`，并避免使用示例账号和本地 SQLite 数据。
- 邮件、对象存储、LLM 和 Redis key 只从 env 读取，不写入代码或前端 bundle。
- 邮箱验证和密码重置只保存 token hash；邮件正文只通过统一 `notification_events` 事件链路发送，密码重置 request 不暴露邮箱是否存在。

## SEO 与公开增长

- `apps/web/app/composables/useKuliSeo.ts` 统一公开页 title、description、canonical、Open Graph 和 JSON-LD 输出。
- 首页、服务列表、服务详情、文档中心、文档详情、产品页、登录页和法律页都声明页面级 metadata。
- 服务详情和 FAQ 文档输出 `FAQPage` structured data。
- `apps/web/server/routes/sitemap.xml.ts` 输出公开路由 sitemap；`apps/web/server/routes/robots.txt.ts` 允许公开内容，阻止订单、后台、个人中心、通知和写小纸条等私有路由。
- 分享图位于 `apps/web/public/og-image.svg`，由 `NUXT_PUBLIC_SITE_URL` 拼接为绝对地址。

## 当前限制

- 真实 Postgres/pgvector 迁移已生成离线 SQL，但本机 Docker/OrbStack 不可用时无法做 live migration smoke。
- OSS provider 已有单独签名适配器；上线前仍需使用生产 bucket、私有 ACL、最小权限密钥和跨域规则做实测。
- 邮件通知已经有 `notification_events`、模板、worker 入口和失败记录，但真实 SMTP/API provider 发送逻辑仍需接入生产邮件服务后实测。
- 站内通知中心和管理员公开回复通知已实现；报价、付款、交付、验收、订单状态变化、邀请积分等通知类型仍需继续补齐触发链路。
- 注册、小酷调用、密码规则和登录锁定已有基础防护；上传、消息、订单写入等所有写接口的统一限流、请求体限制和生产级滥用检测仍需继续增强。
- 在线支付网关未接入，付款记录只支持管理员人工登记。
- 小酷当前是程序化 Three.js 轻量模型，后续可替换为正式 glTF/GLB 美术资产。
- 订单语义搜索、生产级观测、备份、病毒扫描和附件内容解析仍需按正式发布标准继续增强。

## 验证命令

```bash
npm run contracts:check
npm run typecheck
npm run test
npm run build
```

浏览器联调验证：

```bash
npm run dev
npm run smoke:browser
```

`smoke:browser` 使用本机 Chrome 检查桌面/移动页面渲染、小酷浮层和对话入口、服务详情跳转、小纸条提交、普通用户订单隔离以及管理员搜索。

生产栈联调验证：

```bash
npm run stack:up
npm run verify:production-stack
npm run stack:down
```

`verify:production-stack` 会验证 Postgres 连接、Alembic migration、pgvector extension、核心表、生产模式 API 初始化，以及 Redis ping / 写入 / 读取。该命令默认只允许连接本地 Postgres；如需对非本地数据库执行，必须显式设置 `ALLOW_NONLOCAL_PRODUCTION_VERIFY=true`。

数据库迁移验证：

```bash
DATABASE_URL=sqlite:////tmp/kuli_migration_check.sqlite PYTHONPATH=apps/api uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head
DATABASE_URL=postgresql+psycopg://kuli:kuli@localhost:5432/kuli PYTHONPATH=apps/api uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head --sql
```
