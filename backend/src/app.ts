import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import cors from "cors";
import express, { type NextFunction, type Request, type Response } from "express";
import type Database from "better-sqlite3";
import { z, ZodError } from "zod";
import {
  addDeliverable,
  addOrderAttachment,
  addOrderEvent,
  addOrderMessage,
  addPaymentRecord,
  addQuote,
  createOrder,
  createUser,
  findAdminOrder,
  findUserOrder,
  getOrderCollections,
  getService,
  getUserByEmail,
  getUserById,
  listAdminOrders,
  listServices,
  listUserOrders,
  openDatabase,
  updateAdminOrder,
  type DeliverableRow,
  type OrderAttachmentRow,
  type OrderEventRow,
  type OrderMessageRow,
  type OrderRow,
  type PaymentRow,
  type QuoteRow,
  type UserRow
} from "./database.js";
import { createAgentBrief, polishDemand } from "./agent.js";
import { signToken, verifyPassword, verifyToken } from "./security.js";

export type AppOptions = {
  db?: Database.Database;
  jwtSecret?: string;
  corsOrigin?: string;
};

type AuthedRequest = Request & {
  user?: UserRow;
};

const orderStatuses = [
  "submitted",
  "clarifying",
  "quoted",
  "deposit_pending",
  "in_progress",
  "review",
  "final_payment_pending",
  "completed",
  "cancelled"
] as const;

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
});

const registerSchema = loginSchema.extend({
  displayName: z.string().min(1).max(80)
});

const orderInputSchema = z.object({
  serviceSlug: z.string().trim().min(1).max(80).optional(),
  demand: z.string().trim().min(1).max(800),
  originalDemand: z.string().trim().min(1).max(800).optional(),
  category: z.string().trim().min(1).max(80),
  title: z.string().trim().min(1).max(120).optional(),
  urgency: z.string().trim().min(1).max(40).optional(),
  budget: z.string().trim().min(1).max(40).optional(),
  contact: z.string().trim().min(1).max(160),
  remoteHelp: z.string().trim().max(80).optional(),
  customerName: z.string().trim().max(80).optional(),
  attachments: z
    .array(
      z.object({
        fileName: z.string().trim().min(1).max(180),
        fileSize: z.number().int().nonnegative().max(25 * 1024 * 1024),
        contentType: z.string().trim().min(1).max(120),
        contentBase64: z.string().max(40 * 1024 * 1024).optional()
      })
    )
    .max(8)
    .optional()
});

const adminPatchSchema = z.object({
  status: z.enum(orderStatuses).optional(),
  priority: z.enum(["low", "normal", "high", "urgent"]).optional(),
  quotedPrice: z.number().nonnegative().nullable().optional(),
  cost: z.number().nonnegative().nullable().optional(),
  profit: z.number().nullable().optional(),
  publicNotes: z.string().max(1000).optional(),
  internalNotes: z.string().max(1000).optional()
});

const messageSchema = z.object({
  body: z.string().trim().min(1).max(1200)
});

const attachmentSchema = z.object({
  fileName: z.string().trim().min(1).max(180),
  fileSize: z.number().int().nonnegative().max(200 * 1024 * 1024),
  contentType: z.string().trim().min(1).max(120),
  storageKey: z.string().trim().min(1).max(240).optional(),
  contentBase64: z.string().max(40 * 1024 * 1024).optional()
});

const quoteSchema = z.object({
  amount: z.number().nonnegative(),
  kind: z.enum(["full", "deposit", "final", "change", "other"]),
  note: z.string().trim().min(1).max(800)
});

const paymentSchema = z.object({
  amount: z.number().nonnegative(),
  kind: z.enum(["deposit", "final", "full", "refund", "other"]),
  method: z.string().trim().min(1).max(80),
  status: z.enum(["pending", "received", "failed", "refunded"]),
  note: z.string().trim().max(800).optional()
});

