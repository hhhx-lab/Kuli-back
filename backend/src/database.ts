import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import Database from "better-sqlite3";
import { serviceCatalog, type ServiceCatalogItem } from "./catalog.js";
import { hashPassword } from "./security.js";

export type Role = "admin" | "user";

export type UserRow = {
  id: string;
  email: string;
  password_hash: string;
  role: Role;
  display_name: string;
  created_at: string;
};

export type OrderRow = {
  id: string;
  order_number: string;
  owner_user_id: string | null;
  owner_email: string | null;
  customer_name: string;
  contact: string;
  service_slug: string;
  category: string;
  title: string;
  demand: string;
  original_demand: string;
  urgency: string;
  budget: string;
  remote_help: string;
  quoted_price: number | null;
  cost: number | null;
  profit: number | null;
  status: string;
  priority: string;
  public_notes: string;
  internal_notes: string;
  created_at: string;
  updated_at: string;
};

export type OrderEventRow = {
  id: string;
  order_number: string;
  status: string;
  note: string;
  created_by: string | null;
  created_by_email: string | null;
  created_at: string;
};

export type OrderMessageRow = {
  id: string;
  order_number: string;
  author_user_id: string;
  author_email: string | null;
  author_role: Role | null;
  body: string;
  visibility: "public" | "internal";
  created_at: string;
};

export type OrderAttachmentRow = {
  id: string;
  order_number: string;
  uploader_user_id: string | null;
  uploader_email: string | null;
  file_name: string;
  file_size: number;
  content_type: string;
  storage_key: string;
  visibility: "public" | "internal";
  created_at: string;
};

export type QuoteRow = {
  id: string;
  order_number: string;
  amount: number;
  kind: string;
  note: string;
  status: string;
  created_by: string;
  created_by_email: string | null;
  created_at: string;
};

export type PaymentRow = {
  id: string;
  order_number: string;
  amount: number;
  kind: string;
  method: string;
  status: string;
  note: string;
  created_by: string;
  created_by_email: string | null;
  created_at: string;
};

export type DeliverableRow = {
  id: string;
  order_number: string;
  title: string;
  description: string;
  storage_key: string;
  created_by: string;
  created_by_email: string | null;
  created_at: string;
};

export type CreateOrderInput = {
  ownerUserId: string | null;
  serviceSlug?: string;
  customerName?: string;
  contact: string;
  category: string;
  title?: string;
  demand: string;
  originalDemand?: string;
  urgency?: string;
  budget?: string;
  remoteHelp?: string;
};

export function openDatabase(databasePath: string) {
  if (databasePath !== ":memory:") {
    fs.mkdirSync(path.dirname(databasePath), { recursive: true });
  }
  const db = new Database(databasePath);
  db.pragma("foreign_keys = ON");
  migrate(db);
  seed(db);
  return db;
}

export function createMemoryDatabase() {
  const db = new Database(":memory:");
  db.pragma("foreign_keys = ON");
  migrate(db);
  seed(db);
  return db;
}

