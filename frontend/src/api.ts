import type { AdminOrder, NoteInput, Order, ServiceCatalogItem, User } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4000";

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

async function request<T>(path: string, options: ApiOptions = {}) {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.token) headers.set("Authorization", `Bearer ${options.token}`);

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });
  const body = (await response.json().catch(() => ({}))) as { error?: { message?: string } };
  if (!response.ok) {
    throw new ApiError(body.error?.message ?? "请求失败", response.status);
  }
  return body as T;
}

export const api = {
  login(email: string, password: string) {
    return request<{ token: string; user: User }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
  },
  register(displayName: string, email: string, password: string) {
    return request<{ token: string; user: User }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ displayName, email, password })
    });
  },
  me(token: string) {
    return request<{ user: User }>("/api/auth/me", { token });
  },
  listServices() {
    return request<{ services: ServiceCatalogItem[] }>("/api/services");
  },
  getService(slug: string) {
    return request<{ service: ServiceCatalogItem }>(`/api/services/${encodeURIComponent(slug)}`);
  },
  polishDemand(input: { demand: string; serviceSlug?: string }) {
    return request<{ polishedDemand: string; hints: string[] }>("/api/ai/polish-demand", {
      method: "POST",
      body: JSON.stringify(input)
    });
  },
  createPublicInquiry(input: NoteInput) {
    return request<{ order: Order }>("/api/public/inquiries", {
      method: "POST",
      body: JSON.stringify(input)
    });
  },
  createOrder(input: NoteInput, token: string) {
    return request<{ order: Order }>("/api/orders", {
      method: "POST",
      token,
      body: JSON.stringify(input)
    });
  },
  listOrders(token: string) {
    return request<{ orders: Order[] }>("/api/orders", { token });
  },
  addOrderMessage(token: string, orderNumber: string, body: string) {
    return request<{ order: Order }>(`/api/orders/${orderNumber}/messages`, {
      method: "POST",
      token,
      body: JSON.stringify({ body })
    });
  },
  addOrderAttachment(
    token: string,
    orderNumber: string,
    input: { fileName: string; fileSize: number; contentType: string; storageKey?: string; contentBase64?: string }
  ) {
    return request<{ order: Order }>(`/api/orders/${orderNumber}/attachments`, {
      method: "POST",
      token,
      body: JSON.stringify(input)
    });
  },
  acceptOrder(token: string, orderNumber: string, note: string) {
    return request<{ order: Order }>(`/api/orders/${orderNumber}/acceptance`, {
      method: "POST",
      token,
      body: JSON.stringify({ note })
    });
  },
  listAdminOrders(token: string) {
    return request<{ orders: AdminOrder[] }>("/api/admin/orders", { token });
  },
  updateAdminOrder(
    token: string,
    orderNumber: string,
    patch: Partial<Pick<AdminOrder, "status" | "priority" | "quotedPrice" | "cost" | "profit" | "publicNotes" | "internalNotes">>
  ) {
    return request<{ order: AdminOrder }>(`/api/admin/orders/${orderNumber}`, {
      method: "PATCH",
      token,
      body: JSON.stringify(patch)
    });
  },
  updateAdminOrderStatus(token: string, orderNumber: string, patch: Pick<AdminOrder, "status"> & Partial<Pick<AdminOrder, "publicNotes" | "internalNotes">>) {
    return request<{ order: AdminOrder }>(`/api/admin/orders/${orderNumber}/status`, {
      method: "PATCH",
      token,
      body: JSON.stringify(patch)
    });
  },
  createQuote(token: string, orderNumber: string, input: { amount: number; kind: string; note: string }) {
    return request<{ order: AdminOrder }>(`/api/admin/orders/${orderNumber}/quotes`, {
      method: "POST",
      token,
      body: JSON.stringify(input)
    });
  },
  createPayment(token: string, orderNumber: string, input: { amount: number; kind: string; method: string; status: string; note: string }) {
    return request<{ order: AdminOrder }>(`/api/admin/orders/${orderNumber}/payments`, {
      method: "POST",
      token,
      body: JSON.stringify(input)
    });
  },
  createDeliverable(token: string, orderNumber: string, input: { title: string; description: string; storageKey: string }) {
    return request<{ order: AdminOrder }>(`/api/admin/orders/${orderNumber}/deliverables`, {
      method: "POST",
      token,
      body: JSON.stringify(input)
    });
  }
};
