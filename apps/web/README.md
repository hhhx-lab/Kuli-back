# Kuli Web

Nuxt / Vue 3 前端应用，负责官网、服务详情、文档中心、产品页、登录注册、用户订单工作台、管理员后台和小酷 3D 小猫助手。

## 技术栈

- Vue 3 + Nuxt + TypeScript
- Pinia
- Three.js
- Nuxt server routes for `sitemap.xml` and `robots.txt`
- FastAPI OpenAPI 生成类型：`app/types/api-contract.ts`

## 启动

```bash
npm install
cp apps/web/.env.example apps/web/.env
npm run dev --workspace @kuli/web
```

前端默认监听 `http://127.0.0.1:3000`，通过 `NUXT_PUBLIC_API_BASE_URL` 访问 API。

## 常用命令

```bash
npm run typecheck --workspace @kuli/web
npm run build --workspace @kuli/web
HOST=127.0.0.1 PORT=3000 NUXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 NUXT_PUBLIC_SITE_URL=http://127.0.0.1:3000 node apps/web/.output/server/index.mjs
```

## 关键目录

- `app/pages/`：Nuxt 页面路由。
- `app/layouts/default.vue`：全站导航、账号菜单和页脚。
- `app/composables/useApi.ts`：API client。
- `app/composables/useKuliSeo.ts`：公开页 SEO、Open Graph 和 JSON-LD。
- `app/components/xiaoku/XiaokuAvatar.vue`：小酷 3D 小猫助手。
- `app/assets/css/main.css`：全局样式和响应式布局。
- `server/routes/`：`sitemap.xml`、`robots.txt`。
- `public/`：公开静态资源和分享图。

## 公开与权限边界

- 游客可访问 `/`、`/services`、`/services/:slug`、`/help`、`/help/:slug`、`/products`、`/login` 和法律页面。
- `/note`、`/orders`、`/me`、`/settings`、`/referrals`、`/notifications` 需要登录。
- `/admin` 和 `/admin/orders/:orderNumber` 需要管理员账号。
- 登录页支持邮箱密码登录、注册、忘记密码入口和邮件验证 token 链接。