const deliverableSchema = z.object({
  title: z.string().trim().min(1).max(120),
  description: z.string().trim().max(1000).optional(),
  storageKey: z.string().trim().min(1).max(240)
});

const statusPatchSchema = z.object({
  status: z.enum(orderStatuses),
  publicNotes: z.string().max(1000).optional(),
  internalNotes: z.string().max(1000).optional()
});

const acceptanceSchema = z.object({
  note: z.string().trim().max(800).optional()
});

const polishDemandSchema = z.object({
  demand: z.string().trim().min(1).max(800),
  serviceSlug: z.string().trim().min(1).max(80).optional()
});

export function createApp(options: AppOptions = {}) {
  const db = options.db ?? openDatabase(process.env.DATABASE_PATH ?? fileURLToPath(new URL("../data/kuli.sqlite", import.meta.url)));
  const jwtSecret = options.jwtSecret ?? process.env.JWT_SECRET ?? "dev-only-kuli-secret-change-me";

  const app = express();
  app.use(cors({ origin: options.corsOrigin ?? process.env.CORS_ORIGIN ?? true }));
  app.use(express.json({ limit: "40mb" }));

  app.get("/health", (_req, res) => {
    res.json({ ok: true });
  });

  app.get("/api/services", (_req, res) => {
    res.json({ services: listServices() });
  });

  app.get("/api/services/:slug", (req, res, next) => {
    try {
      const service = getService(routeParam(req.params.slug));
      if (!service) throw httpError(404, "服务不存在");
      res.json({ service });
    } catch (error) {
      next(error);
    }
  });

  app.post("/api/ai/polish-demand", (req, res, next) => {
    try {
      const input = polishDemandSchema.parse(req.body);
      assertKnownService(input.serviceSlug);
      res.json(polishDemand(input));
    } catch (error) {
      next(error);
    }
  });

  app.post("/api/auth/login", (req, res, next) => {
    try {
      const input = loginSchema.parse(req.body);
      const user = getUserByEmail(db, input.email);
      if (!user || !verifyPassword(input.password, user.password_hash)) {
        throw httpError(401, "邮箱或密码不正确");
      }
      res.json(authResponse(user, jwtSecret));
    } catch (error) {
      next(error);
    }
  });

  app.post("/api/auth/register", (req, res, next) => {
    try {
      const input = registerSchema.parse(req.body);
      if (getUserByEmail(db, input.email)) throw httpError(409, "邮箱已注册");
      const user = createUser(db, input);
      res.status(201).json(authResponse(user, jwtSecret));
    } catch (error) {
      next(error);
    }
  });

  app.get("/api/auth/me", requireAuth(db, jwtSecret), (req: AuthedRequest, res) => {
    res.json({ user: publicUser(req.user!) });
  });

  app.post("/api/public/inquiries", (req, res, next) => {
    try {
      const input = orderInputSchema.parse(req.body);
      assertKnownService(input.serviceSlug);
      const order = createOrder(db, {
        ...input,
        ownerUserId: null,
        customerName: input.customerName ?? "游客"
      });
      persistSubmittedAttachments(db, order.order_number, null, input.attachments);
      res.status(201).json({ order: toCustomerOrder(db, order) });
    } catch (error) {
      next(error);
    }
  });

  app.get("/api/orders", requireAuth(db, jwtSecret), (req: AuthedRequest, res) => {
    const orders = listUserOrders(db, req.user!.id).map((order) => toCustomerOrder(db, order));
    res.json({ orders });
  });

  app.post("/api/orders", requireAuth(db, jwtSecret), (req: AuthedRequest, res, next) => {
    try {
      const input = orderInputSchema.parse(req.body);
      assertKnownService(input.serviceSlug);
      const order = createOrder(db, {
        ...input,
        ownerUserId: req.user!.id,
        customerName: req.user!.display_name
      });
      persistSubmittedAttachments(db, order.order_number, req.user!.id, input.attachments);
      res.status(201).json({ order: toCustomerOrder(db, order) });
    } catch (error) {
      next(error);
    }
  });

  app.get("/api/orders/:orderNumber", requireAuth(db, jwtSecret), (req: AuthedRequest, res, next) => {
    try {
      const order = findUserOrder(db, req.user!.id, routeParam(req.params.orderNumber));
      if (!order) throw httpError(404, "订单不存在");
      res.json({ order: toCustomerOrder(db, order) });
    } catch (error) {
      next(error);
    }
  });

  app.post("/api/orders/:orderNumber/messages", requireAuth(db, jwtSecret), (req: AuthedRequest, res, next) => {
    try {
      const orderNumber = routeParam(req.params.orderNumber);
      const order = findUserOrder(db, req.user!.id, orderNumber);
      if (!order) throw httpError(404, "订单不存在");
      const input = messageSchema.parse(req.body);
      addOrderMessage(db, {
        orderNumber,
        authorUserId: req.user!.id,
        body: input.body
      });
      res.status(201).json({ order: toCustomerOrder(db, findUserOrder(db, req.user!.id, orderNumber)!) });
    } catch (error) {
      next(error);
    }
  });

  app.post("/api/orders/:orderNumber/attachments", requireAuth(db, jwtSecret), (req: AuthedRequest, res, next) => {
    try {
      const orderNumber = routeParam(req.params.orderNumber);
      const order = findUserOrder(db, req.user!.id, orderNumber);
      if (!order) throw httpError(404, "订单不存在");
      const input = attachmentSchema.parse(req.body);
      const storageKey = input.storageKey ?? localObjectKey(orderNumber, input.fileName);
      writeLocalObject(storageKey, input.contentBase64);
      addOrderAttachment(db, {
        orderNumber,
        uploaderUserId: req.user!.id,
        fileName: input.fileName,
        fileSize: input.fileSize,
        contentType: input.contentType,
        storageKey
      });
      res.status(201).json({ order: toCustomerOrder(db, findUserOrder(db, req.user!.id, orderNumber)!) });
    } catch (error) {
      next(error);
    }
  });

  app.post("/api/orders/:orderNumber/acceptance", requireAuth(db, jwtSecret), (req: AuthedRequest, res, next) => {
    try {
      const orderNumber = routeParam(req.params.orderNumber);
      const order = findUserOrder(db, req.user!.id, orderNumber);
      if (!order) throw httpError(404, "订单不存在");
      const input = acceptanceSchema.parse(req.body);
      updateAdminOrder(db, orderNumber, {
        status: "completed",
        public_notes: input.note || "客户已确认验收。"
      });
      addOrderEvent(db, {
        orderNumber,
        status: "completed",
        note: input.note || "客户已确认验收",
        createdBy: req.user!.id
      });
      res.json({ order: toCustomerOrder(db, findUserOrder(db, req.user!.id, orderNumber)!) });
    } catch (error) {
      next(error);
    }
  });

  app.get("/api/admin/orders", requireAuth(db, jwtSecret), requireAdmin, (_req, res) => {
    res.json({ orders: listAdminOrders(db).map((order) => toAdminOrder(db, order)) });
  });

  app.get("/api/admin/orders/:orderNumber", requireAuth(db, jwtSecret), requireAdmin, (req, res, next) => {
    try {
      const order = findAdminOrder(db, routeParam(req.params.orderNumber));
      if (!order) throw httpError(404, "订单不存在");
      res.json({ order: toAdminOrder(db, order) });
    } catch (error) {
      next(error);
    }
  });

  app.patch("/api/admin/orders/:orderNumber", requireAuth(db, jwtSecret), requireAdmin, (req: AuthedRequest, res, next) => {
    try {
      const input = adminPatchSchema.parse(req.body);
      const orderNumber = routeParam(req.params.orderNumber);
      const before = findAdminOrder(db, orderNumber);
      const order = updateAdminOrder(db, routeParam(req.params.orderNumber), {
        status: input.status,
        priority: input.priority,
        quoted_price: input.quotedPrice,
        cost: input.cost,
        profit: input.profit,
        public_notes: input.publicNotes,
        internal_notes: input.internalNotes
      });
      if (!order) throw httpError(404, "订单不存在");
      if (input.status && before?.status !== input.status) {
        addOrderEvent(db, {
          orderNumber,
          status: input.status,
          note: statusNote(input.status),
          createdBy: req.user!.id
        });
      }
      res.json({ order: toAdminOrder(db, order) });
    } catch (error) {
      next(error);
    }
  });

  app.post("/api/admin/orders/:orderNumber/quotes", requireAuth(db, jwtSecret), requireAdmin, (req: AuthedRequest, res, next) => {
    try {
      const orderNumber = routeParam(req.params.orderNumber);
      if (!findAdminOrder(db, orderNumber)) throw httpError(404, "订单不存在");
      const input = quoteSchema.parse(req.body);
      addQuote(db, {
        orderNumber,
        amount: input.amount,
        kind: input.kind,
        note: input.note,
        createdBy: req.user!.id
      });
      updateAdminOrder(db, orderNumber, {
        status: "quoted",
        quoted_price: input.amount,
        public_notes: input.note
      });
      addOrderEvent(db, {
        orderNumber,
        status: "quoted",
        note: "管理员已发送报价",
        createdBy: req.user!.id
      });
      res.status(201).json({ order: toAdminOrder(db, findAdminOrder(db, orderNumber)!) });
    } catch (error) {
      next(error);
    }
  });

  app.post("/api/admin/orders/:orderNumber/payments", requireAuth(db, jwtSecret), requireAdmin, (req: AuthedRequest, res, next) => {
    try {
      const orderNumber = routeParam(req.params.orderNumber);
      if (!findAdminOrder(db, orderNumber)) throw httpError(404, "订单不存在");
      const input = paymentSchema.parse(req.body);
      addPaymentRecord(db, {
        orderNumber,
        amount: input.amount,
        kind: input.kind,
        method: input.method,
        status: input.status,
        note: input.note ?? "",
        createdBy: req.user!.id
      });
      addOrderEvent(db, {
        orderNumber,
        status: input.kind === "final" && input.status === "received" ? "final_payment_pending" : "deposit_pending",
        note: `管理员记录${input.kind === "final" ? "尾款" : "付款"}：${input.status}`,
        createdBy: req.user!.id
      });
      res.status(201).json({ order: toAdminOrder(db, findAdminOrder(db, orderNumber)!) });
    } catch (error) {
      next(error);
    }
  });

  app.post("/api/admin/orders/:orderNumber/deliverables", requireAuth(db, jwtSecret), requireAdmin, (req: AuthedRequest, res, next) => {
    try {
      const orderNumber = routeParam(req.params.orderNumber);
      if (!findAdminOrder(db, orderNumber)) throw httpError(404, "订单不存在");
      const input = deliverableSchema.parse(req.body);
      addDeliverable(db, {
        orderNumber,
        title: input.title,
        description: input.description ?? "",
        storageKey: input.storageKey,
        createdBy: req.user!.id
      });
      updateAdminOrder(db, orderNumber, {
        status: "review",
        public_notes: "交付物已上传，等待验收。"
      });
      addOrderEvent(db, {
        orderNumber,
        status: "review",
        note: "管理员上传了交付物",
        createdBy: req.user!.id
      });
      res.status(201).json({ order: toAdminOrder(db, findAdminOrder(db, orderNumber)!) });
    } catch (error) {
      next(error);
    }
  });

  app.patch("/api/admin/orders/:orderNumber/status", requireAuth(db, jwtSecret), requireAdmin, (req: AuthedRequest, res, next) => {
    try {
      const orderNumber = routeParam(req.params.orderNumber);
      const input = statusPatchSchema.parse(req.body);
      const order = updateAdminOrder(db, orderNumber, {
        status: input.status,
        public_notes: input.publicNotes,
        internal_notes: input.internalNotes
      });
      if (!order) throw httpError(404, "订单不存在");
      addOrderEvent(db, {
        orderNumber,
        status: input.status,
        note: input.publicNotes ?? statusNote(input.status),
        createdBy: req.user!.id
      });
      res.json({ order: toAdminOrder(db, findAdminOrder(db, orderNumber)!) });
    } catch (error) {
      next(error);
    }
  });

  app.use(errorHandler);
  return app;
}