export function migrate(db: Database.Database) {
  db.exec(`
    create table if not exists users (
      id text primary key,
      email text not null unique,
      password_hash text not null,
      role text not null check (role in ('admin', 'user')),
      display_name text not null,
      created_at text not null
    );

    create table if not exists service_categories (
      slug text primary key,
      title text not null,
      tag text not null,
      summary text not null,
      details_json text not null,
      created_at text not null,
      updated_at text not null
    );

    create table if not exists orders (
      id text primary key,
      order_number text not null unique,
      owner_user_id text references users(id) on delete set null,
      customer_name text not null,
      contact text not null,
      service_slug text not null default 'not-sure',
      category text not null,
      title text not null,
      demand text not null,
      original_demand text not null default '',
      urgency text not null,
      budget text not null,
      remote_help text not null,
      quoted_price real,
      cost real,
      profit real,
      status text not null,
      priority text not null,
      public_notes text not null,
      internal_notes text not null,
      created_at text not null,
      updated_at text not null
    );

    create index if not exists idx_orders_owner on orders(owner_user_id);
    create index if not exists idx_orders_status on orders(status);

    create table if not exists order_events (
      id text primary key,
      order_number text not null references orders(order_number) on delete cascade,
      status text not null,
      note text not null,
      created_by text references users(id) on delete set null,
      created_at text not null
    );

    create table if not exists order_messages (
      id text primary key,
      order_number text not null references orders(order_number) on delete cascade,
      author_user_id text not null references users(id) on delete cascade,
      body text not null,
      visibility text not null check (visibility in ('public', 'internal')),
      created_at text not null
    );

    create table if not exists order_attachments (
      id text primary key,
      order_number text not null references orders(order_number) on delete cascade,
      uploader_user_id text references users(id) on delete set null,
      file_name text not null,
      file_size integer not null,
      content_type text not null,
      storage_key text not null,
      visibility text not null check (visibility in ('public', 'internal')),
      created_at text not null
    );

    create table if not exists quotes (
      id text primary key,
      order_number text not null references orders(order_number) on delete cascade,
      amount real not null,
      kind text not null,
      note text not null,
      status text not null,
      created_by text not null references users(id) on delete cascade,
      created_at text not null
    );

    create table if not exists payment_records (
      id text primary key,
      order_number text not null references orders(order_number) on delete cascade,
      amount real not null,
      kind text not null,
      method text not null,
      status text not null,
      note text not null,
      created_by text not null references users(id) on delete cascade,
      created_at text not null
    );

    create table if not exists deliverables (
      id text primary key,
      order_number text not null references orders(order_number) on delete cascade,
      title text not null,
      description text not null,
      storage_key text not null,
      created_by text not null references users(id) on delete cascade,
      created_at text not null
    );

    create table if not exists admin_audit_logs (
      id text primary key,
      order_number text references orders(order_number) on delete cascade,
      actor_user_id text not null references users(id) on delete cascade,
      action text not null,
      details text not null,
      created_at text not null
    );
  `);
  ensureColumn(db, "orders", "service_slug", "text not null default 'not-sure'");
  ensureColumn(db, "orders", "original_demand", "text not null default ''");
}

export function seed(db: Database.Database) {
  const insertUser = db.prepare(`
    insert or ignore into users (id, email, password_hash, role, display_name, created_at)
    values (@id, @email, @password_hash, @role, @display_name, @created_at)
  `);
  const now = new Date().toISOString();
  insertUser.run({
    id: "user_admin",
    email: "admin@kuli.local",
    password_hash: hashPassword("KuliAdmin123!"),
    role: "admin",
    display_name: "酷里管理员",
    created_at: now
  });
  insertUser.run({
    id: "user_demo",
    email: "demo@kuli.local",
    password_hash: hashPassword("KuliUser123!"),
    role: "user",
    display_name: "Demo 用户",
    created_at: now
  });
  insertUser.run({
    id: "user_other",
    email: "other@kuli.local",
    password_hash: hashPassword("KuliOther123!"),
    role: "user",
    display_name: "Other 用户",
    created_at: now
  });

  const insertService = db.prepare(`
    insert or replace into service_categories (slug, title, tag, summary, details_json, created_at, updated_at)
    values (@slug, @title, @tag, @summary, @details_json, @created_at, @updated_at)
  `);
  for (const service of serviceCatalog) {
    insertService.run({
      slug: service.slug,
      title: service.title,
      tag: service.tag,
      summary: service.summary,
      details_json: JSON.stringify(service),
      created_at: now,
      updated_at: now
    });
  }

  const existingOrders = db.prepare("select count(*) as count from orders").get() as { count: number };
  if (existingOrders.count > 0) return;

  insertOrder(db, {
    orderNumber: "KULI-DEMO-001",
    ownerUserId: "user_demo",
    customerName: "Demo 用户",
    contact: "demo@kuli.local",
    serviceSlug: "tool-development",
    category: "小工具开发",
    title: "课程项目网页 demo",
    demand: "想做一个课程项目网页 demo，有设计稿，希望先出一个能演示的版本。",
    originalDemand: "想做一个课程项目网页 demo，有设计稿，希望先出一个能演示的版本。",
    urgency: "3-5 天",
    budget: "300-1000",
    remoteHelp: "可以远程",
    quotedPrice: 180,
    cost: 60,
    profit: 120,
    status: "clarifying",
    priority: "normal",
    publicNotes: "酷里正在确认需求范围。",
    internalNotes: "Demo 种子订单，用于验证一般账号权限。"
  });
  insertOrder(db, {
    orderNumber: "KULI-OTHER-001",
    ownerUserId: "user_other",
    customerName: "Other 用户",
    contact: "other@kuli.local",
    serviceSlug: "document-processing",
    category: "文档处理",
    title: "PDF 翻译并保留格式",
    demand: "PDF 需要翻译，还要尽量保留排版。",
    originalDemand: "PDF 需要翻译，还要尽量保留排版。",
    urgency: "1-2 天",
    budget: "100-300",
    remoteHelp: "不需要",
    quotedPrice: 120,
    cost: 40,
    profit: 80,
    status: "submitted",
    priority: "normal",
    publicNotes: "已收到材料。",
    internalNotes: "用于验证越权访问被拒绝。"
  });
}

