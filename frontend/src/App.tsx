import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, Navigate, NavLink, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  CreditCard,
  Eye,
  FileUp,
  LockKeyhole,
  LogOut,
  MessageCircle,
  PackageCheck,
  PenLine,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  UserRound
} from "lucide-react";
import { api, ApiError } from "./api";
import { useAuth } from "./auth";
import { cases, faqItems, serviceIconBySlug, services, statusLabels } from "./data";
import type { AdminOrder, NoteInput, Order, OrderStatus, ServiceCatalogItem } from "./types";

const emptyNote: NoteInput = {
  demand: "",
  category: "AI 工具",
  urgency: "1-2 天",
  budget: "50-100",
  contact: "",
  remoteHelp: "看情况，需要的时候再说",
  attachments: []
};

export function App() {
  return <Layout />;
}

function Layout() {
  const { user, logout } = useAuth();
  return (
    <>
      <header className="topbar">
        <div className="shell nav">
          <Link className="brand" to="/" aria-label="酷里小窗口首页">
            <span className="mark">K</span>
            <span className="brand-name">
              <strong>酷里 Kuli</strong>
              <span>酷里小窗口</span>
            </span>
          </Link>
          <nav className="navlinks" aria-label="主导航">
            <NavLink to="/">首页</NavLink>
            <NavLink to="/services">能做什么</NavLink>
            <NavLink to="/how-it-works">怎么合作</NavLink>
            <NavLink to="/rules">边界规则</NavLink>
            <NavLink to="/note">写小纸条</NavLink>
            <NavLink to="/orders">我的订单</NavLink>
            {user?.role === "admin" ? <NavLink to="/admin">管理后台</NavLink> : null}
            <NavLink to="/projects">子产品</NavLink>
          </nav>
          <div className="nav-actions">
            {user ? (
              <>
                <span className="user-pill">{user.role === "admin" ? "管理员" : "一般账号"} · {user.displayName}</span>
                <button className="icon-button" type="button" onClick={logout} aria-label="退出登录">
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <Link className="button secondary compact" to="/login">
                <LockKeyhole size={17} />
                登录
              </Link>
            )}
            <Link className="button compact" to="/note">
              <PenLine size={17} />
              写小纸条
            </Link>
          </div>
        </div>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/services" element={<ServicesPage />} />
          <Route path="/services/:slug" element={<ServiceDetailPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
          <Route path="/rules" element={<RulesPage />} />
          <Route path="/note" element={<NotePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/orders"
            element={
              <RequireAuth>
                <OrdersPage />
              </RequireAuth>
            }
          />
          <Route
            path="/admin"
            element={
              <RequireAuth role="admin">
                <AdminPage />
              </RequireAuth>
            }
          />
          <Route path="/projects" element={<ProjectPortalPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="shell mini-footer">酷里 Kuli · 不保证什么都能做，但能试的我们都会先试试。</footer>
      <div className="mobile-cta">
        <Link className="button" to="/note">
          丢张小纸条给酷里看看
        </Link>
      </div>
    </>
  );
}

function RequireAuth({ children, role }: { children: React.ReactElement; role?: "admin" }) {
  const { user, ready } = useAuth();
  const location = useLocation();
  if (!ready) return <LoadingBlock text="正在确认登录状态" />;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />;
  if (role && user.role !== role) return <Navigate to="/orders" replace />;
  return children;
}

function HomePage() {
  return (
    <>
      <section className="shell hero">
        <div>
          <p className="eyebrow">AI 创客小队 · 小需求急救</p>
          <h1>
            搞不动？先丢给<em>酷里</em>看看。
          </h1>
          <p className="lead">
            文件处理不了、AI 工具不会配置、账号订阅不会开通、小程序网页想做 demo、服务器部署卡住，都可以先从一张小纸条开始。
          </p>
          <div className="hero-actions">
            <Link className="button" to="/note">
              丢张小纸条给酷里看看 <ArrowRight size={18} />
            </Link>
            <Link className="button secondary" to="/services">
              看看能帮什么
            </Link>
          </div>
        </div>
        <div className="panel window chat-window">
          <div className="window-bar"><span className="dot red" /><span className="dot yellow" /><span className="dot green" /><span>$ kuli ask</span></div>
          <div className="chat-row me"><div className="bubble">我想开 GPT Pro，但不知道怎么弄。</div></div>
          <div className="chat-row"><span className="avatar">K</span><div className="bubble">先把你在哪、用什么账号、方便怎么付说一下就好；小活确认能做，做好你看过再结。</div></div>
          <div className="chat-row me"><div className="bubble">还有一个 PDF 想翻译，格式不要乱。</div></div>
          <div className="chat-row"><span className="avatar">K</span><div className="bubble">把文件和目标语言一起丢过来，我们先判断工作量。</div></div>
          <p className="sketch">直接截图：我现在卡在这里</p>
        </div>
      </section>

      <section className="shell section">
        <SectionHead title="最近大家问得最多的，都在这了。" description="不是标准商品列表，更像一扇小窗口：先说问题，酷里判断能不能做、怎么做、多少钱。" />
        <div className="grid cards-grid">
          {services.slice(0, 6).map((service, index) => {
            const Icon = service.icon;
            return (
              <article className={`card service-card ${index === 0 ? "featured" : ""}`} key={service.title}>
                <div className="iconbox"><Icon size={24} /></div>
                <div>
                  <span className="tag">{service.tag}</span>
                  <h3>{service.title}</h3>
                  <p>{service.description}</p>
                </div>
                <Link className="chip" to={`/services/${service.slug}`}>
                  点进去 <ArrowRight size={15} />
                </Link>
              </article>
            );
          })}
        </div>
      </section>

      <section className="shell section">
        <SectionHead title="酷里怎么做" description="流程尽量轻，不把一次临时求助变成复杂项目。" />
        <div className="process-strip">
          {["你先说需求", "酷里判断能不能做", "小需求验收后付款", "复杂需求先定金"].map((item, index) => (
            <article className="card process-card" key={item}>
              <span className="step-num">{index + 1}</span>
              <h3>{item}</h3>
              <p>{index === 0 ? "写几句话、发截图或文件，告诉我们你想解决什么。" : index === 1 ? "评估可行性、工作量、风险和大致报价。" : index === 2 ? "能快速交付的任务，确认效果后再付款。" : "需要开发、部署或多轮沟通时，可能先收一部分定金。"}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="shell section">
        <SectionHead title="正式接单前，先把边界说清楚。" description="酷里更适合轻量、临时、可拆的小需求；不靠万能承诺成交。" />
        <div className="grid cards-grid">
          {[
            ["怎么判断能不能做", "先看目标、材料、账号/环境权限、截止时间和风险；不确定就先拆成最小验证。"],
            ["交易规则", "小需求可以验收后付款；开发、部署、多轮排查等复杂活会先报价和收定金。"],
            ["售后边界", "交付时说明已完成范围；环境变化、二次修改、长期维护默认作为新需求。"],
            ["为什么先写小纸条", "一句话、截图、文件都行。先让酷里判断分类和材料，不用一上来写正式需求书。"],
            ["常见案例", "PDF 翻译保排版、AI/API 配置、网页 demo、服务器部署、小脚本自动化。"],
            ["不接什么", "违法违规、盗号破解、绕过安全限制、批量滥用平台和风险不可控的需求不接。"]
          ].map(([title, description]) => (
            <article className="card trust-card" key={title}>
              <CheckCircle2 size={20} />
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function ServicesPage() {
  const [filter, setFilter] = useState("all");
  const visibleFaq = filter === "all" ? faqItems : faqItems.filter(([topic]) => topic === filter);
  return (
    <>
      <section className="shell page-hero">
        <p className="eyebrow">能做什么 / 怎么帮我</p>
        <h1 className="mega">不是万能客服，是一支会先帮你<em>拆问题</em>的小队。</h1>
        <p className="lead">遇到临时卡住的小事，可以先丢给酷里看看。能说明白最好；说不清也没关系，我们会帮你把关键点一点点问出来。</p>
      </section>

      <section className="shell section">
        <SectionHead title="酷里可以帮你的事" description="不用先分得很准，先把卡住的地方发来，酷里会帮你判断下一步。" />
        <div className="grid cards-grid">
          {services.map((service) => {
            const Icon = service.icon;
            return (
              <article className="card service-card" key={service.title}>
                <div className="iconbox"><Icon size={24} /></div>
                <div>
                  <span className="tag">{service.tag}</span>
                  <h3>{service.title}</h3>
                  <p>{service.description}</p>
                </div>
                <Link className="chip" to={`/services/${service.slug}`}>查看详情 <ArrowRight size={15} /></Link>
              </article>
            );
          })}
        </div>
      </section>

      <section className="shell section">
        <SectionHead title="几个常见小活样子" description="这些是判断参考，不是固定商品。酷里会先看你的具体情况。" />
        <div className="grid cards-grid">
          {cases.map(([tag, title, description]) => (
            <article className="card case-card" key={title}>
              <span className="tag">{tag}</span>
              <h3>{title}</h3>
              <p>{description}</p>
              <Link className="chip" to="/note">先问问 <ArrowRight size={15} /></Link>
            </article>
          ))}
        </div>
      </section>

      <section className="shell section split-band">
        <article className="panel window quote-panel">
          <div className="window-bar"><span className="dot red" /><span className="dot yellow" /><span className="dot green" /><span>rule.note</span></div>
          <blockquote>小需求可以验收后付款；复杂需求先收定金。</blockquote>
          <cite>默认不包长期售后，后续维护、部署、修改另算。</cite>
        </article>
        <table className="price-table" aria-label="结算方式说明">
          <thead><tr><th>情况</th><th>怎么结算</th><th>适合例子</th></tr></thead>
          <tbody>
            <tr><td>小需求</td><td>验收后付款</td><td>PDF 处理、配置指导、简单脚本、轻量页面修改</td></tr>
            <tr><td>复杂需求</td><td>先付定金，节点验收</td><td>网页 demo、部署上线、远程排查、多轮修改</td></tr>
            <tr><td>后续维护</td><td>作为新需求另算</td><td>功能新增、环境迁移、二次部署、长期托管</td></tr>
          </tbody>
        </table>
      </section>

      <section className="shell section">
        <SectionHead title="常见问题" description="点分类过滤，先把付款、范围、交付和风险看清楚。" />
        <div className="faq-tools" aria-label="FAQ 分类过滤">
          {[
            ["all", "全部"],
            ["payment", "付款"],
            ["scope", "范围"],
            ["delivery", "交付"],
            ["risk", "风险"]
          ].map(([key, label]) => (
            <button className={`faq-filter ${filter === key ? "is-active" : ""}`} type="button" onClick={() => setFilter(key)} key={key}>
              {label}
            </button>
          ))}
        </div>
        <div className="faq-list">
          {visibleFaq.map(([, question, answer]) => (
            <details className="faq-item" key={question} open>
              <summary>{question}</summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
      </section>
    </>
  );
}

function HowItWorksPage() {
  return (
    <>
      <section className="shell page-hero">
        <p className="eyebrow">怎么合作</p>
        <h1 className="mega">先把烦恼丢过来，再决定要不要做成订单。</h1>
        <p className="lead">小纸条不是付款入口，而是问题入口。咨询、判断、拆范围可以先发生；确认需要交付、排查或制作时，再进入报价和节点管理。</p>
      </section>
      <section className="shell section">
        <div className="grid cards-grid">
          {[
            ["1. 写小纸条", "可以是一句话、截图、文件或“不知道怎么说”。系统会引导你补材料，也可以先让 AI 帮你润色。"],
            ["2. 酷里读原话", "管理员会看到你的原始描述、附件和 agent 整理，不会只看自动摘要。"],
            ["3. 免费判断", "咨询类、能不能做、需要什么材料，先判断；不代表每张纸条都会收费。"],
            ["4. 报价与节点", "需要交付时才报价。复杂需求可以定金、尾款、交付物和验收分开管理。"],
            ["5. 持续沟通", "订单里可以补充消息和附件，管理员能实时看到新纸条和新材料。"],
            ["6. 交付验收", "交付物上传后进入待验收，你确认效果后订单完成。"]
          ].map(([title, description]) => (
            <article className="card trust-card" key={title}>
              <CheckCircle2 size={20} />
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function RulesPage() {
  return (
    <>
      <section className="shell page-hero">
        <p className="eyebrow">边界规则</p>
        <h1 className="mega">不把“试试看”包装成万能承诺。</h1>
        <p className="lead">酷里可以接通用任务，也会认真看模糊需求；但账号风险、平台规则、文件质量、违法违规和长期维护边界要提前说清楚。</p>
      </section>
      <section className="shell section split-band">
        <article className="panel service-block">
          <h2>可以先免费判断</h2>
          <ul className="check-list">
            <li><CheckCircle2 size={17} /> 需求属于哪一类、材料够不够。</li>
            <li><CheckCircle2 size={17} /> 大概能不能做、风险在哪里。</li>
            <li><CheckCircle2 size={17} /> 是否需要报价、定金或分节点。</li>
          </ul>
        </article>
        <article className="panel service-block">
          <h2>不会接的事</h2>
          <ul className="check-list">
            <li><CheckCircle2 size={17} /> 盗号、破解、绕过安全限制。</li>
            <li><CheckCircle2 size={17} /> 批量滥用平台或明显违规用途。</li>
            <li><CheckCircle2 size={17} /> 风险不可控却要求保证结果。</li>
          </ul>
        </article>
      </section>
    </>
  );
}

function ServiceDetailPage() {
  const { slug = "" } = useParams();
  const [service, setService] = useState<ServiceCatalogItem | null>(null);
  const [error, setError] = useState("");
  const fallback = services.find((item) => item.slug === slug);
  const Icon = (slug && serviceIconBySlug[slug]) || (fallback?.icon ?? ClipboardList);

  useEffect(() => {
    let cancelled = false;
    api
      .getService(slug)
      .then((result) => {
        if (!cancelled) setService(result.service);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "服务详情加载失败");
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (error) {
    return (
      <section className="shell section">
        <EmptyPanel text={error} />
      </section>
    );
  }
  if (!service) return <LoadingBlock text="正在打开服务详情" />;

  return (
    <>
      <section className="shell service-hero">
        <div>
          <p className="eyebrow">{service.tag} / 服务详情</p>
          <h1 className="mega">{service.title}</h1>
          <p className="lead">{service.summary}</p>
          <div className="hero-actions">
            <Link className="button" to={`/note?service=${service.slug}`}>
              带着这个需求写小纸条 <ArrowRight size={18} />
            </Link>
            <Link className="button secondary" to="/services">
              返回服务列表
            </Link>
          </div>
        </div>
        <article className="panel service-snapshot">
          <div className="iconbox"><Icon size={26} /></div>
          <Info label="价格参考" value={service.priceRange} />
          <Info label="周期参考" value={service.timeline} />
          <Info label="下单建议" value="材料越具体，报价越准" />
        </article>
      </section>

      <section className="shell section service-detail-grid">
        <DetailBlock title="适合人群" items={service.audience} />
        <DetailBlock title="常见需求" items={service.commonNeeds} />
        <DetailBlock title="能交付什么" items={service.deliverables} />
        <DetailBlock title="你需要准备" items={service.requiredMaterials} />
        <DetailBlock title="风险边界" items={service.risks} wide />
        <article className="panel service-block wide">
          <h2>案例参考</h2>
          <div className="mini-grid">
            {service.cases.map((item) => (
              <div className="mini-card" key={item.title}>
                <strong>{item.title}</strong>
                <p>{item.description}</p>
              </div>
            ))}
          </div>
        </article>
        <article className="panel service-block wide">
          <h2>FAQ</h2>
          <div className="faq-list">
            {service.faq.map((item) => (
              <details className="faq-item" key={item.question} open>
                <summary>{item.question}</summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </article>
      </section>
    </>
  );
}

function DetailBlock({ title, items, wide = false }: { title: string; items: string[]; wide?: boolean }) {
  return (
    <article className={`panel service-block ${wide ? "wide" : ""}`}>
      <h2>{title}</h2>
      <ul className="check-list">
        {items.map((item) => (
          <li key={item}><CheckCircle2 size={17} /> {item}</li>
        ))}
      </ul>
    </article>
  );
}

function NotePage() {
  const { user, token } = useAuth();
  const location = useLocation();
  const selectedSlug = new URLSearchParams(location.search).get("service") ?? undefined;
  const [selectedService, setSelectedService] = useState<ServiceCatalogItem | null>(null);
  const [form, setForm] = useState<NoteInput>(() => noteForService(selectedSlug));
  const [status, setStatus] = useState<{ type: "error" | "success"; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [polishing, setPolishing] = useState(false);
  const [polishHints, setPolishHints] = useState<string[]>([]);

  useEffect(() => {
    setForm(noteForService(selectedSlug));
    setSelectedService(null);
    if (!selectedSlug) return;
    let cancelled = false;
    api
      .getService(selectedSlug)
      .then((result) => {
        if (!cancelled) setSelectedService(result.service);
      })
      .catch(() => {
        if (!cancelled) setSelectedService(null);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedSlug]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setStatus(null);
    if (!form.demand.trim() || !form.contact.trim()) {
      setStatus({ type: "error", text: "还差一点：请写下需求和联系方式，酷里才知道怎么回你。" });
      return;
    }
    setSubmitting(true);
    try {
      const result = token ? await api.createOrder(form, token) : await api.createPublicInquiry(form);
      setStatus({
        type: "success",
        text: token
          ? `订单 ${result.order.orderNumber} 已创建，可以在“我的订单”里查看进度。`
          : `小纸条 ${result.order.orderNumber} 已投递。登录后创建的订单才能自动追踪进度。`
      });
      setForm(noteForService(selectedSlug));
    } catch (error) {
      setStatus({ type: "error", text: error instanceof ApiError ? error.message : "提交失败，请稍后再试。" });
    } finally {
      setSubmitting(false);
    }
  }

  async function polish() {
    if (!form.demand.trim()) {
      setStatus({ type: "error", text: "先随便写一点原始想法，AI 才能帮你润色。" });
      return;
    }
    setPolishing(true);
    setStatus(null);
    try {
      const result = await api.polishDemand({ demand: form.demand, serviceSlug: form.serviceSlug });
      setForm({ ...form, originalDemand: form.originalDemand ?? form.demand, demand: result.polishedDemand });
      setPolishHints(result.hints);
      setStatus({ type: "success", text: "AI 已帮你整理成更适合酷里判断的描述，你仍然可以继续改。" });
    } catch (error) {
      setStatus({ type: "error", text: error instanceof ApiError ? error.message : "AI 润色失败，请先按原话提交。" });
    } finally {
      setPolishing(false);
    }
  }

  async function addFiles(fileList: FileList | null) {
    if (!fileList) return;
    const files = await Promise.all(Array.from(fileList).slice(0, 8).map(readFileForNote));
    setForm({ ...form, attachments: [...(form.attachments ?? []), ...files] });
  }

  return (
    <>
      <section className="shell page-hero">
        <p className="eyebrow">写张小纸条</p>
        <h1 className="mega">不用写得专业，先把卡住的地方<em>丢过来</em>。</h1>
        <p className="lead">酷里会先判断能不能做、需不需要更多材料、是验收后付款还是先付定金。{user ? `当前以 ${user.email} 提交，可追踪进度。` : "游客也能先投递；登录后创建的订单可追踪进度。"}</p>
      </section>
      <section className="shell section two-col">
        <aside className="panel window">
          <div className="window-bar"><span className="dot red" /><span className="dot yellow" /><span className="dot green" /><span>tips.txt</span></div>
          <div className="sticky-note">
            <strong>可以这样写</strong>
            {selectedService ? (
              <>
                “我想做：{selectedService.commonNeeds[0]}。”<br />
                “我能提供：{selectedService.requiredMaterials.slice(0, 2).join("、")}。”<br />
                “期望：{selectedService.timeline}，预算先按 {selectedService.priceRange} 聊。”
              </>
            ) : (
              <>
                “我想开通 Google Pro，但是不会弄。”<br />
                “PDF 需要翻译，还要保持排版。”<br />
                “我现在卡在这里。”然后直接配一张截图。
              </>
            )}
          </div>
          <div className="notice">
            <CheckCircle2 size={20} />
            <span>小活可以先做完再结；大一点的活可能要先付定金。默认不包长期售后。</span>
          </div>
        </aside>
        <form className="panel form-panel" onSubmit={submit}>
          {selectedService ? (
            <div className="service-hint">
              <span className="tag">已带入：{selectedService.title}</span>
              <strong>这类需求最好先补齐材料、截止时间和风险接受度。</strong>
            </div>
          ) : null}
          <Field label="1. 你想搞定什么？">
            <textarea value={form.demand} maxLength={800} placeholder="例如：我想开通 GPT Pro，但是不会弄；我有一个 PDF 想翻译并保留格式；我想做一个小程序 / 网页 demo。" onChange={(event) => setForm({ ...form, demand: event.target.value })} />
            <small>{form.demand.length} / 800</small>
          </Field>
          <div className="note-assist-row">
            <button className="button compact secondary" type="button" onClick={polish} disabled={polishing}>
              {polishing ? "润色中..." : "让 AI 帮我润色需求"}
            </button>
            <span>保留你的原话思路，只把目标、材料、截止时间和待确认点整理清楚。</span>
          </div>
          {polishHints.length ? (
            <div className="hint-list">
              {polishHints.map((hint) => <span key={hint}>{hint}</span>)}
            </div>
          ) : null}
          <ChoiceField label="2. 大概属于哪一类？" name="category" value={form.category} options={services.map((service) => service.tag)} onChange={(category) => setForm({ ...form, category, serviceSlug: services.find((service) => service.tag === category)?.slug })} />
          <ChoiceField label="3. 什么时候需要？" name="urgency" value={form.urgency} options={["今天", "1-2 天", "3-5 天", "不急", "先聊聊"]} onChange={(urgency) => setForm({ ...form, urgency })} />
          <ChoiceField label="4. 预算大概多少？" name="budget" value={form.budget} options={["50 元以内", "50-100", "100-300", "300-1000", "先报价看看"]} onChange={(budget) => setForm({ ...form, budget })} />
          <ChoiceField label="5. 能不能远程协助？" name="remoteHelp" value={form.remoteHelp} options={["可以远程，方便你们直接帮我看", "暂时不方便，先文字或截图沟通", "看情况，需要的时候再说"]} onChange={(remoteHelp) => setForm({ ...form, remoteHelp })} />
          <Field label="6. 怎么联系你？">
            <input value={form.contact} placeholder="微信 / QQ / 邮箱都可以" onChange={(event) => setForm({ ...form, contact: event.target.value })} />
            <small>只用于沟通，不会对外公开。</small>
          </Field>
          <Field label="7. 有文件就一起丢上来">
            <input type="file" multiple accept=".xlsx,.xls,.csv,.doc,.docx,.pdf,.ppt,.pptx,image/*" onChange={(event) => addFiles(event.currentTarget.files)} />
            <small>支持 Excel、Word、PDF、PPT、图片和截图；这里只做本地对象存储 fallback，管理员能看到附件 key。</small>
          </Field>
          {form.attachments?.length ? (
            <div className="upload-list">
              {form.attachments.map((file) => (
                <div className="record-row" key={`${file.fileName}-${file.fileSize}`}>
                  {file.fileName} · {Math.max(1, Math.round(file.fileSize / 1024))}KB · {file.contentType}
                </div>
              ))}
              <button className="chip" type="button" onClick={() => setForm({ ...form, attachments: [] })}>清空附件</button>
            </div>
          ) : null}
          {status ? <div className={`status-box is-visible ${status.type}`}>{status.text}</div> : null}
          <button className="button full" type="submit" disabled={submitting}>{submitting ? "投递中..." : "把小纸条丢给酷里"}</button>
        </form>
      </section>
    </>
  );
}

function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const next = new URLSearchParams(location.search).get("next") ?? "/orders";
  const [mode, setMode] = useState<"login" | "register">("login");
  const [displayName, setDisplayName] = useState("酷里朋友");
  const [email, setEmail] = useState("demo@kuli.local");
  const [password, setPassword] = useState("KuliUser123!");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const user = mode === "login" ? await login(email, password) : await register(displayName, email, password);
      navigate(user.role === "admin" ? "/admin" : next, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "登录失败");
    }
  }

  return (
    <section className="shell section auth-page">
      <div className="panel form-panel auth-card">
        <p className="eyebrow"><LockKeyhole size={16} /> 邮箱密码登录</p>
        <h1 className="compact-title">{mode === "login" ? "回到你的酷里窗口。" : "创建一个一般账号。"}</h1>
        <p className="muted">Demo 管理员：admin@kuli.local / KuliAdmin123!；一般账号：demo@kuli.local / KuliUser123!</p>
        <div className="segmented">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>登录</button>
          <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>注册一般账号</button>
        </div>
        <form onSubmit={submit}>
          {mode === "register" ? <Field label="昵称"><input value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></Field> : null}
          <Field label="邮箱"><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></Field>
          <Field label="密码"><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></Field>
          {error ? <div className="status-box is-visible error">{error}</div> : null}
          <button className="button full" type="submit">{mode === "login" ? "登录" : "创建账号"}</button>
        </form>
      </div>
    </section>
  );
}

function OrdersPage() {
  const { token } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [selected, setSelected] = useState<Order | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api
      .listOrders(token)
      .then((result) => {
        setOrders(result.orders);
        setSelected(result.orders[0] ?? null);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "订单加载失败"));
  }, [token]);

  function mergeOrder(order: Order) {
    setSelected(order);
    setOrders((items) => items.map((item) => (item.orderNumber === order.orderNumber ? order : item)));
  }

  return (
    <section className="shell section dashboard">
      <DashboardHeader title="我的订单" description="这里只能看到你自己的订单进度、报价和公开沟通信息。" icon={<UserRound />} />
      {error ? <div className="status-box is-visible error">{error}</div> : null}
      <div className="dashboard-grid">
        <OrderList orders={orders} selected={selected?.orderNumber} onSelect={setSelected} />
        <OrderDetail order={selected} token={token} onOrderChange={mergeOrder} />
      </div>
    </section>
  );
}

function AdminPage() {
  const { token } = useAuth();
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [selected, setSelected] = useState<AdminOrder | null>(null);
  const [message, setMessage] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  async function load() {
    if (!token) return;
    const result = await api.listAdminOrders(token);
    setOrders(result.orders);
    setSelected((current) => result.orders.find((order) => order.orderNumber === current?.orderNumber) ?? result.orders[0] ?? null);
  }

  useEffect(() => {
    load().catch((error) => setMessage(error instanceof ApiError ? error.message : "后台加载失败"));
    const timer = window.setInterval(() => {
      load().catch((error) => setMessage(error instanceof ApiError ? error.message : "后台刷新失败"));
    }, 5000);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function save(patch: Partial<AdminOrder>) {
    if (!token || !selected) return;
    const result = await api.updateAdminOrder(token, selected.orderNumber, patch);
    setSelected(result.order);
    setOrders((items) => items.map((item) => (item.orderNumber === result.order.orderNumber ? result.order : item)));
    setMessage(`订单 ${result.order.orderNumber} 已更新`);
  }

  function mergeAdminOrder(order: AdminOrder, text: string) {
    setSelected(order);
    setOrders((items) => items.map((item) => (item.orderNumber === order.orderNumber ? order : item)));
    setMessage(text);
  }

  async function createQuote(input: { amount: number; kind: string; note: string }) {
    if (!token || !selected) return;
    const result = await api.createQuote(token, selected.orderNumber, input);
    mergeAdminOrder(result.order, "报价已发送");
  }

  async function createPayment(input: { amount: number; kind: string; method: string; status: string; note: string }) {
    if (!token || !selected) return;
    const result = await api.createPayment(token, selected.orderNumber, input);
    mergeAdminOrder(result.order, "付款记录已保存");
  }

  async function createDeliverable(input: { title: string; description: string; storageKey: string }) {
    if (!token || !selected) return;
    const result = await api.createDeliverable(token, selected.orderNumber, input);
    mergeAdminOrder(result.order, "交付物已记录");
  }

  async function updateStatus(input: { status: OrderStatus; publicNotes?: string; internalNotes?: string }) {
    if (!token || !selected) return;
    const result = await api.updateAdminOrderStatus(token, selected.orderNumber, input);
    mergeAdminOrder(result.order, "状态已更新");
  }

  const stats = useMemo(() => {
    return {
      total: orders.length,
      active: orders.filter((order) => order.status !== "completed").length,
      publicInquiries: orders.filter((order) => !order.ownerEmail).length,
      completed: orders.filter((order) => order.status === "completed").length
    };
  }, [orders]);

  const visibleOrders = useMemo(() => {
    return statusFilter === "all" ? orders : orders.filter((order) => order.status === statusFilter);
  }, [orders, statusFilter]);

  return (
    <section className="shell section dashboard">
      <DashboardHeader title="管理后台" description="管理员账号可以查看全部订单和内部经营字段。" icon={<ShieldCheck />} />
      <div className="stat-grid">
        <Stat label="全部订单" value={stats.total} />
        <Stat label="进行中" value={stats.active} />
        <Stat label="游客小纸条" value={stats.publicInquiries} />
        <Stat label="已完成" value={stats.completed} />
      </div>
      {message ? <div className="status-box is-visible">{message}</div> : null}
      <div className="faq-tools" aria-label="订单状态筛选">
        {["all", ...Object.keys(statusLabels)].map((key) => (
          <button className={`faq-filter ${statusFilter === key ? "is-active" : ""}`} type="button" key={key} onClick={() => setStatusFilter(key)}>
            {key === "all" ? "全部" : statusLabels[key]?.label ?? key}
          </button>
        ))}
      </div>
      <div className="dashboard-grid">
        <OrderList orders={visibleOrders} selected={selected?.orderNumber} onSelect={(order) => setSelected(order as AdminOrder)} admin />
        <AdminEditor order={selected} onSave={save} onQuote={createQuote} onPayment={createPayment} onDeliverable={createDeliverable} onStatus={updateStatus} />
      </div>
    </section>
  );
}

function ProjectPortalPage() {
  return (
    <section className="shell section two-col">
      <div>
        <p className="eyebrow">子产品 / 项目管理</p>
        <h1 className="mega">这里先留一个<em>入口</em>。</h1>
        <p className="lead">后续官网可能会管理本机其他子项目，但当前版本不会读取、扫描或展示任何真实目录。</p>
        <Link className="button" to="/note">有类似需求先写小纸条</Link>
      </div>
      <article className="panel window">
        <div className="window-bar"><span className="dot red" /><span className="dot yellow" /><span className="dot green" /><span>projects.locked</span></div>
        <div className="placeholder-lock"><LockKeyhole size={42} /><strong>未接入项目管理</strong><span>管理员也暂时没有子项目管理权限。</span></div>
      </article>
    </section>
  );
}

function AdminEditor({
  order,
  onSave,
  onQuote,
  onPayment,
  onDeliverable,
  onStatus
}: {
  order: AdminOrder | null;
  onSave: (patch: Partial<AdminOrder>) => Promise<void>;
  onQuote: (input: { amount: number; kind: string; note: string }) => Promise<void>;
  onPayment: (input: { amount: number; kind: string; method: string; status: string; note: string }) => Promise<void>;
  onDeliverable: (input: { title: string; description: string; storageKey: string }) => Promise<void>;
  onStatus: (input: { status: OrderStatus; publicNotes?: string; internalNotes?: string }) => Promise<void>;
}) {
  const [draft, setDraft] = useState<Partial<AdminOrder>>({});
  const [quote, setQuote] = useState({ amount: "0", kind: "full", note: "" });
  const [payment, setPayment] = useState({ amount: "0", kind: "deposit", method: "微信", status: "received", note: "" });
  const [deliverable, setDeliverable] = useState({ title: "", description: "", storageKey: "" });
  useEffect(() => {
    setDraft(order ?? {});
    setQuote({ amount: String(order?.quotedPrice ?? 0), kind: "full", note: "" });
    setPayment({ amount: "0", kind: "deposit", method: "微信", status: "received", note: "" });
    setDeliverable({ title: "", description: "", storageKey: order ? `deliverables/${order.orderNumber}/` : "" });
  }, [order]);
  if (!order) return <EmptyPanel text="还没有订单。" />;
  return (
    <article className="panel detail-panel">
      <div className="detail-head">
        <div>
          <span className="tag">{order.ownerEmail ? "一般账号订单" : "游客小纸条"}</span>
          <h2>{order.title}</h2>
          <p>{order.orderNumber} · {order.contact} · {order.serviceSlug}</p>
        </div>
        <button className="button compact" type="button" onClick={() => onSave(draft)}>保存</button>
      </div>
      <div className="agent-grid">
        <section className="record-panel">
          <div className="panel-title"><MessageCircle size={18} /> 用户原话</div>
          <p className="raw-demand">{order.originalDemand}</p>
        </section>
        <section className="record-panel agent-panel">
          <div className="panel-title"><Sparkles size={18} /> Agent 需求整理</div>
          <p>{order.agentBrief.summary}</p>
          <div className="hint-list">
            {order.agentBrief.tags.map((tag) => <span key={tag}>{tag}</span>)}
            <span>{order.agentBrief.consultationFirst ? "先咨询/先判断" : "可进入报价"}</span>
          </div>
          <strong>{order.agentBrief.chargeHint}</strong>
          <ul className="question-list">
            {order.agentBrief.suggestedQuestions.map((question) => <li key={question}>{question}</li>)}
          </ul>
        </section>
      </div>
      <div className="form-grid">
        <label>状态<select value={draft.status ?? order.status} onChange={(e) => setDraft({ ...draft, status: e.target.value as OrderStatus })}>{Object.entries(statusLabels).map(([key, value]) => <option key={key} value={key}>{value.label}</option>)}</select></label>
        <label>优先级<select value={draft.priority ?? order.priority} onChange={(e) => setDraft({ ...draft, priority: e.target.value as AdminOrder["priority"] })}><option value="low">低</option><option value="normal">普通</option><option value="high">高</option><option value="urgent">紧急</option></select></label>
        <label>开价<input type="number" value={draft.quotedPrice ?? ""} onChange={(e) => setDraft({ ...draft, quotedPrice: numberOrNull(e.target.value) })} /></label>
        <label>成本<input type="number" value={draft.cost ?? ""} onChange={(e) => setDraft({ ...draft, cost: numberOrNull(e.target.value) })} /></label>
        <label>利润<input type="number" value={draft.profit ?? ""} onChange={(e) => setDraft({ ...draft, profit: numberOrNull(e.target.value) })} /></label>
      </div>
      <label className="stacked">公开备注<textarea value={draft.publicNotes ?? ""} onChange={(e) => setDraft({ ...draft, publicNotes: e.target.value })} /></label>
      <label className="stacked">内部备注<textarea value={draft.internalNotes ?? ""} onChange={(e) => setDraft({ ...draft, internalNotes: e.target.value })} /></label>
      <OrderProgress status={order.status} />
      <div className="admin-workbench">
        <form className="mini-form" onSubmit={(event) => { event.preventDefault(); onQuote({ amount: Number(quote.amount), kind: quote.kind, note: quote.note || "管理员报价" }); }}>
          <h3>发报价</h3>
          <input type="number" min="0" value={quote.amount} onChange={(event) => setQuote({ ...quote, amount: event.target.value })} />
          <select value={quote.kind} onChange={(event) => setQuote({ ...quote, kind: event.target.value })}><option value="full">全款</option><option value="deposit">定金</option><option value="final">尾款</option><option value="change">变更</option><option value="other">其他</option></select>
          <textarea value={quote.note} placeholder="报价说明" onChange={(event) => setQuote({ ...quote, note: event.target.value })} />
          <button className="button compact" type="submit">发送报价</button>
        </form>
        <form className="mini-form" onSubmit={(event) => { event.preventDefault(); onPayment({ amount: Number(payment.amount), kind: payment.kind, method: payment.method, status: payment.status, note: payment.note }); }}>
          <h3>记付款</h3>
          <input type="number" min="0" value={payment.amount} onChange={(event) => setPayment({ ...payment, amount: event.target.value })} />
          <select value={payment.kind} onChange={(event) => setPayment({ ...payment, kind: event.target.value })}><option value="deposit">定金</option><option value="final">尾款</option><option value="full">全款</option><option value="refund">退款</option><option value="other">其他</option></select>
          <select value={payment.status} onChange={(event) => setPayment({ ...payment, status: event.target.value })}><option value="received">已收</option><option value="pending">待确认</option><option value="failed">失败</option><option value="refunded">已退</option></select>
          <input value={payment.method} onChange={(event) => setPayment({ ...payment, method: event.target.value })} />
          <textarea value={payment.note} placeholder="凭证备注" onChange={(event) => setPayment({ ...payment, note: event.target.value })} />
          <button className="button compact secondary" type="submit">保存付款</button>
        </form>
        <form className="mini-form" onSubmit={(event) => { event.preventDefault(); onDeliverable(deliverable); }}>
          <h3>交付物</h3>
          <input value={deliverable.title} placeholder="交付物标题" onChange={(event) => setDeliverable({ ...deliverable, title: event.target.value })} />
          <input value={deliverable.storageKey} placeholder="对象存储 key" onChange={(event) => setDeliverable({ ...deliverable, storageKey: event.target.value })} />
          <textarea value={deliverable.description} placeholder="交付说明" onChange={(event) => setDeliverable({ ...deliverable, description: event.target.value })} />
          <button className="button compact secondary" type="submit">记录交付</button>
        </form>
        <form className="mini-form" onSubmit={(event) => { event.preventDefault(); onStatus({ status: (draft.status ?? order.status) as OrderStatus, publicNotes: draft.publicNotes, internalNotes: draft.internalNotes }); }}>
          <h3>状态节点</h3>
          <select value={draft.status ?? order.status} onChange={(event) => setDraft({ ...draft, status: event.target.value as OrderStatus })}>{Object.entries(statusLabels).map(([key, value]) => <option key={key} value={key}>{value.label}</option>)}</select>
          <button className="button compact" type="submit">更新状态</button>
        </form>
      </div>
      <div className="workbench-grid">
        <Timeline events={order.events} />
        <RecordList title="报价" icon={<CreditCard size={18} />} empty="暂无报价" items={order.quotes.map((item) => `￥${item.amount} · ${item.kind} · ${item.createdByEmail ?? "管理员"} · ${item.note}`)} />
        <RecordList title="付款" icon={<CalendarDays size={18} />} empty="暂无付款" items={order.payments.map((item) => `￥${item.amount} · ${item.kind} · ${item.method} · ${item.status}`)} />
        <RecordList title="交付物" icon={<PackageCheck size={18} />} empty="暂无交付物" items={order.deliverables.map((item) => `${item.title} · ${item.storageKey}`)} />
        <RecordList title="客户沟通" icon={<MessageCircle size={18} />} empty="暂无沟通" items={order.messages.map((item) => `${item.authorEmail ?? "未知"}：${item.body}`)} />
        <RecordList title="附件" icon={<FileUp size={18} />} empty="暂无附件" items={order.attachments.map((item) => `${item.fileName} · ${item.storageKey}`)} />
      </div>
    </article>
  );
}

function OrderList({ orders, selected, onSelect, admin = false }: { orders: Order[]; selected?: string; onSelect: (order: Order) => void; admin?: boolean }) {
  return (
    <aside className="panel list-panel">
      <div className="panel-title"><ClipboardList size={18} /> 订单列表</div>
      {orders.length === 0 ? <EmptyPanel text="暂无订单，先写一张小纸条。" /> : null}
      {orders.map((order) => (
        <button className={`order-row ${selected === order.orderNumber ? "active" : ""}`} type="button" key={order.orderNumber} onClick={() => onSelect(order)}>
          <strong>{order.title}</strong>
          <span>{order.orderNumber} · {statusLabels[order.status]?.label ?? order.status}</span>
          <small>{admin ? order.ownerEmail ?? "游客小纸条" : order.publicNotes}</small>
        </button>
      ))}
    </aside>
  );
}

function OrderDetail({ order, token, onOrderChange }: { order: Order | null; token: string | null; onOrderChange: (order: Order) => void }) {
  const [message, setMessage] = useState("");
  const [attachment, setAttachment] = useState({ fileName: "", fileSize: "0", contentType: "application/pdf" });
  const [notice, setNotice] = useState("");
  if (!order) return <EmptyPanel text="选择一个订单查看进度。" />;
  const currentOrder = order;

  async function addMessage(event: FormEvent) {
    event.preventDefault();
    if (!token || !message.trim()) return;
    const result = await api.addOrderMessage(token, currentOrder.orderNumber, message.trim());
    onOrderChange(result.order);
    setMessage("");
    setNotice("补充信息已发送");
  }

  async function addAttachment(event: FormEvent) {
    event.preventDefault();
    if (!token || !attachment.fileName.trim()) return;
    const result = await api.addOrderAttachment(token, currentOrder.orderNumber, {
      fileName: attachment.fileName.trim(),
      fileSize: Number(attachment.fileSize) || 0,
      contentType: attachment.contentType.trim() || "application/octet-stream"
    });
    onOrderChange(result.order);
    setAttachment({ fileName: "", fileSize: "0", contentType: "application/pdf" });
    setNotice("附件记录已保存");
  }

  async function acceptOrder() {
    if (!token) return;
    const result = await api.acceptOrder(token, currentOrder.orderNumber, "客户已确认验收。");
    onOrderChange(result.order);
    setNotice("已确认验收，订单完成");
  }

  return (
    <article className="panel detail-panel">
      <div className="detail-head">
        <div>
          <span className="tag">{order.category}</span>
          <h2>{order.title}</h2>
          <p>{order.orderNumber} · 预算 {order.budget}</p>
        </div>
        <Link className="button compact secondary" to="/note">补充新需求</Link>
      </div>
      <OrderProgress status={order.status} />
      {notice ? <div className="status-box is-visible">{notice}</div> : null}
      <div className="info-grid">
        <Info label="当前报价" value={order.quotedPrice == null ? "待报价" : `￥${order.quotedPrice}`} />
        <Info label="期望时间" value={order.urgency} />
        <Info label="远程协助" value={order.remoteHelp} />
        <Info label="联系方式" value={order.contact} />
      </div>
      <div className="workbench-grid">
        <Timeline events={order.events} />
        <RecordList title="报价记录" icon={<CreditCard size={18} />} empty="还没有报价" items={order.quotes.map((item) => `￥${item.amount} · ${item.kind} · ${item.note}`)} />
        <RecordList title="付款记录" icon={<CalendarDays size={18} />} empty="还没有付款记录" items={order.payments.map((item) => `￥${item.amount} · ${item.kind} · ${item.method} · ${item.status}`)} />
        <RecordList title="交付物" icon={<PackageCheck size={18} />} empty="还没有交付物" items={order.deliverables.map((item) => `${item.title} · ${item.storageKey}`)} />
      </div>
      <div className="note-block">
        <MessageCircle size={18} />
        <div><strong>公开备注</strong><p>{order.publicNotes}</p></div>
      </div>
      <section className="customer-actions">
        <form className="inline-form" onSubmit={addMessage}>
          <label>补充沟通<textarea value={message} placeholder="补充材料、反馈修改意见、说明验收情况。" onChange={(event) => setMessage(event.target.value)} /></label>
          <button className="button compact" type="submit">发送</button>
        </form>
        <form className="inline-form" onSubmit={addAttachment}>
          <label>附件名<input value={attachment.fileName} placeholder="sample.pdf" onChange={(event) => setAttachment({ ...attachment, fileName: event.target.value })} /></label>
          <label>大小 bytes<input type="number" min="0" value={attachment.fileSize} onChange={(event) => setAttachment({ ...attachment, fileSize: event.target.value })} /></label>
          <label>类型<input value={attachment.contentType} onChange={(event) => setAttachment({ ...attachment, contentType: event.target.value })} /></label>
          <button className="button compact secondary" type="submit"><UploadCloud size={16} /> 记录附件</button>
        </form>
        {order.status === "review" ? <button className="button full" type="button" onClick={acceptOrder}>确认验收并完成订单</button> : null}
      </section>
      <RecordList title="沟通记录" icon={<MessageCircle size={18} />} empty="还没有沟通记录" items={order.messages.map((item) => `${item.authorEmail ?? "酷里"}：${item.body}`)} />
      <RecordList title="附件列表" icon={<FileUp size={18} />} empty="还没有附件" items={order.attachments.map((item) => `${item.fileName} · ${Math.round(item.fileSize / 1024)}KB · ${item.storageKey}`)} />
    </article>
  );
}

function Timeline({ events }: { events: Order["events"] }) {
  return (
    <section className="record-panel">
      <div className="panel-title"><ClipboardList size={18} /> 进度时间线</div>
      {events.length === 0 ? <p className="muted">暂无节点</p> : null}
      <div className="timeline">
        {events.map((event) => (
          <div className="timeline-item" key={event.id}>
            <strong>{statusLabels[event.status]?.label ?? event.status}</strong>
            <span>{event.note}</span>
            <small>{new Date(event.createdAt).toLocaleString()}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function RecordList({ title, icon, items, empty }: { title: string; icon: React.ReactNode; items: string[]; empty: string }) {
  return (
    <section className="record-panel">
      <div className="panel-title">{icon} {title}</div>
      {items.length === 0 ? <p className="muted">{empty}</p> : null}
      <div className="record-list">
        {items.map((item) => (
          <div className="record-row" key={item}>{item}</div>
        ))}
      </div>
    </section>
  );
}

function OrderProgress({ status }: { status: string }) {
  const keys = Object.keys(statusLabels);
  const currentIndex = Math.max(0, keys.indexOf(status));
  return (
    <div className="progress-line">
      {keys.map((key, index) => {
        const meta = statusLabels[key];
        const Icon = meta.icon;
        return (
          <div className={`progress-step ${index <= currentIndex ? "done" : ""}`} key={key}>
            <span><Icon size={16} /></span>
            <strong>{meta.label}</strong>
            <small>{meta.hint}</small>
          </div>
        );
      })}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}

function ChoiceField({ label, name, value, options, onChange }: { label: string; name: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <div className="field">
      <span>{label}</span>
      <div className="choice-row">
        {options.map((option) => (
          <label key={option}>
            <input type="radio" name={name} checked={value === option} onChange={() => onChange(option)} />
            <span>{option}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function SectionHead({ title, description }: { title: string; description: string }) {
  return <div className="section-head"><h2>{title}</h2><p>{description}</p></div>;
}

function DashboardHeader({ title, description, icon }: { title: string; description: string; icon: React.ReactNode }) {
  return <div className="dashboard-head"><div className="iconbox">{icon}</div><div><h1 className="compact-title">{title}</h1><p>{description}</p></div></div>;
}

function Stat({ label, value }: { label: string; value: number }) {
  return <article className="card stat-card"><span>{label}</span><strong>{value}</strong></article>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="info-card"><span>{label}</span><strong>{value}</strong></div>;
}

function EmptyPanel({ text }: { text: string }) {
  return <article className="panel empty-panel"><Eye size={24} /><p>{text}</p></article>;
}

function LoadingBlock({ text }: { text: string }) {
  return <section className="shell section"><div className="panel empty-panel">{text}</div></section>;
}

function numberOrNull(value: string) {
  return value === "" ? null : Number(value);
}

function noteForService(slug?: string): NoteInput {
  const service = services.find((item) => item.slug === slug);
  return {
    ...emptyNote,
    attachments: [],
    serviceSlug: service?.slug,
    category: service?.tag ?? emptyNote.category
  };
}

function readFileForNote(file: File) {
  return new Promise<NonNullable<NoteInput["attachments"]>[number]>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result ?? "");
      resolve({
        fileName: file.name,
        fileSize: file.size,
        contentType: file.type || "application/octet-stream",
        contentBase64: result.includes(",") ? result.split(",")[1] : result
      });
    };
    reader.onerror = () => reject(reader.error ?? new Error("文件读取失败"));
    reader.readAsDataURL(file);
  });
}
