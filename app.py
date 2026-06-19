from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from simhash import Simhash

import hashlib
import re
import unicodedata

app = FastAPI(title="News Preprocessing Service")


# =========================================================
# Request / Response Models
# =========================================================

class ArticleRequest(BaseModel):
    content: str


class ArticleResponse(BaseModel):
    normalized_content: str

    sha256: str
    simhash: str

    char_count: int
    token_count: int


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_text(text: str) -> str:
    """
    Aggressive normalization for dedup.
    """

    if not text:
        return ""

    text = text.lower()
    text = unicodedata.normalize("NFKC", text)

    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# SHA256
# =========================================================

def generate_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# =========================================================
# SIMHASH (FIXED - SAFE)
# =========================================================

def generate_simhash(text: str) -> str:
    """
    FIX:
    - limit length (avoid overflow)
    - use tokens instead of raw text
    """

    # 🔥 critical fix: limit size
    text = text[:3000]

    # 🔥 safer feature extraction
    features = text.split()

    # fallback safety
    if not features:
        return "0x0"

    return hex(Simhash(features).value)


# =========================================================
# STATS
# =========================================================

def count_tokens(text: str) -> int:
    return len(text.split())


# =========================================================
# MAIN PIPELINE
# =========================================================

@app.post("/process_article", response_model=ArticleResponse)
def process_article(article: ArticleRequest):

    normalized_content = normalize_text(article.content)

    sha256_hash = generate_sha256(normalized_content)
    simhash_hash = generate_simhash(normalized_content)

    char_count = len(normalized_content)
    token_count = count_tokens(normalized_content)

    return ArticleResponse(
        normalized_content=normalized_content,

        sha256=sha256_hash,
        simhash=simhash_hash,

        char_count=char_count,
        token_count=token_count,
    )