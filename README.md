# 酷里 Kuli 官网与订单系统

酷里是一个面向公开发布的服务官网与订单管理系统。当前版本覆盖官网服务展示、服务详情页、写小纸条提交需求、邮箱密码登录、普通账号订单工作台，以及管理员订单管理台。

系统的核心目标是把“用户说不清楚的需求”先收进来，再通过服务分类、需求润色、订单进度、报价、付款记录、交付物和验收流程，形成一个可追踪的服务闭环。

## 当前功能

- 官网首页、服务列表、服务详情页和交易规则说明。
- `/services/:slug` 服务详情路由，覆盖 AI 工具、文档处理、小工具开发、部署配置、API/token 和“不知道怎么分”。
- “写小纸条”支持游客提交，也支持登录后创建归属到账号的订单。
- 邮箱密码登录与注册，区分管理员账号和一般账号。
- 普通账号只能查看自己的订单、进度、沟通、附件、报价、付款和交付物。
- 管理员可查看全部订单，并维护状态、优先级、报价、成本、利润、公开备注、内部备注、付款记录和交付物。
- 后端提供规则型需求润色与管理员 agent brief，帮助管理员快速判断需求方向和下一步问题。

## 目录结构

```text
.
├── backend/                 # Express + TypeScript API
│   ├── src/app.ts           # API 路由、鉴权、错误处理
│   ├── src/database.ts      # SQLite schema、seed、订单数据访问
│   ├── src/catalog.ts       # 服务目录与详情内容
│   ├── src/agent.ts         # 规则型需求润色和订单 brief
│   └── .env.example         # 后端环境变量示例
├── frontend/                # Vite + React 前端
│   ├── src/App.tsx          # 页面路由与主要界面
│   ├── src/api.ts           # API client
│   ├── src/auth.tsx         # 登录态与 token 管理
│   └── .env.example         # 前端环境变量示例
├── docs/                    # 项目文档
├── openspec/                # OpenSpec proposal/design/specs/tasks
├── plan/                    # 前置 plan 文档
└── package.json             # npm workspace 脚本
```

## 环境准备

需要本机已安装 Node.js 和 npm。本仓库使用 npm workspaces 管理 `backend` 与 `frontend` 两个包，不需要 Python 环境参与项目运行。

第一次启动前安装依赖并准备环境变量：

```bash
npm install
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

本地默认端口：

- 前端：`http://localhost:5173`
- 后端 API：`http://localhost:4000`
- 健康检查：`http://localhost:4000/health`

## 启动方式

同时启动前后端：

```bash
npm run dev
```

分别启动：

```bash
npm run dev --workspace backend
npm run dev --workspace frontend
```

生产构建并运行后端产物：

```bash
npm run build
npm run start --workspace backend
```

前端构建产物位于 `frontend/dist/`，可按部署平台要求托管静态文件。

## Demo 账号

本地 SQLite 初始化时会写入以下种子账号：

| 角色 | 邮箱 | 密码 |
| --- | --- | --- |
| 管理员 | `admin@kuli.local` | `KuliAdmin123!` |
| 一般账号 | `demo@kuli.local` | `KuliUser123!` |
| 一般账号 | `other@kuli.local` | `KuliOther123!` |

`demo` 与 `other` 用于验证普通账号只能看到自己的订单；管理员可以看到全部订单和内部字段。

## 环境变量

后端变量来自 `backend/.env.example`：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `PORT` | `4000` | 后端 API 端口 |
| `CORS_ORIGIN` | `http://localhost:5173` | 允许访问 API 的前端地址 |
| `JWT_SECRET` | `replace-with-a-long-random-secret` | token 签名密钥，生产环境必须替换为足够长的随机字符串 |
| `DATABASE_PATH` | `data/kuli.sqlite` | 当前代码使用的 SQLite 数据库路径 |
| `LOCAL_OBJECT_STORE_DIR` | `data/object-store` | 当前附件本地对象存储 fallback 目录 |

前端变量来自 `frontend/.env.example`：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:4000` | 前端请求后端 API 的基础地址 |

`DATABASE_URL`、`OBJECT_STORAGE_*` 已在示例文件中预留为正式发布目标，但当前代码还没有实现 Postgres 或 S3/R2/OSS adapter。现阶段生产化前需要补齐对应数据与对象存储接入。

## 常用命令

```bash
npm run typecheck
npm run test
npm run build
```

如需验证 OpenSpec 变更：

```bash
openspec validate add-kuli-order-portal --strict
```

## 数据与附件

- 本地数据库默认写入 `backend/data/kuli.sqlite`。
- 本地附件 fallback 默认写入 `backend/data/object-store/`。
- 数据库中保存附件 metadata、权限归属、文件状态和 storage key。
- `.env`、`backend/data/`、`dist/`、`node_modules/`、`.codex/` 等本地或生成文件已加入 `.gitignore`，不要提交到仓库。

## 更多文档

- [技术架构](docs/TECHNICAL_ARCHITECTURE.md)
- [2.0 订单自动化与小酷 agent 设计](docs/superpowers/specs/2026-05-29-kuli-v2-order-automation-xiaoku-agent-design.md)
