import type { ApiRequest, ApiResponse } from "~/types/api-contract";

type ApiOptions = RequestInit & {
  token?: string | null;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
  }
}

export function useApi() {
  const config = useRuntimeConfig();

  async function request<T>(path: string, options: ApiOptions = {}) {
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");
    if (options.token) headers.set("Authorization", `Bearer ${options.token}`);
    const response = await fetch(`${config.public.apiBaseUrl}${path}`, { ...options, headers });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new ApiError(body.detail ?? body.error?.message ?? "请求失败", response.status);
    }
    return body as T;
  }

  async function uploadFile(token: string, upload: PresignedUpload, file: File) {
    const uploadUrl = upload.uploadUrl.startsWith("http") ? upload.uploadUrl : `${config.public.apiBaseUrl}${upload.uploadUrl}`;
    if (upload.provider === "local") {
      const headers = new Headers();
      headers.set("Authorization", `Bearer ${token}`);
      headers.set("Content-Type", file.type || "application/octet-stream");
      const response = await fetch(uploadUrl, { method: "POST", headers, body: file });
      if (!response.ok) throw new ApiError("本地附件上传失败", response.status);
      return;
    }

    const form = new FormData();
    Object.entries(upload.fields).forEach(([key, value]) => form.append(key, value));
    form.append("file", file);
    const response = await fetch(uploadUrl, { method: "POST", body: form });
    if (!response.ok) throw new ApiError("对象存储上传失败", response.status);
  }

  return {
    request,
    uploadFile,
    listServices: () => request<ApiResponse<"/api/services", "get">>("/api/services"),
    getService: (slug: string) => request<ApiResponse<"/api/services/{slug}", "get">>(`/api/services/${encodeURIComponent(slug)}`),
    listKnowledge: () => request<ApiResponse<"/api/knowledge", "get">>("/api/knowledge"),
    searchKnowledge: (query: string) => request<ApiResponse<"/api/knowledge/search", "get">>(`/api/knowledge/search?q=${encodeURIComponent(query)}`),
    listDocs: () => request<ApiResponse<"/api/docs", "get">>("/api/docs"),
    getDoc: (slug: string) => request<ApiResponse<"/api/docs/{slug}", "get">>(`/api/docs/${encodeURIComponent(slug)}`),
    searchDocs: (query: string) => request<ApiResponse<"/api/docs/search", "get">>(`/api/docs/search?q=${encodeURIComponent(query)}`),
    polishDemand: (input: { demand: string; serviceSlug?: string }) =>
      request<ApiResponse<"/api/ai/polish-demand", "post">>("/api/ai/polish-demand", {
        method: "POST",
        body: JSON.stringify(input)
      }),
    login: (email: string, password: string) =>
      request<ApiResponse<"/api/auth/login", "post">>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
    register: (input: { email: string; password: string; displayName: string; referralCode?: string }) =>
      request<ApiResponse<"/api/auth/register", "post">>("/api/auth/register", { method: "POST", body: JSON.stringify(input) }),
    me: (token: string) => request<ApiResponse<"/api/auth/me", "get">>("/api/auth/me", { token }),
    requestEmailVerification: (token: string) =>
      request<{ ok: boolean; message: string }>("/api/auth/email-verification/request", { method: "POST", token }),
    confirmEmailVerification: (input: { token: string }) =>
      request<{ ok: boolean; message: string }>("/api/auth/email-verification/confirm", { method: "POST", body: JSON.stringify(input) }),
    requestPasswordReset: (email: string) =>
      request<{ ok: boolean; message: string }>("/api/auth/password-reset/request", { method: "POST", body: JSON.stringify({ email }) }),
    confirmPasswordReset: (input: { token: string; password: string }) =>
      request<{ ok: boolean; message: string }>("/api/auth/password-reset/confirm", { method: "POST", body: JSON.stringify(input) }),
    getProfile: (token: string) => request<{ profile: UserProfile }>("/api/me/profile", { token }),
    updateProfile: (token: string, input: { displayName: string }) =>
      request<{ profile: UserProfile }>("/api/me/profile", { method: "PATCH", token, body: JSON.stringify(input) }),
    getMySummary: (token: string) => request<{ summary: UserSummary }>("/api/me/summary", { token }),
    getReferral: (token: string) => request<{ referral: UserReferral }>("/api/me/referral", { token }),
    listNotifications: (token: string) => request<ApiResponse<"/api/notifications", "get">>("/api/notifications", { token }),
    getUnreadNotificationCount: (token: string) => request<ApiResponse<"/api/notifications/unread-count", "get">>("/api/notifications/unread-count", { token }),
    markNotificationRead: (token: string, notificationId: string) =>
      request<ApiResponse<"/api/notifications/{notification_id}/read", "patch">>(`/api/notifications/${encodeURIComponent(notificationId)}/read`, { method: "PATCH", token }),
    markAllNotificationsRead: (token: string) => request<ApiResponse<"/api/notifications/read-all", "patch">>("/api/notifications/read-all", { method: "PATCH", token }),
    createOrder: (input: NoteInput, token?: string | null) =>
      request<ApiResponse<"/api/orders", "post">>("/api/orders", { method: "POST", token, body: JSON.stringify(input) }),
    createInquiry: (input: NoteInput) =>
      request<ApiResponse<"/api/inquiries", "post">>("/api/inquiries", { method: "POST", body: JSON.stringify(input) }),
    listOrders: (token: string) => request<ApiResponse<"/api/orders", "get">>("/api/orders", { token }),
    getOrder: (token: string, orderNumber: string) => request<ApiResponse<"/api/orders/{order_number}", "get">>(`/api/orders/${encodeURIComponent(orderNumber)}`, { token }),
    presignUpload: (token: string, input: UploadPresignInput) =>
      request<ApiResponse<"/api/uploads/presign", "post">>("/api/uploads/presign", { method: "POST", token, body: JSON.stringify(input) }),
    addOrderAttachment: (token: string, orderNumber: string, input: AttachmentInput) =>
      request<ApiResponse<"/api/orders/{order_number}/attachments", "post">>(`/api/orders/${encodeURIComponent(orderNumber)}/attachments`, {
        method: "POST",
        token,
        body: JSON.stringify(input)
      }),
    getAttachmentDownload: (token: string, orderNumber: string, attachmentId: string) =>
      request<ApiResponse<"/api/orders/{order_number}/attachments/{attachment_id}/download", "get">>(
        `/api/orders/${encodeURIComponent(orderNumber)}/attachments/${encodeURIComponent(attachmentId)}/download`,
        { token }
      ),
    addOrderMessage: (token: string, orderNumber: string, body: string) =>
      request<ApiResponse<"/api/orders/{order_number}/messages", "post">>(`/api/orders/${encodeURIComponent(orderNumber)}/messages`, {
        method: "POST",
        token,
        body: JSON.stringify({ body })
      }),
    acceptOrder: (token: string, orderNumber: string) =>
      request<ApiResponse<"/api/orders/{order_number}/accept", "post">>(`/api/orders/${encodeURIComponent(orderNumber)}/accept`, { method: "POST", token }),
    listAdminOrders: (token: string, query = "") => request<ApiResponse<"/api/admin/orders", "get">>(`/api/admin/orders${query}`, { token }),
    getAdminOrder: (token: string, orderNumber: string) =>
      request<ApiResponse<"/api/admin/orders/{order_number}", "get">>(`/api/admin/orders/${encodeURIComponent(orderNumber)}`, { token }),
    updateAdminOrder: (token: string, orderNumber: string, input: AdminOrderPatch) =>
      request<ApiResponse<"/api/admin/orders/{order_number}", "patch">>(`/api/admin/orders/${encodeURIComponent(orderNumber)}`, {
        method: "PATCH",
        token,
        body: JSON.stringify(input)
      }),
    addAdminMessage: (token: string, orderNumber: string, input: { body: string; visibility: "public" | "internal" }) =>
      request<ApiResponse<"/api/admin/orders/{order_number}/messages", "post">>(`/api/admin/orders/${encodeURIComponent(orderNumber)}/messages`, {
        method: "POST",
        token,
        body: JSON.stringify(input)
      }),
    addQuote: (token: string, orderNumber: string, input: QuoteInput) =>
      request<ApiResponse<"/api/admin/orders/{order_number}/quotes", "post">>(`/api/admin/orders/${encodeURIComponent(orderNumber)}/quotes`, {
        method: "POST",
        token,
        body: JSON.stringify(input)
      }),
    addPayment: (token: string, orderNumber: string, input: PaymentInput) =>
      request<ApiResponse<"/api/admin/orders/{order_number}/payments", "post">>(`/api/admin/orders/${encodeURIComponent(orderNumber)}/payments`, {
        method: "POST",
        token,
        body: JSON.stringify(input)
      }),
    addDeliverable: (token: string, orderNumber: string, input: DeliverableInput) =>
      request<ApiResponse<"/api/admin/orders/{order_number}/deliverables", "post">>(`/api/admin/orders/${encodeURIComponent(orderNumber)}/deliverables`, {
        method: "POST",
        token,
        body: JSON.stringify(input)
      }),
    runAutomation: (token: string, orderNumber: string) =>
      request<ApiResponse<"/api/admin/orders/{order_number}/automation/run", "post">>(`/api/admin/orders/${encodeURIComponent(orderNumber)}/automation/run`, { method: "POST", token }),
    retryAttachmentScan: (token: string, orderNumber: string, attachmentId: string) =>
      request<ApiResponse<"/api/admin/orders/{order_number}/attachments/{attachment_id}/retry-scan", "post">>(
        `/api/admin/orders/${encodeURIComponent(orderNumber)}/attachments/${encodeURIComponent(attachmentId)}/retry-scan`,
        { method: "POST", token }
      ),
    applySuggestion: (token: string, orderNumber: string, suggestionId: string) =>
      request<ApiResponse<"/api/admin/orders/{order_number}/suggestions/{suggestion_id}/apply", "post">>(`/api/admin/orders/${encodeURIComponent(orderNumber)}/suggestions/${encodeURIComponent(suggestionId)}/apply`, {
        method: "POST",
        token
      }),
    createAgentSession: (input: { pagePath: string; visitorId?: string }, token?: string | null) =>
      request<ApiResponse<"/api/agent/sessions", "post">>("/api/agent/sessions", { method: "POST", token, body: JSON.stringify(input) }),
    chat: (input: { sessionId: string; message: string }, token?: string | null) =>
      request<ApiResponse<"/api/agent/chat", "post">>("/api/agent/chat", { method: "POST", token, body: JSON.stringify(input) })
  };
}