export function getUserByEmail(db: Database.Database, email: string) {
  return db.prepare("select * from users where lower(email) = lower(?)").get(email) as UserRow | undefined;
}

export function getUserById(db: Database.Database, id: string) {
  return db.prepare("select * from users where id = ?").get(id) as UserRow | undefined;
}

export function createUser(db: Database.Database, input: { email: string; password: string; displayName: string }) {
  const user: UserRow = {
    id: randomUUID(),
    email: input.email.toLowerCase(),
    password_hash: hashPassword(input.password),
    role: "user",
    display_name: input.displayName,
    created_at: new Date().toISOString()
  };
  db.prepare(`
    insert into users (id, email, password_hash, role, display_name, created_at)
    values (@id, @email, @password_hash, @role, @display_name, @created_at)
  `).run(user);
  return user;
}

export function listAdminOrders(db: Database.Database) {
  return db.prepare(orderSelectSql("order by o.updated_at desc")).all() as OrderRow[];
}

export function listUserOrders(db: Database.Database, userId: string) {
  return db.prepare(orderSelectSql("where o.owner_user_id = ? order by o.updated_at desc")).all(userId) as OrderRow[];
}

export function findAdminOrder(db: Database.Database, orderNumber: string) {
  return db.prepare(orderSelectSql("where o.order_number = ?")).get(orderNumber) as OrderRow | undefined;
}

export function findUserOrder(db: Database.Database, userId: string, orderNumber: string) {
  return db.prepare(orderSelectSql("where o.owner_user_id = ? and o.order_number = ?")).get(userId, orderNumber) as
    | OrderRow
    | undefined;
}

export function createOrder(db: Database.Database, input: CreateOrderInput) {
  const orderNumber = nextOrderNumber(db);
  const order = insertOrder(db, {
    orderNumber,
    ownerUserId: input.ownerUserId,
    serviceSlug: input.serviceSlug ?? serviceSlugFromCategory(input.category),
    customerName: input.customerName ?? "未命名客户",
    contact: input.contact,
    category: input.category,
    title: input.title ?? summarizeDemand(input.demand),
    demand: input.demand,
    originalDemand: input.originalDemand ?? input.demand,
    urgency: input.urgency ?? "先聊聊",
    budget: input.budget ?? "先报价看看",
    remoteHelp: input.remoteHelp ?? "看情况",
    quotedPrice: null,
    cost: null,
    profit: null,
    status: "submitted",
    priority: "normal",
    publicNotes: "小纸条已收到，酷里会先判断是否适合做。",
    internalNotes: input.ownerUserId ? "登录账号提交订单。" : "游客提交小纸条。"
  });
  addOrderEvent(db, {
    orderNumber,
    status: "submitted",
    note: "订单已提交",
    createdBy: input.ownerUserId
  });
  return order;
}

