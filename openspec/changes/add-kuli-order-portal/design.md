## Context

The repository is a greenfield project for "酷里 Kuli". It currently has a MyPlan document, project background copy, four JPG UI references, and three "酷里小窗口" HTML prototypes with shared CSS/JS. OpenSpec is initialized, but there are no baseline specs and no active changes other than this one. There is no existing application stack, package manifest, source directory, database schema, or production data.

The target is a separated frontend/backend implementation: a public website and account/order UI in one frontend app, plus an API backend with authentication, authorization, persistence, and order management. The first version should be useful locally without external services.

## Goals / Non-Goals

**Goals:**
- Build a runnable frontend web app for the Kuli homepage, service explanation, note submission, user order progress, admin order management, and reserved project portal.
- Build a backend API for email/password login, role-based access, public inquiries, account-owned orders, admin order updates, and durable local persistence.
- Keep admin and normal-account permissions distinct across routes, API authorization, and response fields.
- Provide seed data so the app can be verified immediately after install.
- Provide automated backend tests and build scripts for both apps.

**Non-Goals:**
- No real payment processing, invoice flow, long-term maintenance workflow, or automated service fulfillment.
- No third-party OAuth, SMS login, magic-link login, or multi-level RBAC beyond `admin` and `user`.
- No real subproject management or filesystem scanning outside the repository.
- No exact pixel-copy requirement for the HTML/JPG prototypes.

## Decisions

### Decision 1: npm workspace with separated frontend and backend

Use a root npm workspace with `frontend/` and `backend/`. The frontend will be a Vite React TypeScript app. The backend will be an Express TypeScript API service. Root scripts will orchestrate install, dev, test, and build without coupling frontend and backend deployment.

Alternatives considered:
- Next.js full-stack app: faster routing, but it weakens the explicit frontend/backend separation requested by the user.
- Static HTML only: close to the prototypes, but cannot satisfy account, admin, order API, or persistence requirements.

### Decision 2: Local SQLite persistence behind a small repository layer

Use SQLite via a backend database module for local durable data. The schema will include users, orders, order messages, and optional attachment metadata. The backend will seed an admin account and demo user account in development/test environments.

Alternatives considered:
- JSON files: simpler but too fragile for concurrent API writes and relational authorization checks.
- External hosted database: more production-like, but unnecessary for a local first version and adds setup friction.

### Decision 3: Token-based API auth with server-side role checks

Use email/password login. Passwords are hashed with a salt and a slow key-derivation function, never stored as plaintext. Successful login returns an API token containing user id and role. Every protected route loads the authenticated user and applies role/ownership checks on the server.

Alternatives considered:
- Cookie sessions: good for same-origin apps, but frontend/backend separation and local ports make bearer tokens easier for the first version.
- Order-number/contact lookup: previously considered, but replaced by the user's explicit email/password account requirement.

### Decision 4: Public inquiries and account orders are related but distinct

Visitors can submit a "小纸条" as a public inquiry that admins can process. Logged-in normal accounts can create account-owned orders and later view their own progress. Public inquiries do not grant order-detail access until an admin links or recreates them under an account in a later change.

Alternatives considered:
- Force login before submitting any note: simpler auth, but contradicts the website funnel where visitors can first drop a small note.
- Automatically create accounts from public notes: convenient, but requires password setup and email verification that are out of scope.

### Decision 5: Frontend uses prototype structure with production routing

The frontend will convert the prototype's "首页 / 能做什么 / 写小纸条" into React routes and add `/orders`, `/admin`, `/login`, and `/projects`. CSS should preserve the dark Kuli visual direction, note-card CTA, window/chat feel, responsive mobile CTA, and FAQ filtering while fixing missing resource paths.

Alternatives considered:
- Embed the supplied HTML directly: fast but hard to integrate with auth state and API responses.
- Rebuild with a component library: more uniform but risks losing the Kuli-specific personality.

## Risks / Trade-offs

- Native SQLite dependency may fail on some local Node environments → keep database access isolated and document Node/npm versions; tests will catch startup failure.
- Token auth in local storage is simple but less hardened than production cookie/session hardening → acceptable for local first version; server-side role checks remain mandatory.
- Public inquiry versus account order distinction can confuse users → UI copy must explain that logging in is required to track progress.
- Generated `.codex/` files are created by OpenSpec init → keep them uncommitted per repository convention.
- The frontend prototypes reference missing `assets/...` paths → production implementation must use self-contained React/CSS assets and no broken references.

## Migration Plan

This is a greenfield build. No existing production schema or data is migrated. The backend will create its local SQLite schema on startup and seed development accounts when missing.

Rollback is to stop the API, delete generated runtime data, and remove the new frontend/backend source files. The reserved project portal must never read `/Users/hwaigc/太空垃圾站` or other workspace directories in this change.

## Open Questions

- Exact production deployment target is not chosen yet; local development and build scripts are required for this change.
- Admin account provisioning is local-seed based for this version; production provisioning can be refined later.