function requireAuth(db: Database.Database, jwtSecret: string) {
  return (req: AuthedRequest, _res: Response, next: NextFunction) => {
    const header = req.header("Authorization");
    const token = header?.startsWith("Bearer ") ? header.slice("Bearer ".length) : "";
    const payload = token ? verifyToken(token, jwtSecret) : null;
    if (!payload) return next(httpError(401, "请先登录"));

    const user = getUserById(db, payload.sub);
    if (!user) return next(httpError(401, "请先登录"));
    req.user = user;
    next();
  };
}

function requireAdmin(req: AuthedRequest, _res: Response, next: NextFunction) {
  if (req.user?.role !== "admin") return next(httpError(403, "没有管理员权限"));
  next();
}

function authResponse(user: UserRow, jwtSecret: string) {
  return {
    token: signToken({ sub: user.id, email: user.email, role: user.role }, jwtSecret),
    user: publicUser(user)
  };
}

function publicUser(user: UserRow) {
  return {
    id: user.id,
    email: user.email,
    role: user.role,
    displayName: user.display_name
  };
}

function toCustomerOrder(db: Database.Database, order: OrderRow) {
  const collections = getOrderCollections(db, order.order_number, false);
  return {
    id: order.id,
    orderNumber: order.order_number,
    ownerEmail: order.owner_email,
    customerName: order.customer_name,
    contact: order.contact,
    serviceSlug: order.service_slug,
    category: order.category,
    title: order.title,
    demand: order.demand,
    originalDemand: order.original_demand || order.demand,
    urgency: order.urgency,
    budget: order.budget,
    remoteHelp: order.remote_help,
    quotedPrice: order.quoted_price,
    status: order.status,
    priorityLabel: priorityLabel(order.priority),
    publicNotes: order.public_notes,
    createdAt: order.created_at,
    updatedAt: order.updated_at,
    events: collections.events.map(toEvent),
    messages: collections.messages.map(toMessage),
    attachments: collections.attachments.map(toAttachment),
    quotes: collections.quotes.map(toQuote),
    payments: collections.payments.map(toPayment),
    deliverables: collections.deliverables.map(toDeliverable)
  };
}

