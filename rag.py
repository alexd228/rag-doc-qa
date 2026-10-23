#!/usr/bin/env python3
"""
rag-doc-qa — a small, dependency-free retrieval-augmented generation demo.

Pipeline:
  1. Ingest .md/.txt files from a folder and split them into overlapping chunks.
  2. Index the chunks with TF-IDF vectors (pure standard library).
  3. Given a question, retrieve the top-k most relevant chunks.
  4. If OPENAI_API_KEY is set, send question + retrieved context to an
     OpenAI-compatible chat model and print a grounded answer with sources.
     Without a key, print the retrieved passages themselves (retrieval-only
     mode) so the demo still runs end to end offline.

Usage:
    python rag.py ask "How should I model a one-to-many relationship?"
    python rag.py ask "..." --docs ./docs --top-k 3
    OPENAI_API_KEY=sk-... python rag.py ask "..."
"""
import argparse
import json
import math
import os
import re
import sys
import urllib.request
from collections import Counter

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = set("a an the is are was were be been of to in on for and or with "
                "as at by it its this that these those from you your we our".split())


def tokenize(text: str):
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


def chunk_text(text: str, size: int = 700, overlap: int = 120):
    text = re.sub(r"\s+", " ", text).strip()
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def load_chunks(docs_dir: str):
    chunks = []
    for name in sorted(os.listdir(docs_dir)):
        if not name.lower().endswith((".md", ".txt")):
            continue
        with open(os.path.join(docs_dir, name), encoding="utf-8") as f:
            for i, piece in enumerate(chunk_text(f.read())):
                chunks.append({"source": name, "index": i, "text": piece})
    return chunks


class TfidfIndex:
    def __init__(self, chunks):
        self.chunks = chunks
        self.docs_tokens = [tokenize(c["text"]) for c in chunks]
        n = len(chunks)
        df = Counter()
        for toks in self.docs_tokens:
            df.update(set(toks))
        self.idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}
        self.vectors = [self._vectorize(toks) for toks in self.docs_tokens]

    def _vectorize(self, toks):
        counts = Counter(toks)
        total = max(len(toks), 1)
        return {t: (c / total) * self.idf.get(t, 1.0) for t, c in counts.items()}

    @staticmethod
    def _cosine(a, b):
        dot = sum(v * b.get(t, 0.0) for t, v in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def search(self, query: str, top_k: int = 3):
        q = self._vectorize(tokenize(query))
        scored = [(self._cosine(q, v), self.chunks[i])
                  for i, v in enumerate(self.vectors)]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(s, c) for s, c in scored[:top_k] if s > 0]


def llm_answer(question: str, hits) -> str:
    key = os.environ["OPENAI_API_KEY"]
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    context = "\n\n".join(
        f"[{c['source']}#{c['index']}] {c['text']}" for _, c in hits)
    payload = {
        "model": model,
        "messages": [
            {"role": "system",
             "content": "Answer using ONLY the provided context. If the context "
                        "does not answer the question, say so. Cite sources like "
                        "[file.md#2] after each claim."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Ask questions over a folder of documents (RAG).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ask = sub.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--docs", default=os.path.join(os.path.dirname(__file__), "docs"))
    ask.add_argument("--top-k", type=int, default=3)
    args = ap.parse_args()

    chunks = load_chunks(args.docs)
    if not chunks:
        print(f"No documents found in {args.docs}", file=sys.stderr)
        return 1
    index = TfidfIndex(chunks)
    hits = index.search(args.question, args.top_k)
    if not hits:
        print("No relevant passages found.")
        return 0

    if os.environ.get("OPENAI_API_KEY"):
        print(llm_answer(args.question, hits))
        print("\nSources:")
        for s, c in hits:
            print(f"  - {c['source']}#{c['index']} (score {s:.3f})")
    else:
        print("Retrieval-only mode (set OPENAI_API_KEY for generated answers).\n")
        for s, c in hits:
            print(f"--- {c['source']}#{c['index']} (score {s:.3f}) ---")
            print(c["text"])
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
