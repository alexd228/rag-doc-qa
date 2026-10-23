# rag-doc-qa

A small retrieval-augmented generation (RAG) demo with zero dependencies.

Point it at a folder of Markdown or text files, ask a question, and it
retrieves the most relevant passages and — if an LLM API key is available —
generates a grounded answer with citations.

## How it works

1. **Chunk** — documents are split into overlapping chunks (~700 chars,
   120-char overlap) so retrieval keeps local context.
2. **Index** — each chunk becomes a TF-IDF vector (pure standard library:
   `collections`, `math`, `re`). Cosine similarity does the ranking.
3. **Retrieve** — the question is vectorized the same way; top-k chunks win.
4. **Generate (optional)** — with `OPENAI_API_KEY` set, the question and
   retrieved context go to an OpenAI-compatible chat model, instructed to
   answer only from the context and cite `[file#chunk]` sources. Without a
   key, the retrieved passages print directly (retrieval-only mode).

## Quick start

```bash
# retrieval only — works offline, no key
python rag.py ask "When should I embed instead of referencing?"

# grounded answers with an LLM
OPENAI_API_KEY=sk-... python rag.py ask "How does CDC keep a migration in sync?"
```

Sample output (retrieval mode):

```text
--- mongodb-modeling.md#0 (score 0.412) ---
Embed when the relationship is one-to-few, when the child data is almost
always read together with the parent...
```

## Design choices

- **TF-IDF instead of embeddings** keeps the demo runnable anywhere with no
  installs and no API bill. The index class is the swap point: replace
  `TfidfIndex._vectorize` with an embedding call and the rest is unchanged.
- **Citations are mandatory** in the system prompt; a RAG answer you can't
  trace to a source is just a confident guess.
- The bundled `docs/` cover MongoDB data modeling and Kafka-based CDC —
  swap in your own folder with `--docs`.

## Layout

```text
rag.py            # chunking, TF-IDF index, retrieval, optional LLM answer
docs/             # sample knowledge base
```