function toAdminOrder(db: Database.Database, order: OrderRow) {
  const collections = getOrderCollections(db, order.order_number, true);
  return {
    ...toCustomerOrder(db, order),
    events: collections.events.map(toEvent),
    messages: collections.messages.map(toMessage),
    attachments: collections.attachments.map(toAttachment),
    quotes: collections.quotes.map(toQuote),
    payments: collections.payments.map(toPayment),
    deliverables: collections.deliverables.map(toDeliverable),
    ownerUserId: order.owner_user_id,
    cost: order.cost,
    profit: order.profit,
    priority: order.priority,
    internalNotes: order.internal_notes,
    agentBrief: createAgentBrief({
      demand: order.original_demand || order.demand,
      category: order.category,
      serviceSlug: order.service_slug,
      urgency: order.urgency,
      budget: order.budget,
      attachmentCount: collections.attachments.length
    })
  };
}

function priorityLabel(priority: string) {
  const labels: Record<string, string> = {
    low: "低",
    normal: "普通",
    high: "高",
    urgent: "紧急"
  };
  return labels[priority] ?? priority;
}

function toEvent(row: OrderEventRow) {
  return {
    id: row.id,
    status: row.status,
    note: row.note,
    createdByEmail: row.created_by_email,
    createdAt: row.created_at
  };
}

