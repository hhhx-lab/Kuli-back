export default defineEventHandler((event) => {
  const config = useRuntimeConfig();
  const siteUrl = String(config.public.siteUrl ?? "http://127.0.0.1:3000").replace(/\/+$/, "");

  setHeader(event, "content-type", "text/plain; charset=utf-8");
  return [
    "User-agent: *",
    "Allow: /",
    "Disallow: /admin",
    "Disallow: /orders",
    "Disallow: /me",
    "Disallow: /settings",
    "Disallow: /referrals",
    "Disallow: /notifications",
    "Disallow: /note",
    "",
    `Sitemap: ${siteUrl}/sitemap.xml`,
    ""
  ].join("\n");
});
