## Why

酷里目前只有需求文档、前端参考图和静态原型，还没有可运行的官网、账号系统、订单系统或后端服务。需要把“酷里小窗口”落成前后端分离的第一版产品，让访客能了解服务和提交需求，让一般账号能查看自己的订单进度，让管理员能管理全部订单与内部经营字段。

## What Changes

- 新增前后端分离工程：独立前端 Web 应用和后端 API 服务，统一根目录脚本用于开发、测试和构建。
- 新增酷里官网前台：首页、服务说明、写小纸条、预留子项目入口，并复用现有“酷里小窗口”原型的页面结构、文案风格和交互。
- 新增邮箱加密码登录能力，账号分为管理员账号和一般账号。
- 新增订单提交能力：访客可提交小纸条形成待处理询单，登录一般账号可创建归属于自己的订单。
- 新增一般账号订单视图：一般账号只能查看自己的订单进度、公开报价、沟通记录和附件状态。
- 新增管理员订单后台：管理员可查看全部订单，维护客户信息、联系方式、需求、成本、利润、开价、进度、优先级和内部备注。
- 新增订单状态与进度模型，支持已提交、需求确认中、处理中/试验初版中、待验收、已完成等阶段。
- 新增基础持久化和种子数据，支持本地开发环境可直接试用。
- 新增资源与路由校验，确保前端没有断链资源、缺失页面或无法访问的核心入口。

## Capabilities

### New Capabilities
- `website`: 酷里官网前台页面、服务说明、FAQ、结算规则、移动端 CTA 和预留子项目入口。
- `order-submission`: 写小纸条与订单创建流程，包括必填校验、字数反馈、提交状态和订单号生成。
- `auth-and-roles`: 邮箱密码登录、一般账号/管理员账号角色区分、会话与接口鉴权。
- `customer-order-view`: 一般账号查看自己订单进度、公开报价、沟通记录和附件状态。
- `order-management`: 管理员查看与维护全部订单、内部经营字段、状态、优先级和备注。
- `reserved-project-portal`: 子项目/子产品管理的前端预留入口，占位但不读取本机其他项目数据。

### Modified Capabilities
- None. The OpenSpec specs baseline is currently empty.

## Impact

- Adds root workspace scripts and dependency manifests.
- Adds a backend API service with authentication, authorization, order persistence, validation and tests.
- Adds a frontend Web app with routed pages, auth state, API integration, role-based views and responsive styling.
- Adds local development configuration and ignores generated runtime data and `.codex/` from commits.
- Adds OpenSpec specs and implementation tasks for a new greenfield system; no existing production data or application code is migrated.