function toMessage(row: OrderMessageRow) {
  return {
    id: row.id,
    authorEmail: row.author_email,
    authorRole: row.author_role,
    body: row.body,
    visibility: row.visibility,
    createdAt: row.created_at
  };
}

function toAttachment(row: OrderAttachmentRow) {
  return {
    id: row.id,
    uploaderEmail: row.uploader_email,
    fileName: row.file_name,
    fileSize: row.file_size,
    contentType: row.content_type,
    storageKey: row.storage_key,
    visibility: row.visibility,
    createdAt: row.created_at
  };
}

function toQuote(row: QuoteRow) {
  return {
    id: row.id,
    amount: row.amount,
    kind: row.kind,
    note: row.note,
    status: row.status,
    createdByEmail: row.created_by_email,
    createdAt: row.created_at
  };
}

function toPayment(row: PaymentRow) {
  return {
    id: row.id,
    amount: row.amount,
    kind: row.kind,
    method: row.method,
    status: row.status,
    note: row.note,
    createdByEmail: row.created_by_email,
    createdAt: row.created_at
  };
}

function toDeliverable(row: DeliverableRow) {
  return {
    id: row.id,
    title: row.title,
    description: row.description,
    storageKey: row.storage_key,
    createdByEmail: row.created_by_email,
    createdAt: row.created_at
  };
}

