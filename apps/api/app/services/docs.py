import re
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings


REQUIRED_DOC_SLUGS = ["quick-start", "concepts", "faq", "guides", "contact"]
REQUIRED_FRONTMATTER = ["slug", "title", "description", "tags", "order", "updated_at", "status"]
VALID_DOC_STATUSES = {"published", "draft", "deprecated"}
HEADING_RE = re.compile(r"^(#{2,4})\s+(.+?)(?:\s+\{#([a-z0-9-]+)\})?\s*$")


@dataclass(frozen=True)
class DocPage:
    slug: str
    title: str
    category: str
    description: str
    tags: list[str]
    order: int
    updated_at: str
    status: str
    aliases: list[str]
    source_path: str
    content: str
    anchors: list[dict[str, object]]


def docs_root() -> Path:
    return Path(get_settings().knowledge_root)


def _parse_list(value: str) -> list[str]:
    stripped = value.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        return [item.strip().strip("\"'") for item in stripped[1:-1].split(",") if item.strip()]
    return [stripped] if stripped else []


def _parse_tags(value: str) -> list[str]:
    return _parse_list(value)


def _slugify(text: str) -> str:
    ascii_text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return ascii_text or f"section-{abs(hash(text)) % 10_000}"


def _parse_frontmatter(raw: str) -> tuple[dict[str, object], str]:
    if not raw.startswith("---\n"):
        raise ValueError("文档缺少 frontmatter")
    _, frontmatter, content = raw.split("---", 2)
    meta: dict[str, object] = {}
    for line in frontmatter.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in {"tags", "aliases"}:
            meta[key] = _parse_list(value)
        elif key == "order":
            meta[key] = int(value)
        else:
            meta[key] = value
    return meta, content.strip()


def _anchors(content: str) -> list[dict[str, object]]:
    anchors: list[dict[str, object]] = []
    for line in content.splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        marker, title, explicit_id = match.groups()
        clean_title = re.sub(r"\s+\{#[a-z0-9-]+\}$", "", title).strip()
        anchors.append({"id": explicit_id or _slugify(clean_title), "title": clean_title, "level": len(marker)})
    return anchors


def _load_doc(path: Path) -> DocPage:
    meta, content = _parse_frontmatter(path.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_FRONTMATTER if key not in meta]
    if missing:
        raise ValueError(f"{path} 缺少必填 frontmatter: {', '.join(missing)}")
    status = str(meta["status"])
    if status not in VALID_DOC_STATUSES:
        raise ValueError(f"{path} status 非法: {status}")
    return DocPage(
        slug=str(meta["slug"]),
        title=str(meta["title"]),
        category=str(meta.get("category", "docs")),
        description=str(meta["description"]),
        tags=list(meta.get("tags", [])),
        order=int(meta["order"]),
        updated_at=str(meta["updated_at"]),
        status=status,
        aliases=list(meta.get("aliases", [])),
        source_path=str(path.as_posix()),
        content=content,
        anchors=_anchors(content),
    )


def load_docs(root: str | Path | None = None, *, include_unpublished: bool = False) -> list[DocPage]:
    active_root = Path(root) if root is not None else docs_root()
    docs = [_load_doc(active_root / f"{slug}.md") for slug in REQUIRED_DOC_SLUGS]
    if not include_unpublished:
        docs = [doc for doc in docs if doc.status == "published"]
    return sorted(docs, key=lambda item: item.order)


def doc_summary(doc: DocPage) -> dict[str, object]:
    return {
        "slug": doc.slug,
        "title": doc.title,
        "category": doc.category,
        "description": doc.description,
        "tags": doc.tags,
        "order": doc.order,
        "updatedAt": doc.updated_at,
        "status": doc.status,
    }


def get_doc(slug: str) -> DocPage | None:
    docs = load_docs()
    for doc in docs:
        if slug == doc.slug or slug in doc.aliases:
            return doc
    if slug not in REQUIRED_DOC_SLUGS:
        return None
    path = docs_root() / f"{slug}.md"
    if not path.exists():
        return None
    doc = _load_doc(path)
    return doc if doc.status == "published" else None


def doc_detail(doc: DocPage) -> dict[str, object]:
    related = [item for item in load_docs() if item.slug != doc.slug][:3]
    return {
        **doc_summary(doc),
        "content": doc.content,
        "anchors": doc.anchors,
        "relatedDocs": [doc_summary(item) for item in related],
    }


def search_docs(query: str) -> list[dict[str, object]]:
    q = query.strip().lower()
    results: list[dict[str, object]] = []
    if not q:
        return results
    for doc in load_docs():
        haystack = f"{doc.title}\n{doc.description}\n{' '.join(doc.tags)}\n{doc.content}".lower()
        if q not in haystack:
            continue
        index = max(haystack.find(q), 0)
        plain = re.sub(r"[#>*_`{}\[\]()-]+", " ", doc.content)
        excerpt = re.sub(r"\s+", " ", plain).strip()
        if len(excerpt) > 140:
            excerpt = excerpt[:140] + "..."
        anchor = doc.anchors[0]["id"] if doc.anchors else None
        results.append({"slug": doc.slug, "title": doc.title, "excerpt": excerpt, "anchor": anchor, "score": index})
    return sorted(results, key=lambda item: int(item["score"]))
