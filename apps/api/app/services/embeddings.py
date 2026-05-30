from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class EmbeddingResult:
    provider: str
    model: str
    vector: list[float]


def remote_embeddings_enabled() -> bool:
    settings = get_settings()
    return bool(settings.effective_llm_api_key and settings.embedding_model != "local-rules")


def embed_text(text: str, *, allow_remote: bool = True) -> EmbeddingResult:
    if allow_remote and remote_embeddings_enabled():
        remote = _remote_embedding(text)
        if remote:
            return remote
    return _local_embedding(text)


def vector_to_json(vector: list[float]) -> str:
    return json.dumps([round(value, 8) for value in vector], ensure_ascii=False, separators=(",", ":"))


def vector_from_json(raw: str) -> list[float]:
    if not raw or raw == "[]":
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [float(item) for item in data if isinstance(item, int | float)]


def vector_to_pg_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def _remote_embedding(text: str) -> EmbeddingResult | None:
    settings = get_settings()
    try:
        url = settings.effective_llm_base_url.rstrip("/") + "/embeddings"
        payload = {"model": settings.embedding_model, "input": text[:8000]}
        headers = {"Authorization": f"Bearer {settings.effective_llm_api_key}", "Content-Type": "application/json"}
        response = httpx.post(url, headers=headers, json=payload, timeout=settings.llm_timeout_seconds)
        response.raise_for_status()
        body = response.json()
        vector = body["data"][0]["embedding"]
        return EmbeddingResult(provider=settings.effective_llm_provider or "openai-compatible", model=settings.embedding_model, vector=[float(item) for item in vector])
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None


def _local_embedding(text: str) -> EmbeddingResult:
    settings = get_settings()
    dimension = max(32, int(settings.vector_dimension))
    vector = [0.0] * dimension
    tokens = _tokens(text)
    if not tokens:
        vector[0] = 1.0
        return EmbeddingResult(provider="local-hash", model="local-hash", vector=vector)

    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        index = value % dimension
        sign = 1.0 if value & 1 else -1.0
        weight = 1.0 + min(len(token), 12) / 12
        vector[index] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        vector[0] = 1.0
        return EmbeddingResult(provider="local-hash", model="local-hash", vector=vector)
    return EmbeddingResult(provider="local-hash", model="local-hash", vector=[value / norm for value in vector])


def _tokens(text: str) -> list[str]:
    lowered = text.lower()
    ascii_terms = re.findall(r"[a-z0-9_\\-]{2,}", lowered)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    chinese_terms = ["".join(chinese_chars[index : index + 2]) for index in range(max(len(chinese_chars) - 1, 0))]
    return list(dict.fromkeys([*ascii_terms, *chinese_terms]))
