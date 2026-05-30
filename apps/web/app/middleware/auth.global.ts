export default defineNuxtRouteMiddleware(async (to) => {
  const path = to.path;
  const protectedPrefixes = ["/note", "/orders", "/me", "/settings", "/referrals", "/notifications"];
  const isProtected = protectedPrefixes.some((prefix) => path === prefix || path.startsWith(`${prefix}/`));
  const isAdmin = path === "/admin" || path.startsWith("/admin/");
  const auth = useAuthStore();

  if (import.meta.server) {
    const tokenCookie = useCookie<string | null>("kuli-v2-token");
    if (tokenCookie.value) await auth.restore();
    if ((isProtected || isAdmin) && !auth.user) {
      return navigateTo({ path: "/login", query: { redirect: to.fullPath } });
    }
    if (isAdmin && auth.user?.role !== "admin") {
      return navigateTo("/orders");
    }
    return;
  }

  if (!auth.ready) await auth.restore();

  if ((isProtected || isAdmin) && !auth.user) {
    return navigateTo({ path: "/login", query: { redirect: to.fullPath } });
  }

  if (isAdmin && auth.user?.role !== "admin") {
    return navigateTo("/orders");
  }
});