export function updateAdminOrder(
  db: Database.Database,
  orderNumber: string,
  patch: Partial<Pick<OrderRow, "status" | "priority" | "quoted_price" | "cost" | "profit" | "public_notes" | "internal_notes">>
) {
  const existing = findAdminOrder(db, orderNumber);
  if (!existing) return undefined;

  const updated = {
    status: patch.status ?? existing.status,
    priority: patch.priority ?? existing.priority,
    quoted_price: patch.quoted_price ?? existing.quoted_price,
    cost: patch.cost ?? existing.cost,
    profit: patch.profit ?? existing.profit,
    public_notes: patch.public_notes ?? existing.public_notes,
    internal_notes: patch.internal_notes ?? existing.internal_notes,
    updated_at: new Date().toISOString(),
    order_number: orderNumber
  };
  db.prepare(`
    update orders
    set status = @status,
        priority = @priority,
        quoted_price = @quoted_price,
        cost = @cost,
        profit = @profit,
        public_notes = @public_notes,
        internal_notes = @internal_notes,
        updated_at = @updated_at
    where order_number = @order_number
  `).run(updated);

  return findAdminOrder(db, orderNumber);
}

export function listServices() {
  return serviceCatalog;
}

export function getService(slug: string) {
  return serviceCatalog.find((service) => service.slug === slug);
}

export function addOrderMessage(
  db: Database.Database,
  input: { orderNumber: string; authorUserId: string; body: string; visibility?: "public" | "internal" }
) {
  const row = {
    id: randomUUID(),
    order_number: input.orderNumber,
    author_user_id: input.authorUserId,
    body: input.body,
    visibility: input.visibility ?? "public",
    created_at: new Date().toISOString()
  };
  db.prepare(`
    insert into order_messages (id, order_number, author_user_id, body, visibility, created_at)
    values (@id, @order_number, @author_user_id, @body, @visibility, @created_at)
  `).run(row);
  return listOrderMessages(db, input.orderNumber, input.visibility === "internal");
}

export function addOrderAttachment(
  db: Database.Database,
  input: {
    orderNumber: string;
    uploaderUserId: string | null;
    fileName: string;
    fileSize: number;
    contentType: string;
    storageKey?: string;
    visibility?: "public" | "internal";
  }
) {
  const row = {
    id: randomUUID(),
    order_number: input.orderNumber,
    uploader_user_id: input.uploaderUserId,
    file_name: input.fileName,
    file_size: input.fileSize,
    content_type: input.contentType,
    storage_key: input.storageKey ?? `local-object-store/${input.orderNumber}/${Date.now()}-${input.fileName}`,
    visibility: input.visibility ?? "public",
    created_at: new Date().toISOString()
  };
  db.prepare(`
    insert into order_attachments (id, order_number, uploader_user_id, file_name, file_size, content_type, storage_key, visibility, created_at)
    values (@id, @order_number, @uploader_user_id, @file_name, @file_size, @content_type, @storage_key, @visibility, @created_at)
  `).run(row);
  return listOrderAttachments(db, input.orderNumber, input.visibility === "internal");
}

export function addQuote(
  db: Database.Database,
  input: { orderNumber: string; amount: number; kind: string; note: string; createdBy: string }
) {
  const row = {
    id: randomUUID(),
    order_number: input.orderNumber,
    amount: input.amount,
    kind: input.kind,
    note: input.note,
    status: "sent",
    created_by: input.createdBy,
    created_at: new Date().toISOString()
  };
  db.prepare(`
    insert into quotes (id, order_number, amount, kind, note, status, created_by, created_at)
    values (@id, @order_number, @amount, @kind, @note, @status, @created_by, @created_at)
  `).run(row);
  return listQuotes(db, input.orderNumber);
}

