import { defineStore } from "pinia";
import type { User } from "~/composables/useApi";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: "" as string,
    user: null as User | null,
    ready: false
  }),
  actions: {
    async restore() {
      const tokenCookie = useCookie<string | null>("kuli-v2-token", { sameSite: "lax", maxAge: 60 * 60 * 24 * 30 });
      const stored = import.meta.server ? tokenCookie.value : localStorage.getItem("kuli-v2-token") || tokenCookie.value;
      if (!stored) {
        this.ready = true;
        return;
      }
      const api = useApi();
      try {
        const result = await api.me(stored);
        this.token = stored;
        this.user = result.user;
        tokenCookie.value = stored;
        if (!import.meta.server) localStorage.setItem("kuli-v2-token", stored);
      } catch {
        this.token = "";
        this.user = null;
        tokenCookie.value = null;
        if (!import.meta.server) localStorage.removeItem("kuli-v2-token");
      } finally {
        this.ready = true;
      }
    },
    async login(email: string, password: string) {
      const api = useApi();
      const result = await api.login(email, password);
      this.token = result.token;
      this.user = result.user;
      const tokenCookie = useCookie<string | null>("kuli-v2-token", { sameSite: "lax", maxAge: 60 * 60 * 24 * 30 });
      tokenCookie.value = result.token;
      localStorage.setItem("kuli-v2-token", result.token);
    },
    async register(input: { email: string; password: string; displayName: string; referralCode?: string }) {
      const api = useApi();
      const result = await api.register(input);
      this.token = result.token;
      this.user = result.user;
      const tokenCookie = useCookie<string | null>("kuli-v2-token", { sameSite: "lax", maxAge: 60 * 60 * 24 * 30 });
      tokenCookie.value = result.token;
      localStorage.setItem("kuli-v2-token", result.token);
    },
    logout() {
      this.token = "";
      this.user = null;
      const tokenCookie = useCookie<string | null>("kuli-v2-token", { sameSite: "lax", maxAge: 60 * 60 * 24 * 30 });
      tokenCookie.value = null;
      localStorage.removeItem("kuli-v2-token");
    }
  }
});
