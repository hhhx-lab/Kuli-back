const publicRoutes = [
  "/",
  "/services",
  "/services/ai-tools",
  "/services/document-processing",
  "/services/tool-development",
  "/services/deployment-config",
  "/services/api-token",
  "/services/not-sure",
  "/help",
  "/help/quick-start",
  "/help/concepts",
  "/help/faq",
  "/help/guides",
  "/help/contact",
  "/products",
  "/login",
  "/legal/privacy",
  "/legal/terms",
  "/legal/upload-policy"
];

export default defineEventHandler((event) => {
  const config = useRuntimeConfig();
  const siteUrl = String(config.public.siteUrl ?? "http://127.0.0.1:3000").replace(/\/+$/, "");
  const now = new Date().toISOString();
  const entries = publicRoutes
    .map((path) => {
      const priority = path === "/" ? "1.0" : path.startsWith("/services") || path.startsWith("/help") ? "0.8" : "0.6";
      const changefreq = path === "/" ? "weekly" : "monthly";
      return [
        "  <url>",
        `    <loc>${escapeXml(siteUrl + path)}</loc>`,
        `    <lastmod>${now}</lastmod>`,
        `    <changefreq>${changefreq}</changefreq>`,
        `    <priority>${priority}</priority>`,
        "  </url>"
      ].join("\n");
    })
    .join("\n");

  setHeader(event, "content-type", "application/xml; charset=utf-8");
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${entries}\n</urlset>\n`;
});

function escapeXml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
