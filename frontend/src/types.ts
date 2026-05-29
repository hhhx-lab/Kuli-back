export type Role = "admin" | "user";

export type User = {
  id: string;
  email: string;
  role: Role;
  displayName: string;
};

export type ServiceCatalogItem = {
  slug: string;
  title: string;
  tag: string;
  summary: string;
  audience: string[];
  commonNeeds: string[];
  deliverables: string[];
  requiredMaterials: string[];
  priceRange: string;
  timeline: string;
  risks: string[];
  cases: Array<{ title: string; description: string }>;
  faq: Array<{ question: string; answer: string }>;
};

export type OrderEvent = {
  id: string;
  status: string;
  note: string;
  createdByEmail?: string | null;
  createdAt: string;
};

export type OrderMessage = {
  id: string;
  authorEmail: string | null;
  authorRole: Role | null;
  body: string;
  visibility: "public" | "internal";
  createdAt: string;
};

export type OrderAttachment = {
  id: string;
  uploaderEmail: string | null;
  fileName: string;
  fileSize: number;
  contentType: string;
  storageKey: string;
  visibility: "public" | "internal";
  createdAt: string;
};

export type Quote = {
  id: string;
  amount: number;
  kind: string;
  note: string;
  status: string;
  createdByEmail?: string | null;
  createdAt: string;
};

export type PaymentRecord = {
  id: string;
  amount: number;
  kind: string;
  method: string;
  status: string;
  note: string;
  createdByEmail?: string | null;
  createdAt: string;
};

export type Deliverable = {
  id: string;
  title: string;
  description: string;
  storageKey: string;
  createdByEmail?: string | null;
  createdAt: string;
};

export type Order = {
  id: string;
  orderNumber: string;
  ownerEmail: string | null;
  customerName: string;
  contact: string;
  serviceSlug: string;
  category: string;
  title: string;
  demand: string;
  originalDemand: string;
  urgency: string;
  budget: string;
  remoteHelp: string;
  quotedPrice: number | null;
  status: OrderStatus;
  priorityLabel: string;
  publicNotes: string;
  createdAt: string;
  updatedAt: string;
  events: OrderEvent[];
  messages: OrderMessage[];
  attachments: OrderAttachment[];
  quotes: Quote[];
  payments: PaymentRecord[];
  deliverables: Deliverable[];
};

export type AdminOrder = Order & {
  ownerUserId: string | null;
  cost: number | null;
  profit: number | null;
  priority: "low" | "normal" | "high" | "urgent";
  internalNotes: string;
  agentBrief: AgentBrief;
};

export type AgentBrief = {
  originalDemand: string;
  summary: string;
  tags: string[];
  suggestedQuestions: string[];
  recommendedNextStatus: OrderStatus;
  consultationFirst: boolean;
  chargeHint: string;
};

export type OrderStatus =
  | "submitted"
  | "clarifying"
  | "quoted"
  | "deposit_pending"
  | "in_progress"
  | "review"
  | "final_payment_pending"
  | "completed"
  | "cancelled";

export type NoteInput = {
  serviceSlug?: string;
  demand: string;
  originalDemand?: string;
  category: string;
  urgency: string;
  budget: string;
  contact: string;
  remoteHelp: string;
  attachments?: NoteAttachmentInput[];
};

export type NoteAttachmentInput = {
  fileName: string;
  fileSize: number;
  contentType: string;
  contentBase64?: string;
};
