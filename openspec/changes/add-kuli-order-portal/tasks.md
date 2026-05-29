## 1. Project Setup

- [x] 1.1 Create root npm workspace scripts and repository ignores for generated runtime files.
- [x] 1.2 Create separated `backend/` and `frontend/` package manifests, TypeScript configs, and development scripts.
- [x] 1.3 Add shared environment examples for backend API port, frontend API base URL, JWT secret, and database path.

## 2. Backend API

- [x] 2.1 Add backend tests for email/password login, generic failed-login errors, and password hash storage.
- [x] 2.2 Implement backend app factory, config loader, error handling, and health endpoint.
- [x] 2.3 Implement SQLite schema, seed data, password hashing, and token helpers.
- [x] 2.4 Add backend tests proving admins can see all orders and normal users only see their own orders.
- [x] 2.5 Implement auth routes, authenticated user loading, role guards, and order ownership guards.
- [x] 2.6 Add backend tests for public inquiry creation, owned order creation, admin order updates, and hidden customer fields.
- [x] 2.7 Implement public inquiry, user order, admin order, message, and status update API routes.

## 3. Frontend Web App

- [x] 3.1 Create Vite React app shell, API client, auth state, protected route helpers, and shared layout.
- [x] 3.2 Implement Kuli homepage, services/FAQ page, write-note page, login/register page, orders page, admin dashboard, and reserved project portal.
- [x] 3.3 Wire write-note submission to public inquiry or owned order APIs depending on login state.
- [x] 3.4 Wire normal-account order progress view to backend customer-safe order responses.
- [x] 3.5 Wire admin dashboard to backend all-order list, detail editing, status, priority, quoted price, cost, profit, public notes, and internal notes.
- [x] 3.6 Apply responsive Kuli visual styling from the supplied prototype while removing broken asset references.

## 4. Verification

- [x] 4.1 Run backend test suite and fix failures.
- [x] 4.2 Run frontend and backend typecheck/build scripts and fix failures.
- [x] 4.3 Start local dev servers and verify core flows in browser: homepage, services FAQ filter, note submit, login, normal orders, admin orders, reserved portal.
- [x] 4.4 Re-run `openspec validate add-kuli-order-portal --strict` and update task checkboxes for completed work.