export function addPaymentRecord(
  db: Database.Database,
  input: { orderNumber: string; amount: number; kind: string; method: string; status: string; note: string; createdBy: string }
) {
  const row = {
    id: randomUUID(),
    order_number: input.orderNumber,
    amount: input.amount,
    kind: input.kind,
    method: input.method,
    status: input.status,
    note: input.note,
    created_by: input.createdBy,
    created_at: new Date().toISOString()
  };
  db.prepare(`
    insert into payment_records (id, order_number, amount, kind, method, status, note, created_by, created_at)
    values (@id, @order_number, @amount, @kind, @method, @status, @note, @created_by, @created_at)
  `).run(row);
  return listPayments(db, input.orderNumber);
}

export function addDeliverable(
  db: Database.Database,
  input: { orderNumber: string; title: string; description: string; storageKey: string; createdBy: string }
) {
  const row = {
    id: randomUUID(),
    order_number: input.orderNumber,
    title: input.title,
    description: input.description,
    storage_key: input.storageKey,
    created_by: input.createdBy,
    created_at: new Date().toISOString()
  };
  db.prepare(`
    insert into deliverables (id, order_number, title, description, storage_key, created_by, created_at)
    values (@id, @order_number, @title, @description, @storage_key, @created_by, @created_at)
  `).run(row);
  return listDeliverables(db, input.orderNumber);
}

export function addOrderEvent(db: Database.Database, input: { orderNumber: string; status: string; note: string; createdBy: string | null }) {
  const row = {
    id: randomUUID(),
    order_number: input.orderNumber,
    status: input.status,
    note: input.note,
    created_by: input.createdBy,
    created_at: new Date().toISOString()
  };
  db.prepare(`
    insert into order_events (id, order_number, status, note, created_by, created_at)
    values (@id, @order_number, @status, @note, @created_by, @created_at)
  `).run(row);
}

export function getOrderCollections(db: Database.Database, orderNumber: string, includeInternal = false) {
  return {
    events: listOrderEvents(db, orderNumber),
    messages: listOrderMessages(db, orderNumber, includeInternal),
    attachments: listOrderAttachments(db, orderNumber, includeInternal),
    quotes: listQuotes(db, orderNumber),
    payments: listPayments(db, orderNumber),
    deliverables: listDeliverables(db, orderNumber)
  };
}

function listOrderEvents(db: Database.Database, orderNumber: string) {
  return db
    .prepare(
      `select e.*, u.email as created_by_email
       from order_events e
       left join users u on u.id = e.created_by
       where e.order_number = ?
       order by e.created_at asc`
    )
    .all(orderNumber) as OrderEventRow[];
}

function listOrderMessages(db: Database.Database, orderNumber: string, includeInternal: boolean) {
  return db
    .prepare(
      `select m.*, u.email as author_email, u.role as author_role
       from order_messages m
       left join users u on u.id = m.author_user_id
       where m.order_number = ?
       ${includeInternal ? "" : "and m.visibility = 'public'"}
       order by m.created_at asc`
    )
    .all(orderNumber) as OrderMessageRow[];
}

function listOrderAttachments(db: Database.Database, orderNumber: string, includeInternal: boolean) {
  return db
    .prepare(
      `select a.*, u.email as uploader_email
       from order_attachments a
       left join users u on u.id = a.uploader_user_id
       where a.order_number = ?
       ${includeInternal ? "" : "and a.visibility = 'public'"}
       order by a.created_at asc`
    )
    .all(orderNumber) as OrderAttachmentRow[];
}

function listQuotes(db: Database.Database, orderNumber: string) {
  return db
    .prepare(
      `select q.*, u.email as created_by_email
       from quotes q
       left join users u on u.id = q.created_by
       where q.order_number = ?
       order by q.created_at asc`
    )
    .all(orderNumber) as QuoteRow[];
}