export type User = ApiResponse<"/api/auth/me", "get">["user"];
export type UserProfile = User & {
  points: number;
  referralCode: string;
  referredByUserId: string | null;
  emailVerifiedAt: string | null;
  createdAt: string;
};
export type UserSummary = {
  profile: UserProfile;
  orders: { total: number; byStatus: Record<string, number> };
  recentOrders: Array<{ orderNumber: string; title: string; status: string; nextAction: string; updatedAt: string }>;
  points: { current: number; nextLevel: number; progress: number };
};
export type UserReferral = {
  referralCode: string;
  invitePath: string;
  points: number;
  rewardedInvites: number;
  rewards: Array<{ id: string; points: number; reason: string; createdAt: string }>;
};
export type NotificationItem = ApiResponse<"/api/notifications", "get">["notifications"][number];
export type ServiceItem = ApiResponse<"/api/services", "get">["services"][number];
export type KnowledgeArticle = ApiResponse<"/api/knowledge", "get">["articles"][number];
export type DocSummary = ApiResponse<"/api/docs", "get">["docs"][number];
export type DocDetail = ApiResponse<"/api/docs/{slug}", "get">["doc"];
export type DocSearchResult = ApiResponse<"/api/docs/search", "get">["results"][number];
export type NoteInput = ApiRequest<"/api/orders", "post">;
export type UploadPresignInput = ApiRequest<"/api/uploads/presign", "post">;
export type PresignedUpload = ApiResponse<"/api/uploads/presign", "post">["upload"];
export type AttachmentInput = ApiRequest<"/api/orders/{order_number}/attachments", "post">;
export type AttachmentDownload = ApiResponse<"/api/orders/{order_number}/attachments/{attachment_id}/download", "get">["download"];
export type Order = ApiResponse<"/api/orders/{order_number}", "get">["order"];
export type OrderAttachment = Order["attachments"][number];
export type OrderMessage = Order["messages"][number];
export type OrderEvent = Order["events"][number];
export type Quote = Order["quotes"][number];
export type PaymentRecord = Order["payments"][number];
export type Deliverable = Order["deliverables"][number];
export type AdminOrder = ApiResponse<"/api/admin/orders/{order_number}", "get">["order"];
export type AutomationSuggestion = AdminOrder["automationSuggestions"][number];
export type OrderTodo = AdminOrder["todos"][number];
export type OrderAiSummary = AdminOrder["aiSummaries"][number];
export type AdminOrderListResponse = ApiResponse<"/api/admin/orders", "get">;
export type AdminOrderPatch = ApiRequest<"/api/admin/orders/{order_number}", "patch">;
export type QuoteInput = ApiRequest<"/api/admin/orders/{order_number}/quotes", "post">;
export type PaymentInput = ApiRequest<"/api/admin/orders/{order_number}/payments", "post">;
export type DeliverableInput = ApiRequest<"/api/admin/orders/{order_number}/deliverables", "post">;
