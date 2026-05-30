import { toValue, type MaybeRefOrGetter } from "vue";

type FaqItem = {
  question: string;
  answer: string;
};

type SeoInput = {
  title: MaybeRefOrGetter<string>;
  description: MaybeRefOrGetter<string>;
  path?: MaybeRefOrGetter<string>;
  image?: MaybeRefOrGetter<string>;
  type?: MaybeRefOrGetter<string>;
  structuredData?: MaybeRefOrGetter<Array<Record<string, unknown>>>;
};

export function useKuliSeo(input: SeoInput) {
  const config = useRuntimeConfig();

  useHead(() => {
    const title = toValue(input.title);
    const description = toValue(input.description);
    const path = toValue(input.path ?? "/");
    const image = toValue(input.image ?? "/og-image.svg");
    const type = toValue(input.type ?? "website");
    const canonical = absoluteUrl(String(config.public.siteUrl), path);
    const ogImage = absoluteUrl(String(config.public.siteUrl), image);
    const structuredData = toValue(input.structuredData ?? []);

    return {
      title,
      link: [{ rel: "canonical", href: canonical }],
      meta: [
        { name: "description", content: description },
        { property: "og:type", content: type },
        { property: "og:title", content: title },
        { property: "og:description", content: description },
        { property: "og:url", content: canonical },
        { property: "og:image", content: ogImage },
        { name: "twitter:card", content: "summary_large_image" },
        { name: "twitter:title", content: title },
        { name: "twitter:description", content: description },
        { name: "twitter:image", content: ogImage }
      ],
      script: structuredData.map((item) => ({
        type: "application/ld+json",
        innerHTML: JSON.stringify(item)
      }))
    };
  });
}

export function faqPageJsonLd(items: FaqItem[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer
      }
    }))
  };
}

function absoluteUrl(siteUrl: string, path: string) {
  if (/^https?:\/\//.test(path)) return path;
  const base = siteUrl.replace(/\/+$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}
