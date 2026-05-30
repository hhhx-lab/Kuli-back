from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    displayName: str


class AuthIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str


class RegisterIn(AuthIn):
    displayName: str = Field(min_length=1, max_length=80)
    referralCode: str | None = Field(default=None, max_length=40)


class AuthOut(BaseModel):
    token: str
    user: UserOut


class StatusOut(BaseModel):
    ok: bool
    message: str


class TokenConfirmIn(BaseModel):
    token: str = Field(min_length=16, max_length=512)


class PasswordResetRequestIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class PasswordResetConfirmIn(TokenConfirmIn):
    password: str


class ServiceOut(BaseModel):
    slug: str
    title: str
    tag: str
    summary: str
    audience: list[str]
    commonNeeds: list[str]
    deliverables: list[str]
    requiredMaterials: list[str]
    priceRange: str
    timeline: str
    risks: list[str]
    cases: list[dict[str, str]]
    faq: list[dict[str, str]]


class HealthOut(BaseModel):
    ok: bool
    service: str
    version: str


class DependencyHealthOut(BaseModel):
    ok: bool
    required: bool
    status: str
    detail: str | None = None
    driver: str | None = None
    provider: str | None = None
    model: str | None = None
    articleCount: int | None = None
    chunkCount: int | None = None
    embeddingCount: int | None = None


class HealthDepsOut(HealthOut):
    environment: str
    dependencies: dict[str, DependencyHealthOut]


class ServicesOut(BaseModel):
    services: list[ServiceOut]


class ServiceEnvelope(BaseModel):
    service: ServiceOut


class KnowledgeArticleOut(BaseModel):
    id: str
    scope: str
    title: str
    body: str
    tags: list[str]
    source: str
    updatedAt: str


class KnowledgeArticlesOut(BaseModel):
    articles: list[KnowledgeArticleOut]


class DocSummaryOut(BaseModel):
    slug: str
    title: str
    category: str
    description: str
    tags: list[str]
    order: int
    updatedAt: str
    status: str


class DocAnchorOut(BaseModel):
    id: str
    title: str
    level: int


class DocDetailOut(DocSummaryOut):
    content: str
    anchors: list[DocAnchorOut]
    relatedDocs: list[DocSummaryOut]


class DocsOut(BaseModel):
    docs: list[DocSummaryOut]


class DocEnvelope(BaseModel):
    doc: DocDetailOut


class DocSearchResultOut(BaseModel):
    slug: str
    title: str
    excerpt: str
    anchor: str | None = None


class DocSearchOut(BaseModel):
    results: list[DocSearchResultOut]


class PolishOut(BaseModel):
    polishedDemand: str
    hints: list[str]
    intent: str
    missingFields: list[str]
    serviceConfidence: float


class UserEnvelope(BaseModel):
    user: UserOut


class UserProfileOut(UserOut):
    points: int
    referralCode: str
    referredByUserId: str | None
    emailVerifiedAt: str | None
    createdAt: str


class UserProfileEnvelope(BaseModel):
    profile: UserProfileOut


class UserProfilePatch(BaseModel):
    displayName: str = Field(min_length=1, max_length=80)


class UserOrderSummaryOut(BaseModel):
    total: int
    byStatus: dict[str, int]


class UserSummaryEnvelope(BaseModel):
    summary: dict[str, object]


class UserReferralEnvelope(BaseModel):
    referral: dict[str, object]


class NotificationOut(BaseModel):
    id: str
    type: str
    orderNumber: str | None
    title: str
    body: str
    status: str
    targetUrl: str
    createdAt: str
    readAt: str | None


class NotificationsOut(BaseModel):
    notifications: list[NotificationOut]


class NotificationEnvelope(BaseModel):
    notification: NotificationOut


class NotificationUnreadCountOut(BaseModel):
    unreadCount: int


class NotificationsReadAllOut(BaseModel):
    updated: int


class NoteInput(BaseModel):
    serviceSlug: str | None = "not-sure"
    demand: str = Field(min_length=1, max_length=1200)
    originalDemand: str | None = None
    category: str = Field(default="先聊聊", max_length=120)
    urgency: str = "先聊聊"
    budget: str = "先报价看看"
    contact: str
    remoteHelp: str = "看情况"
    customerName: str | None = None
    intent: str | None = None


