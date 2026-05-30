import { existsSync } from "node:fs";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://127.0.0.1:3000";
const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const WAIT_TIMEOUT_MS = Number(process.env.SMOKE_TIMEOUT_MS ?? 90_000);
const chromePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH
  ?? (existsSync("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome") ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" : undefined);

const result = {
  pages: [],
  noteOrder: "",
  polishedLength: 0,
  xiaokuOk: false,
  serviceOk: false,
  healthDepsOk: false,
  docsGovernanceOk: false,
  noteOk: false,
  productsOk: false,
  docsOk: false,
  authGateOk: false,
  accountOk: false,
  notificationsOk: false,
  legalOk: false,
  seoOk: false,
  mobileAccountOk: false,
  userOk: false,
  userDetailOk: false,
  adminOk: false,
  adminDetailOk: false,
  badMetrics: [],
  consoleErrors: [],
  pageErrors: []
};

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function url(path) {
  return new URL(path, BASE_URL).toString();
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function waitForHttp(endpoint, label) {
  const started = Date.now();
  let lastError = "";
  while (Date.now() - started < WAIT_TIMEOUT_MS) {
    try {
      const response = await fetch(endpoint);
      if (response.ok) return;
      lastError = `${response.status} ${response.statusText}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await sleep(1000);
  }
  throw new Error(`Timed out waiting for ${label} at ${endpoint}: ${lastError}`);
}

async function goto(page, path) {
  await page.goto(url(path), { waitUntil: "domcontentloaded", timeout: WAIT_TIMEOUT_MS });
  await page.waitForLoadState("networkidle", { timeout: 6000 }).catch(() => undefined);
}

async function clearBrowserState(page) {
  await goto(page, "/");
  await page.evaluate(() => localStorage.clear());
  await page.context().clearCookies();
  await goto(page, "/");
}

function collectErrors(page) {
  page.on("console", (message) => {
    if (message.type() === "error") result.consoleErrors.push(`${page.url()}: ${message.text()}`);
  });
  page.on("pageerror", (error) => {
    result.pageErrors.push(error.message);
  });
}

async function checkPageMetrics(page, path, viewportName) {
  await goto(page, path);
  await page.locator("body").waitFor({ timeout: WAIT_TIMEOUT_MS });
  const metrics = await page.evaluate(() => {
    const root = document.documentElement;
    const bodyText = document.body.innerText.replace(/\s+/g, " ").trim();
    const xiaoku = document.querySelector(".xiaoku");
    const canvas = document.querySelector(".xiaoku-canvas");
    return {
      title: document.title,
      path: location.pathname,
      textLength: bodyText.length,
      overflowX: root.scrollWidth > root.clientWidth + 2,
      xiaoku: Boolean(xiaoku),
      xiaokuCanvas: Boolean(canvas)
    };
  });
  result.pages.push({ viewport: viewportName, requestedPath: path, ...metrics });
  if (metrics.textLength < 80) result.badMetrics.push(`${viewportName} ${path}: page text too short (${metrics.textLength})`);
  if (metrics.overflowX) result.badMetrics.push(`${viewportName} ${path}: horizontal overflow`);
  if (!metrics.xiaoku || !metrics.xiaokuCanvas) result.badMetrics.push(`${viewportName} ${path}: xiaoku layer or canvas missing`);
}

async function checkXiaoku(page) {
  await goto(page, "/");
  await page.locator(".xiaoku-face").click({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("小酷", { exact: true }).waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("帮我写小纸条").waitFor({ timeout: WAIT_TIMEOUT_MS });
  result.xiaokuOk = true;
}

async function checkHealthDeps() {
  const response = await fetch(`${API_BASE_URL}/api/health/deps`);
  assert(response.ok, `Health deps returned ${response.status}`);
  const body = await response.json();
  assert(body.ok === true, "Local health deps should be ok with optional degraded dependencies");
  assert(body.dependencies?.database?.ok === true, "Health deps database check failed");
  assert(body.dependencies?.objectStorage?.ok === true, "Health deps object storage check failed");
  result.healthDepsOk = true;
}

async function checkDocsGovernance() {
  const response = await fetch(`${API_BASE_URL}/api/docs`);
  assert(response.ok, `Docs API returned ${response.status}`);
  const body = await response.json();
  assert(Array.isArray(body.docs), "Docs API did not return docs array");
  assert(body.docs.length === 5, `Docs API expected 5 published docs, got ${body.docs.length}`);
  assert(body.docs.every((item) => item.status === "published"), "Docs API returned an unpublished document");
  result.docsGovernanceOk = true;
}

async function checkServiceNavigation(page) {
  await goto(page, "/services");
  await page.locator('a[href="/services/ai-tools"]').first().click({ timeout: WAIT_TIMEOUT_MS });
  await page.waitForURL("**/services/ai-tools", { timeout: WAIT_TIMEOUT_MS });
  await page.getByText("带着这个服务写小纸条").waitFor({ timeout: WAIT_TIMEOUT_MS });
  result.serviceOk = true;
}

async function checkNoteFlow(page) {
  await clearBrowserState(page);
  await loginAs(page, "demo@kuli.local", "KuliUser123!", "/orders");
  await goto(page, "/note?service=ai-tools");
  await page.locator("#need-detail").fill("我想做一个课程汇报 PPT，大概 15 页，内容在 Word 里，希望更好看一点。");
  await page.getByRole("button", { name: "让 AI 帮我整理" }).click();
  const polished = page.locator("#polished-demand");
  await expectValueLength(polished, 30);
  result.polishedLength = (await polished.inputValue()).length;
  await page.locator("#contact").fill("demo@kuli.local");
  await page.getByRole("button", { name: "丢张小纸条给酷里看看" }).click();
  const status = page.locator(".status-box.is-visible");
  await status.waitFor({ timeout: WAIT_TIMEOUT_MS });
  const text = await status.innerText();
  const match = text.match(/KULI-\d{6}/);
  assert(match, `Note submission did not show an order number: ${text}`);
  result.noteOrder = match[0];
  result.noteOk = true;
}

async function checkAuthGate(page) {
  await clearBrowserState(page);
  await goto(page, "/note?service=ai-tools");
  await page.waitForURL("**/login?redirect=**", { timeout: WAIT_TIMEOUT_MS });
  const noteRedirect = new URL(page.url()).searchParams.get("redirect");
  assert(noteRedirect === "/note?service=ai-tools", `Note auth redirect mismatch: ${noteRedirect}`);

  await goto(page, "/orders");
  await page.waitForURL("**/login?redirect=**", { timeout: WAIT_TIMEOUT_MS });
  const ordersRedirect = new URL(page.url()).searchParams.get("redirect");
  assert(ordersRedirect === "/orders", `Orders auth redirect mismatch: ${ordersRedirect}`);

  await goto(page, "/login");
  await page.getByRole("button", { name: "忘记密码？" }).click();
  await page.getByText("重置邮箱").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await goto(page, "/login?resetToken=smoke-token");
  await page.getByText("新密码").waitFor({ timeout: WAIT_TIMEOUT_MS });

  result.authGateOk = true;
}

async function checkProductsPage(page) {
  await clearBrowserState(page);
  await goto(page, "/products");
  await page.getByText("酷里的工具和子产品").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("酷里小纸条").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("小酷 Agent").waitFor({ timeout: WAIT_TIMEOUT_MS });
  result.productsOk = true;
}

async function checkDocsCenter(page) {
  await clearBrowserState(page);
  await goto(page, "/help/quick-start");
  await page.getByRole("heading", { name: "快速开始" }).waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.locator("#write-note").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("继续阅读").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.locator('a[href="/help/guides"]').first().click({ timeout: WAIT_TIMEOUT_MS });
  await page.waitForURL("**/help/guides", { timeout: WAIT_TIMEOUT_MS });
  await page.locator("#upload-materials").waitFor({ timeout: WAIT_TIMEOUT_MS });
  result.docsOk = true;
}

async function checkLegalAndUploadPolicy(page) {
  await clearBrowserState(page);
  await goto(page, "/legal/privacy");
  await page.getByRole("heading", { name: "隐私政策" }).waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("不出售个人数据").waitFor({ timeout: WAIT_TIMEOUT_MS });

  await goto(page, "/legal/terms");
  await page.getByRole("heading", { name: "服务条款" }).waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("小酷不代表最终报价").waitFor({ timeout: WAIT_TIMEOUT_MS });

  await goto(page, "/legal/upload-policy");
  await page.getByRole("heading", { name: "文件上传与敏感信息说明" }).waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("密码、验证码、私钥、支付凭证、身份证").waitFor({ timeout: WAIT_TIMEOUT_MS });

  await loginAs(page, "demo@kuli.local", "KuliUser123!", "/orders");
  await goto(page, "/note");
  await page.getByText("不要提交密码、验证码、私钥").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await goto(page, "/orders/KULI-DEMO-001");
  await page.getByText("附件不要包含密码、验证码、私钥").waitFor({ timeout: WAIT_TIMEOUT_MS });

  result.legalOk = true;
}

async function checkSeoAndGrowth(page) {
  for (const path of ["/", "/services/ai-tools", "/help/faq", "/products"]) {
    await goto(page, path);
    const seo = await page.evaluate(() => {
      const meta = (name) => document.querySelector(`meta[name="${name}"]`)?.getAttribute("content") ?? "";
      const property = (name) => document.querySelector(`meta[property="${name}"]`)?.getAttribute("content") ?? "";
      return {
        title: document.title,
        description: meta("description"),
        canonical: document.querySelector('link[rel="canonical"]')?.getAttribute("href") ?? "",
        ogTitle: property("og:title"),
        ogDescription: property("og:description"),
        ogImage: property("og:image"),
        jsonLdTypes: [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map((node) => {
            try {
              return JSON.parse(node.textContent || "{}")["@type"];
            } catch {
              return "invalid";
            }
          })
      };
    });
    assert(seo.title.includes("酷里") || seo.title.includes("Kuli"), `${path} title missing brand`);
    assert(seo.description.length >= 40, `${path} description too short`);
    assert(seo.canonical.endsWith(path === "/" ? "/" : path), `${path} canonical mismatch: ${seo.canonical}`);
    assert(seo.ogTitle && seo.ogDescription && seo.ogImage, `${path} OG metadata missing`);
    if (path === "/services/ai-tools" || path === "/help/faq") {
      assert(seo.jsonLdTypes.includes("FAQPage"), `${path} missing FAQPage JSON-LD`);
    }
  }

  const sitemap = await fetch(`${BASE_URL}/sitemap.xml`);
  assert(sitemap.ok, `sitemap.xml returned ${sitemap.status}`);
  const sitemapText = await sitemap.text();
  assert(sitemapText.includes("<urlset"), "sitemap.xml missing urlset");
  assert(sitemapText.includes("/services/ai-tools"), "sitemap.xml missing service route");
  assert(sitemapText.includes("/help/faq"), "sitemap.xml missing FAQ route");

  const robots = await fetch(`${BASE_URL}/robots.txt`);
  assert(robots.ok, `robots.txt returned ${robots.status}`);
  const robotsText = await robots.text();
  assert(robotsText.includes("Sitemap:"), "robots.txt missing sitemap");
  assert(robotsText.includes("Allow: /"), "robots.txt missing allow rule");

  result.seoOk = true;
}

async function checkAccountCenter(page) {
  await clearBrowserState(page);
  await loginAs(page, "demo@kuli.local", "KuliUser123!", "/orders");

  await goto(page, "/me");
  await page.getByText("你的酷里主页").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("积分进度").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("邮箱验证").waitFor({ timeout: WAIT_TIMEOUT_MS });

  await goto(page, "/settings");
  await page.getByText("账号设置").waitFor({ timeout: WAIT_TIMEOUT_MS });
  const displayName = `Smoke 用户 ${Date.now()}`;
  await page.getByLabel("展示名").fill(displayName);
  await page.getByRole("button", { name: "保存设置" }).click();
  await page.getByText("设置已保存").waitFor({ timeout: WAIT_TIMEOUT_MS });

  await goto(page, "/referrals");
  await page.getByText("邀请朋友来酷里").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByRole("button", { name: "复制邀请链接" }).waitFor({ timeout: WAIT_TIMEOUT_MS });

  result.accountOk = true;
}

async function checkNotificationCenter(page) {
  await clearBrowserState(page);
  await loginAs(page, "demo@kuli.local", "KuliUser123!", "/orders");
  await goto(page, "/notifications");
  await page.getByRole("heading", { name: "通知中心" }).waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("管理员回复了你的订单").first().waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByRole("button", { name: "全部已读" }).click();
  await page.getByText("未读 0").waitFor({ timeout: WAIT_TIMEOUT_MS });
  result.notificationsOk = true;
}

async function checkMobileAccountNavigation(page) {
  await page.setViewportSize({ width: 390, height: 844 });
  await goto(page, "/me");
  const accountSummary = page.locator(".account-menu summary");
  await accountSummary.waitFor({ timeout: WAIT_TIMEOUT_MS });
  assert(await accountSummary.isVisible(), "Mobile account menu summary is hidden");
  await accountSummary.click();
  await page.getByText("个人主页").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("积分与邀请").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.setViewportSize({ width: 1440, height: 980 });
  result.mobileAccountOk = true;
}

async function expectValueLength(locator, minLength) {
  const started = Date.now();
  while (Date.now() - started < WAIT_TIMEOUT_MS) {
    const value = await locator.inputValue().catch(() => "");
    if (value.length >= minLength) return;
    await sleep(300);
  }
  throw new Error(`Expected input value length >= ${minLength}`);
}

async function loginAs(page, email, password, targetPath) {
  await goto(page, "/login");
  await page.evaluate(() => localStorage.removeItem("kuli-v2-token"));
  await page.getByLabel("邮箱").fill(email);
  await page.getByLabel("密码").fill(password);
  await page.locator(".auth-form button[type='submit']").click();
  await page.waitForURL(`**${targetPath}`, { timeout: WAIT_TIMEOUT_MS });
}

async function checkUserOrders(page) {
  await loginAs(page, "demo@kuli.local", "KuliUser123!", "/orders");
  await page.getByText("KULI-DEMO-001").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await assertNoInternalText(page, "User orders page");

  await page.locator('a[href="/orders/KULI-DEMO-001"]').first().click({ timeout: WAIT_TIMEOUT_MS });
  await page.waitForURL("**/orders/KULI-DEMO-001", { timeout: WAIT_TIMEOUT_MS });
  await page.getByText("进度时间线").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("报价与付款").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await assertNoInternalText(page, "User order detail page");

  const message = `浏览器 smoke 补充说明 ${Date.now()}`;
  await page.getByPlaceholder("补充说明、链接或验收反馈").fill(message);
  await page.getByRole("button", { name: "发送" }).click();
  await page.getByText(message).waitFor({ timeout: WAIT_TIMEOUT_MS });

  const attachmentName = `smoke-note-${Date.now()}.txt`;
  await page.locator('input[type="file"]').setInputFiles({
    name: attachmentName,
    mimeType: "text/plain",
    buffer: Buffer.from("browser smoke attachment")
  });
  await page.getByRole("button", { name: "登记附件" }).click();
  await page.getByText(attachmentName, { exact: true }).first().waitFor({ timeout: WAIT_TIMEOUT_MS });

  await page.setViewportSize({ width: 390, height: 844 });
  await checkPageMetrics(page, "/orders/KULI-DEMO-001", "mobile-auth");
  await page.setViewportSize({ width: 1440, height: 980 });

  result.userOk = true;
  result.userDetailOk = true;
}

async function checkAdminOrders(page) {
  await clearBrowserState(page);
  await loginAs(page, "admin@kuli.local", "KuliAdmin123!", "/admin");
  await page.getByText("共").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("KULI-DEMO-001").waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.locator('input[placeholder*="搜索订单号"]').fill("KULI-DEMO-001");
  await page.getByRole("button", { name: "搜索" }).click();
  await page.getByText("KULI-DEMO-001").waitFor({ timeout: WAIT_TIMEOUT_MS });

  await page.locator('a[href="/admin/orders/KULI-DEMO-001"]').first().click({ timeout: WAIT_TIMEOUT_MS });
  await page.waitForURL("**/admin/orders/KULI-DEMO-001", { timeout: WAIT_TIMEOUT_MS });
  await page.getByRole("term").filter({ hasText: "内部备注" }).waitFor({ timeout: WAIT_TIMEOUT_MS });
  await page.getByText("AI 自动化建议").waitFor({ timeout: WAIT_TIMEOUT_MS });

  await page.getByRole("button", { name: "重新运行自动化" }).click();
  await page.getByText("建议状态").first().waitFor({ timeout: WAIT_TIMEOUT_MS });

  const adminMessage = `管理员 smoke 公开备注 ${Date.now()}`;
  await page.getByPlaceholder("给客户或内部团队的备注").fill(adminMessage);
  await page.getByRole("button", { name: "发送" }).click();
  await page.getByText(adminMessage).waitFor({ timeout: WAIT_TIMEOUT_MS });

  const quoteNote = `浏览器 smoke 报价 ${Date.now()}`;
  await page.getByPlaceholder("报价金额").fill("188");
  await page.getByPlaceholder("报价说明").fill(quoteNote);
  await page.getByRole("button", { name: "发报价" }).click();
  await page.getByText(quoteNote).waitFor({ timeout: WAIT_TIMEOUT_MS });

  const paymentMethod = `浏览器 smoke 收款 ${Date.now()}`;
  await page.getByPlaceholder("收款金额").fill("88");
  await page.getByPlaceholder("收款方式").fill(paymentMethod);
  await page.getByRole("button", { name: "记收款" }).click();
  await page.getByText(paymentMethod).waitFor({ timeout: WAIT_TIMEOUT_MS });

  const deliverableTitle = `浏览器 smoke 交付物 ${Date.now()}`;
  await page.getByPlaceholder("交付物标题").fill(deliverableTitle);
  await page.getByPlaceholder("对象存储 key / 链接").fill(`orders/KULI-DEMO-001/${deliverableTitle}.txt`);
  await page.getByRole("button", { name: "登记交付" }).click();
  await page.getByText(deliverableTitle, { exact: true }).waitFor({ timeout: WAIT_TIMEOUT_MS });

  await page.setViewportSize({ width: 390, height: 844 });
  await checkPageMetrics(page, "/admin/orders/KULI-DEMO-001", "mobile-admin");
  await page.setViewportSize({ width: 1440, height: 980 });

  result.adminOk = true;
  result.adminDetailOk = true;
}

async function assertNoInternalText(page, label) {
  const text = await page.locator("body").innerText();
  assert(!text.includes("内部备注"), `${label} leaked internal note text`);
  assert(!text.includes("利润"), `${label} leaked profit text`);
  assert(!text.includes("成本"), `${label} leaked cost text`);
}

async function run() {
  await waitForHttp(`${API_BASE_URL}/api/health`, "Kuli API");
  await waitForHttp(BASE_URL, "Kuli web");

  const launchOptions = {
    headless: true,
    ...(chromePath ? { executablePath: chromePath } : { channel: process.env.PLAYWRIGHT_CHANNEL ?? "chrome" })
  };
  const browser = await chromium.launch(launchOptions);
  const context = await browser.newContext({ viewport: { width: 1440, height: 980 } });
  const page = await context.newPage();
  collectErrors(page);

  try {
    await clearBrowserState(page);
    await checkHealthDeps();
    await checkDocsGovernance();

    for (const path of ["/", "/services", "/services/ai-tools", "/help", "/help/quick-start", "/products", "/login"]) {
      await checkPageMetrics(page, path, "desktop");
    }

    await checkAuthGate(page);
    await checkProductsPage(page);
    await checkDocsCenter(page);
    await checkLegalAndUploadPolicy(page);
    await checkSeoAndGrowth(page);
    await checkXiaoku(page);
    await checkServiceNavigation(page);
    await checkNoteFlow(page);
    await checkAccountCenter(page);
    await checkMobileAccountNavigation(page);
    await checkUserOrders(page);

    await clearBrowserState(page);
    await page.setViewportSize({ width: 390, height: 844 });
    for (const path of ["/", "/services", "/services/ai-tools", "/help/quick-start", "/products", "/login", "/note", "/orders", "/admin"]) {
      await checkPageMetrics(page, path, "mobile");
    }

    await page.setViewportSize({ width: 1440, height: 980 });
    await checkAdminOrders(page);
    await checkNotificationCenter(page);

    assert(result.xiaokuOk, "Xiaoku panel check did not pass");
    assert(result.healthDepsOk, "Health dependency check did not pass");
    assert(result.docsGovernanceOk, "Docs governance check did not pass");
    assert(result.serviceOk, "Service navigation check did not pass");
    assert(result.noteOk, "Note submission check did not pass");
    assert(result.productsOk, "Products page check did not pass");
    assert(result.docsOk, "Docs center check did not pass");
    assert(result.legalOk, "Legal and upload policy check did not pass");
    assert(result.seoOk, "SEO and growth check did not pass");
    assert(result.authGateOk, "Auth gate check did not pass");
    assert(result.accountOk, "Account center check did not pass");
    assert(result.notificationsOk, "Notification center check did not pass");
    assert(result.mobileAccountOk, "Mobile account navigation check did not pass");
    assert(result.userOk, "User order check did not pass");
    assert(result.userDetailOk, "User order detail check did not pass");
    assert(result.adminOk, "Admin order check did not pass");
    assert(result.adminDetailOk, "Admin order detail check did not pass");
    assert(result.badMetrics.length === 0, `Bad page metrics:\n${result.badMetrics.join("\n")}`);
    assert(result.consoleErrors.length === 0, `Browser console errors:\n${result.consoleErrors.join("\n")}`);
    assert(result.pageErrors.length === 0, `Browser page errors:\n${result.pageErrors.join("\n")}`);
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify(result, null, 2));
}

run().catch((error) => {
  console.error(error);
  console.error(JSON.stringify(result, null, 2));
  process.exit(1);
});