function assertKnownService(serviceSlug?: string) {
  if (serviceSlug && !getService(serviceSlug)) {
    throw httpError(400, "服务类型不存在");
  }
}

function persistSubmittedAttachments(
  db: Database.Database,
  orderNumber: string,
  uploaderUserId: string | null,
  attachments?: Array<{ fileName: string; fileSize: number; contentType: string; contentBase64?: string }>
) {
  for (const attachment of attachments ?? []) {
    const storageKey = localObjectKey(orderNumber, attachment.fileName);
    writeLocalObject(storageKey, attachment.contentBase64);
    addOrderAttachment(db, {
      orderNumber,
      uploaderUserId,
      fileName: attachment.fileName,
      fileSize: attachment.fileSize,
      contentType: attachment.contentType,
      storageKey
    });
  }
}

function localObjectKey(orderNumber: string, fileName: string) {
  return `local-object-store/${orderNumber}/${Date.now()}-${safeFileName(fileName)}`;
}

function safeFileName(fileName: string) {
  return fileName.replace(/[^\p{L}\p{N}._-]+/gu, "-").slice(0, 120) || "upload.bin";
}

function writeLocalObject(storageKey: string, contentBase64?: string) {
  if (!contentBase64) return;
  const baseDir = process.env.LOCAL_OBJECT_STORE_DIR ?? fileURLToPath(new URL("../data/object-store", import.meta.url));
  const target = path.resolve(baseDir, storageKey.replace(/^local-object-store\//, ""));
  const root = path.resolve(baseDir);
  if (!target.startsWith(root)) throw httpError(400, "附件路径不合法");
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, Buffer.from(contentBase64, "base64"));
}

function statusNote(status: string) {
  const notes: Record<string, string> = {
    submitted: "订单已提交",
    clarifying: "正在确认需求",
    quoted: "已发送报价",
    deposit_pending: "等待定金",
    in_progress: "正在处理",
    review: "等待验收",
    final_payment_pending: "等待尾款",
    completed: "订单已完成",
    cancelled: "订单已取消"
  };
  return notes[status] ?? status;
}

function routeParam(value: string | string[]) {
  return Array.isArray(value) ? value[0] : value;
}

function httpError(status: number, message: string) {
  return Object.assign(new Error(message), { status });
}

function errorHandler(error: unknown, _req: Request, res: Response, _next: NextFunction) {
  if (error instanceof ZodError) {
    return res.status(400).json({ error: { message: "提交内容不完整", issues: error.issues } });
  }
  const status = typeof error === "object" && error && "status" in error ? Number(error.status) : 500;
  const message = error instanceof Error ? error.message : "服务器开小差了";
  return res.status(Number.isInteger(status) ? status : 500).json({ error: { message } });
}