class MessageInput(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    visibility: str = "public"


class AttachmentInput(BaseModel):
    fileName: str = Field(min_length=1, max_length=255)
    fileSize: int = Field(ge=0, le=200 * 1024 * 1024)
    contentType: str = Field(min_length=1, max_length=120)
    storageKey: str = Field(min_length=1, max_length=600)
    bucket: str = "kuli-order-files"
    checksum: str = ""


class UploadPresignInput(BaseModel):
    fileName: str = Field(min_length=1, max_length=255)
    fileSize: int = Field(ge=0, le=200 * 1024 * 1024)
    contentType: str = Field(min_length=1, max_length=120)
    orderNumber: str | None = None


class PolishInput(BaseModel):
    demand: str = Field(min_length=1, max_length=1200)
    serviceSlug: str | None = None


class OrderEventOut(BaseModel):
    id: str
    status: str
    note: str
    createdBy: str | None
    createdAt: str


class OrderMessageOut(BaseModel):
    id: str
    authorUserId: str
    body: str
    visibility: str
    createdAt: str


class OrderAttachmentOut(BaseModel):
    id: str
    fileName: str
    fileSize: int
    contentType: str
    bucket: str
    storageKey: str
    visibility: str
    scanStatus: str
    parsedSummary: str
    scanError: str
    retryCount: int
    lastScannedAt: str | None
    createdAt: str


class QuoteOut(BaseModel):
    id: str
    amount: float
    kind: str
    note: str
    status: str
    createdAt: str


class PaymentRecordOut(BaseModel):
    id: str
    amount: float
    kind: str
    method: str
    status: str
    note: str
    createdAt: str


class DeliverableOut(BaseModel):
    id: str
    title: str
    description: str
    storageKey: str
    createdAt: str


class OrderOut(BaseModel):
    id: str
    orderNumber: str
    customerName: str
    contact: str
    serviceSlug: str
    category: str
    title: str
    demand: str
    originalDemand: str
    polishedDemand: str
    urgency: str
    budget: str
    remoteHelp: str
    intent: str
    missingFields: list[str]
    serviceConfidence: float
    quotedPrice: float | None
    status: str
    aiStatus: str
    nextAction: str
    publicNotes: str
    createdAt: str
    updatedAt: str
    events: list[OrderEventOut]
    messages: list[OrderMessageOut]
    attachments: list[OrderAttachmentOut]
    quotes: list[QuoteOut]
    payments: list[PaymentRecordOut]
    deliverables: list[DeliverableOut]


class AutomationSuggestionOut(BaseModel):
    id: str
    kind: str
    severity: str
    summary: str
    suggestedStatus: str | None
    suggestedMessage: str
    confidence: float
    status: str
    reason: str
    createdAt: str


class OrderTodoOut(BaseModel):
    id: str
    title: str
    source: str
    status: str
    dueAt: str | None
    createdAt: str


class OrderAiSummaryOut(BaseModel):
    id: str
    summary: str
    riskFlags: list[str]
    suggestedQuestions: list[str]
    createdAt: str


class AdminOrderOut(OrderOut):
    ownerUserId: str | None
    cost: float | None
    profit: float | None
    priority: str
    internalNotes: str
    assignedAdminId: str | None
    automationAuditCount: int
    automationSuggestions: list[AutomationSuggestionOut]
    todos: list[OrderTodoOut]
    aiSummaries: list[OrderAiSummaryOut]


class OrderEnvelope(BaseModel):
    order: OrderOut


class OrdersOut(BaseModel):
    orders: list[OrderOut]


class AdminOrderEnvelope(BaseModel):
    order: AdminOrderOut


class PaginationOut(BaseModel):
    page: int
    pageSize: int
    total: int
    hasMore: bool


class AdminOrdersOut(BaseModel):
    orders: list[AdminOrderOut]
    pagination: PaginationOut


class PresignedUploadOut(BaseModel):
    provider: str
    bucket: str
    objectKey: str
    uploadUrl: str
    publicUrl: str | None
    fields: dict[str, str]


class PresignedUploadEnvelope(BaseModel):
    upload: PresignedUploadOut


class AttachmentDownloadOut(BaseModel):
    provider: str
    bucket: str
    objectKey: str
    downloadUrl: str
    expiresIn: int


class AttachmentDownloadEnvelope(BaseModel):
    download: AttachmentDownloadOut


class AdminOrderPatch(BaseModel):
    status: str | None = None
    priority: str | None = None
    quotedPrice: float | None = None
    cost: float | None = None
    profit: float | None = None
    publicNotes: str | None = None
    internalNotes: str | None = None
    nextAction: str | None = None


class QuoteInput(BaseModel):
    amount: float
    kind: str = "full"
    note: str


class PaymentInput(BaseModel):
    amount: float
    kind: str
    method: str
    status: str
    note: str = ""


class DeliverableInput(BaseModel):
    title: str
    description: str = ""
    storageKey: str


class AgentSessionInput(BaseModel):
    visitorId: str | None = None
    pagePath: str = "/"


class AgentChatInput(BaseModel):
    sessionId: str
    message: str


class AgentSessionOut(BaseModel):
    id: str
    pagePath: str
    userId: str | None


class AgentSessionEnvelope(BaseModel):
    session: AgentSessionOut


class AgentActionOut(BaseModel):
    label: str
    to: str


class AgentCitationOut(BaseModel):
    title: str
    to: str
    source: str | None = None


class AgentDraftOut(BaseModel):
    serviceSlug: str
    summary: str
    missingFields: list[str]


class AgentChatOut(BaseModel):
    answer: str
    actions: list[AgentActionOut]
    citations: list[AgentCitationOut] = Field(default_factory=list)
    draft: AgentDraftOut | None = None


class AssistantSummaryContentOut(BaseModel):
    orderNumber: str
    status: str
    nextAction: str
    publicNotes: str


class AssistantSummaryOut(BaseModel):
    summary: AssistantSummaryContentOut


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
