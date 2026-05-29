import request from "supertest";
import { beforeEach, describe, expect, it } from "vitest";
import { createTestApp, type TestContext } from "./test-utils.js";

describe("Kuli backend auth and orders", () => {
  let ctx: TestContext;

  beforeEach(() => {
    ctx = createTestApp();
  });

  it("authenticates seeded admin and user with email/password and rejects wrong passwords generically", async () => {
    const adminLogin = await request(ctx.app)
      .post("/api/auth/login")
      .send({ email: "admin@kuli.local", password: "KuliAdmin123!" })
      .expect(200);

    expect(adminLogin.body.user).toMatchObject({ email: "admin@kuli.local", role: "admin" });
    expect(adminLogin.body.token).toEqual(expect.any(String));

    const badLogin = await request(ctx.app)
      .post("/api/auth/login")
      .send({ email: "admin@kuli.local", password: "wrong-password" })
      .expect(401);

    expect(badLogin.body.error.message).toBe("邮箱或密码不正确");
  });

  it("stores password verifiers as hashes instead of plaintext", () => {
    const admin = ctx.db.prepare("select password_hash from users where email = ?").get("admin@kuli.local") as {
      password_hash: string;
    };

    expect(admin.password_hash).not.toBe("KuliAdmin123!");
    expect(admin.password_hash).toMatch(/^pbkdf2\$/);
  });

  it("lets admins list every order while normal users only list their own customer-safe orders", async () => {
    const adminToken = await login(ctx, "admin@kuli.local", "KuliAdmin123!");
    const userToken = await login(ctx, "demo@kuli.local", "KuliUser123!");

    const adminOrders = await request(ctx.app)
      .get("/api/admin/orders")
      .set("Authorization", `Bearer ${adminToken}`)
      .expect(200);

    expect(adminOrders.body.orders.length).toBeGreaterThanOrEqual(2);
    expect(adminOrders.body.orders[0]).toHaveProperty("cost");
    expect(adminOrders.body.orders[0]).toHaveProperty("profit");

    const userOrders = await request(ctx.app)
      .get("/api/orders")
      .set("Authorization", `Bearer ${userToken}`)
      .expect(200);

    expect(userOrders.body.orders).toHaveLength(1);
    expect(userOrders.body.orders[0]).not.toHaveProperty("cost");
    expect(userOrders.body.orders[0]).not.toHaveProperty("profit");
    expect(userOrders.body.orders[0].ownerEmail).toBe("demo@kuli.local");
  });

  it("prevents normal users from reading other users' orders or admin endpoints", async () => {
    const userToken = await login(ctx, "demo@kuli.local", "KuliUser123!");

    await request(ctx.app)
      .get("/api/admin/orders")
      .set("Authorization", `Bearer ${userToken}`)
      .expect(403);

    await request(ctx.app)
      .get("/api/orders/KULI-OTHER-001")
      .set("Authorization", `Bearer ${userToken}`)
      .expect(404);
  });

  it("creates public inquiries and logged-in user orders with unique order numbers", async () => {
    const publicInquiry = await request(ctx.app)
      .post("/api/public/inquiries")
      .send({
        demand: "我有一个 PDF 想翻译并保留格式",
        category: "文档处理",
        urgency: "1-2 天",
        budget: "100-300",
        contact: "wechat:kuli-demo"
      })
      .expect(201);

    expect(publicInquiry.body.order.orderNumber).toMatch(/^KULI-/);
    expect(publicInquiry.body.order.ownerEmail).toBeNull();

    const userToken = await login(ctx, "demo@kuli.local", "KuliUser123!");
    const ownedOrder = await request(ctx.app)
      .post("/api/orders")
      .set("Authorization", `Bearer ${userToken}`)
      .send({
        demand: "想做一个课程项目网页 demo",
        category: "小工具开发",
        urgency: "3-5 天",
        budget: "300-1000",
        contact: "demo@kuli.local"
      })
      .expect(201);

    expect(ownedOrder.body.order.ownerEmail).toBe("demo@kuli.local");
  });

  it("allows admins to update order status and financial fields without exposing internal fields to users", async () => {
    const adminToken = await login(ctx, "admin@kuli.local", "KuliAdmin123!");
    const userToken = await login(ctx, "demo@kuli.local", "KuliUser123!");

    await request(ctx.app)
      .patch("/api/admin/orders/KULI-DEMO-001")
      .set("Authorization", `Bearer ${adminToken}`)
      .send({
        status: "in_progress",
        priority: "high",
        quotedPrice: 280,
        cost: 90,
        profit: 190,
        publicNotes: "已经开始试做初版。",
        internalNotes: "优先处理，预计今天给反馈。"
      })
      .expect(200);

    const userOrder = await request(ctx.app)
      .get("/api/orders/KULI-DEMO-001")
      .set("Authorization", `Bearer ${userToken}`)
      .expect(200);

    expect(userOrder.body.order.status).toBe("in_progress");
    expect(userOrder.body.order.quotedPrice).toBe(280);
    expect(userOrder.body.order).not.toHaveProperty("cost");
    expect(userOrder.body.order).not.toHaveProperty("profit");
    expect(userOrder.body.order).not.toHaveProperty("internalNotes");
  });

  it("serves service detail content used by the public service detail pages", async () => {
    const list = await request(ctx.app).get("/api/services").expect(200);

    expect(list.body.services.map((service: { slug: string }) => service.slug)).toEqual(
      expect.arrayContaining(["ai-tools", "document-processing", "tool-development", "deployment-config", "api-token", "not-sure"])
    );

    const detail = await request(ctx.app).get("/api/services/document-processing").expect(200);
    expect(detail.body.service).toMatchObject({
      slug: "document-processing",
      title: "文档与文件急救"
    });
    expect(detail.body.service.deliverables.length).toBeGreaterThan(0);
    expect(detail.body.service.requiredMaterials.length).toBeGreaterThan(0);
    expect(detail.body.service.faq.length).toBeGreaterThan(0);
  });

  it("polishes rough note text while keeping the original intent and no-charge consultation framing", async () => {
    const response = await request(ctx.app)
      .post("/api/ai/polish-demand")
      .send({
        serviceSlug: "not-sure",
        demand: "我有个表格和 pdf 搞不懂，想先问问能不能帮我看看"
      })
      .expect(200);

    expect(response.body.polishedDemand).toContain("先判断");
    expect(response.body.polishedDemand).toContain("表格");
    expect(response.body.hints).toEqual(expect.arrayContaining(["补充截止时间", "上传相关文件或截图"]));
  });

  it("stores service-specific owned orders and exposes timeline, messages, attachments, quotes, payments, and deliverables safely", async () => {
    const userToken = await login(ctx, "demo@kuli.local", "KuliUser123!");
    const adminToken = await login(ctx, "admin@kuli.local", "KuliAdmin123!");

    const created = await request(ctx.app)
      .post("/api/orders")
      .set("Authorization", `Bearer ${userToken}`)
      .send({
        serviceSlug: "document-processing",
        demand: "我需要翻译一份 PDF，并尽量保留表格和公式排版。",
        category: "文档处理",
        urgency: "1-2 天",
        budget: "100-300",
        contact: "demo@kuli.local"
      })
      .expect(201);

    const orderNumber = created.body.order.orderNumber;
    expect(created.body.order.serviceSlug).toBe("document-processing");

    await request(ctx.app)
      .post(`/api/orders/${orderNumber}/messages`)
      .set("Authorization", `Bearer ${userToken}`)
      .send({ body: "我补充一下：文件里有 3 页扫描图。" })
      .expect(201);

    await request(ctx.app)
      .post(`/api/orders/${orderNumber}/attachments`)
      .set("Authorization", `Bearer ${userToken}`)
      .send({ fileName: "sample.pdf", fileSize: 2048, contentType: "application/pdf" })
      .expect(201);

    await request(ctx.app)
      .post(`/api/admin/orders/${orderNumber}/quotes`)
      .set("Authorization", `Bearer ${adminToken}`)
      .send({ amount: 180, kind: "full", note: "PDF 翻译保排版报价" })
      .expect(201);

    await request(ctx.app)
      .post(`/api/admin/orders/${orderNumber}/payments`)
      .set("Authorization", `Bearer ${adminToken}`)
      .send({ amount: 80, kind: "deposit", method: "wechat", status: "received", note: "微信定金已收" })
      .expect(201);

    await request(ctx.app)
      .post(`/api/admin/orders/${orderNumber}/deliverables`)
      .set("Authorization", `Bearer ${adminToken}`)
      .send({ title: "PDF 初版译稿", description: "已保留主要表格结构", storageKey: "deliverables/demo.pdf" })
      .expect(201);

    await request(ctx.app)
      .patch(`/api/admin/orders/${orderNumber}/status`)
      .set("Authorization", `Bearer ${adminToken}`)
      .send({ status: "review", publicNotes: "初版已交付，等你验收。", internalNotes: "注意扫描页需人工复核。" })
      .expect(200);

    const userOrder = await request(ctx.app)
      .get(`/api/orders/${orderNumber}`)
      .set("Authorization", `Bearer ${userToken}`)
      .expect(200);

    expect(userOrder.body.order.status).toBe("review");
    expect(userOrder.body.order.messages).toHaveLength(1);
    expect(userOrder.body.order.attachments[0]).toMatchObject({ fileName: "sample.pdf", storageKey: expect.any(String) });
    expect(userOrder.body.order.quotes[0]).toMatchObject({ amount: 180, kind: "full" });
    expect(userOrder.body.order.payments[0]).toMatchObject({ amount: 80, kind: "deposit", status: "received" });
    expect(userOrder.body.order.deliverables[0]).toMatchObject({ title: "PDF 初版译稿" });
    expect(userOrder.body.order.events.map((event: { status: string }) => event.status)).toContain("review");
    expect(userOrder.body.order).not.toHaveProperty("cost");
    expect(userOrder.body.order).not.toHaveProperty("internalNotes");

    const adminOrder = await request(ctx.app)
      .get(`/api/admin/orders/${orderNumber}`)
      .set("Authorization", `Bearer ${adminToken}`)
      .expect(200);

    expect(adminOrder.body.order.internalNotes).toBe("注意扫描页需人工复核。");
    expect(adminOrder.body.order.quotes[0].createdByEmail).toBe("admin@kuli.local");

    await request(ctx.app)
      .post(`/api/orders/${orderNumber}/acceptance`)
      .set("Authorization", `Bearer ${userToken}`)
      .send({ note: "确认验收，效果可以。" })
      .expect(200);

    const completedOrder = await request(ctx.app)
      .get(`/api/orders/${orderNumber}`)
      .set("Authorization", `Bearer ${userToken}`)
      .expect(200);

    expect(completedOrder.body.order.status).toBe("completed");
    expect(completedOrder.body.order.events.map((event: { status: string }) => event.status)).toContain("completed");
  });

  it("creates notes with uploaded file payloads and exposes an admin agent brief beside the user's original words", async () => {
    const userToken = await login(ctx, "demo@kuli.local", "KuliUser123!");
    const adminToken = await login(ctx, "admin@kuli.local", "KuliAdmin123!");

    const created = await request(ctx.app)
      .post("/api/orders")
      .set("Authorization", `Bearer ${userToken}`)
      .send({
        serviceSlug: "not-sure",
        demand: "老师给了一个 Excel 和几张截图，我不知道怎么整理，想先咨询能不能帮我看看。",
        originalDemand: "excel 和截图乱七八糟，我不会弄，先问问",
        category: "先聊聊",
        urgency: "不急",
        budget: "先报价看看",
        contact: "demo@kuli.local",
        attachments: [
          {
            fileName: "需求截图.png",
            fileSize: 12,
            contentType: "image/png",
            contentBase64: Buffer.from("fake image").toString("base64")
          }
        ]
      })
      .expect(201);

    expect(created.body.order.attachments[0]).toMatchObject({
      fileName: "需求截图.png",
      contentType: "image/png",
      storageKey: expect.stringContaining("local-object-store/")
    });

    const adminOrder = await request(ctx.app)
      .get(`/api/admin/orders/${created.body.order.orderNumber}`)
      .set("Authorization", `Bearer ${adminToken}`)
      .expect(200);

    expect(adminOrder.body.order.demand).toContain("老师给了一个 Excel");
    expect(adminOrder.body.order.originalDemand).toContain("excel 和截图乱七八糟");
    expect(adminOrder.body.order.agentBrief.summary).toContain("Excel");
    expect(adminOrder.body.order.agentBrief.originalDemand).toContain("excel 和截图乱七八糟");
    expect(adminOrder.body.order.agentBrief.suggestedQuestions.length).toBeGreaterThan(0);
    expect(adminOrder.body.order.agentBrief.consultationFirst).toBe(true);
  });
});

async function login(ctx: TestContext, email: string, password: string) {
  const response = await request(ctx.app).post("/api/auth/login").send({ email, password }).expect(200);
  return response.body.token as string;
}