function listPayments(db: Database.Database, orderNumber: string) {
  return db
    .prepare(
      `select p.*, u.email as created_by_email
       from payment_records p
       left join users u on u.id = p.created_by
       where p.order_number = ?
       order by p.created_at asc`
    )
    .all(orderNumber) as PaymentRow[];
}

function listDeliverables(db: Database.Database, orderNumber: string) {
  return db
    .prepare(
      `select d.*, u.email as created_by_email
       from deliverables d
       left join users u on u.id = d.created_by
       where d.order_number = ?
       order by d.created_at asc`
    )
    .all(orderNumber) as DeliverableRow[];
}

function insertOrder(
  db: Database.Database,
  input: {
    orderNumber: string;
    ownerUserId: string | null;
    serviceSlug: string;
    customerName: string;
    contact: string;
    category: string;
    title: string;
    demand: string;
    originalDemand: string;
    urgency: string;
    budget: string;
    remoteHelp: string;
    quotedPrice: number | null;
    cost: number | null;
    profit: number | null;
    status: string;
    priority: string;
    publicNotes: string;
    internalNotes: string;
  }
) {
  const now = new Date().toISOString();
  const row = {
    id: randomUUID(),
    order_number: input.orderNumber,
    owner_user_id: input.ownerUserId,
    customer_name: input.customerName,
    contact: input.contact,
    service_slug: input.serviceSlug,
    category: input.category,
    title: input.title,
    demand: input.demand,
    original_demand: input.originalDemand,
    urgency: input.urgency,
    budget: input.budget,
    remote_help: input.remoteHelp,
    quoted_price: input.quotedPrice,
    cost: input.cost,
    profit: input.profit,
    status: input.status,
    priority: input.priority,
    public_notes: input.publicNotes,
    internal_notes: input.internalNotes,
    created_at: now,
    updated_at: now
  };
  db.prepare(`
    insert into orders (
      id, order_number, owner_user_id, customer_name, contact, service_slug, category, title, demand, original_demand,
      urgency, budget, remote_help, quoted_price, cost, profit, status, priority,
      public_notes, internal_notes, created_at, updated_at
    )
    values (
      @id, @order_number, @owner_user_id, @customer_name, @contact, @service_slug, @category, @title, @demand, @original_demand,
      @urgency, @budget, @remote_help, @quoted_price, @cost, @profit, @status, @priority,
      @public_notes, @internal_notes, @created_at, @updated_at
    )
  `).run(row);
  return findAdminOrder(db, input.orderNumber)!;
}

function orderSelectSql(tail: string) {
  return `
    select
      o.*,
      u.email as owner_email
    from orders o
    left join users u on u.id = o.owner_user_id
    ${tail}
  `;
}

function nextOrderNumber(db: Database.Database) {
  const date = new Date();
  const stamp = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, "0")}${String(date.getDate()).padStart(2, "0")}`;
  const count = db.prepare("select count(*) as count from orders where order_number like ?").get(`KULI-${stamp}-%`) as {
    count: number;
  };
  return `KULI-${stamp}-${String(count.count + 1).padStart(3, "0")}`;
}

function summarizeDemand(demand: string) {
  return demand.trim().replace(/\s+/g, " ").slice(0, 36) || "新的小纸条";
}

function ensureColumn(db: Database.Database, table: string, column: string, definition: string) {
  const rows = db.prepare(`pragma table_info(${table})`).all() as Array<{ name: string }>;
  if (!rows.some((row) => row.name === column)) {
    db.exec(`alter table ${table} add column ${column} ${definition}`);
  }
}

function serviceSlugFromCategory(category: string) {
  const normalized = category.toLowerCase();
  const match = serviceCatalog.find(
    (service: ServiceCatalogItem) =>
      service.slug === normalized ||
      category.includes(service.tag) ||
      category.includes(service.title) ||
      service.title.includes(category)
  );
  return match?.slug ?? "not-sure";
}
