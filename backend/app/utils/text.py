from __future__ import annotations

import re


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def semantic_chunks(text: str, target_chars: int = 1400, overlap_chars: int = 180) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > target_chars:
            chunks.append(current)
            tail = current[-overlap_chars:]
            first_space = tail.find(" ")
            current = tail[first_space + 1 :] if first_space >= 0 else tail
        current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def fts_query(query: str) -> str:
    tokens = re.findall(r"[\w-]+", query.lower(), flags=re.UNICODE)
    stop = {"the", "a", "an", "is", "are", "was", "were", "what", "when", "where", "did", "i", "my", "about"}
    useful = [token.replace('"', "") for token in tokens if token not in stop]
    return " OR ".join(f'"{token}"' for token in useful[:12])

