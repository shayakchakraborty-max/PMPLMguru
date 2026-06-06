"""
doc_store.py — the RAG ON-RAMP.

A keyless, dependency-free document store + retriever so the consulting brain can
ground answers on the OWNER'S OWN documents (P&L, policies, vendor terms, notes),
not just the playbook + web. Pure-Python TF-IDF over chunked text, persisted as
JSONL under BRAIN_DATA_DIR.

This is deliberately a drop-in shape: ingest() / search() / list_docs(). When real
scale arrives, swap the in-file index for Qdrant/embeddings behind the same API —
the rest of the platform doesn't change.
"""

import os
import re
import json
import math
import time
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.getenv("BRAIN_DATA_DIR", "").strip() or os.path.join(_HERE, "brain_data")
_DOCS_PATH = os.path.join(_DATA_DIR, "docs.jsonl")

_WORD = re.compile(r"[a-z0-9₹]{3,}")
_STOP = set((
    "the and for are with this that from have has had not you your our their they them was were will "
    "would can could should which what when where who whom whose into onto over under than then thus "
    "also been being but its it's are is am of to in on at by as or an a be we us i").split())


def _tok(text):
    return [w for w in _WORD.findall((text or "").lower()) if w not in _STOP]


def _tf(text):
    d = {}
    for t in _tok(text):
        d[t] = d.get(t, 0) + 1
    return d


def _ensure():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        return True
    except Exception as e:  # pragma: no cover
        print(f"[doc_store] cannot create {_DATA_DIR}: {e}", flush=True)
        return False


def _chunk(text, size=600):
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) > size and cur:
            chunks.append(cur.strip())
            cur = p
        else:
            cur = (cur + " " + p).strip()
    if cur:
        chunks.append(cur.strip())
    # hard-wrap any monster chunk (tables with no sentence breaks)
    out = []
    for c in chunks:
        while len(c) > size * 2:
            out.append(c[:size])
            c = c[size:]
        out.append(c)
    return out


def _read():
    out = []
    try:
        if os.path.exists(_DOCS_PATH):
            with open(_DOCS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            out.append(json.loads(line))
                        except Exception:
                            continue
    except Exception as e:  # pragma: no cover
        print(f"[doc_store] read failed: {e}", flush=True)
    return out


def ingest(name, text, workspace="default"):
    """Chunk + index a document. Returns how many chunks were stored."""
    if not _ensure():
        return {"ingested_chunks": 0, "source": name, "error": "no data dir"}
    chunks = _chunk(text)
    n = 0
    try:
        with open(_DOCS_PATH, "a", encoding="utf-8") as f:
            for i, c in enumerate(chunks):
                rec = {"id": hashlib.sha1((name + str(i) + str(time.time())).encode()).hexdigest()[:12],
                       "workspace": workspace or "default", "source": name or "document",
                       "chunk": i, "text": c, "tf": _tf(c), "ts": int(time.time())}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    except Exception as e:  # pragma: no cover
        return {"ingested_chunks": 0, "source": name, "error": str(e)}
    return {"ingested_chunks": n, "source": name}


def list_docs(workspace=None):
    by = {}
    for d in _read():
        if workspace and d.get("workspace") != workspace:
            continue
        s = d.get("source", "document")
        by[s] = by.get(s, 0) + 1
    return [{"source": k, "chunks": v} for k, v in sorted(by.items())]


def search(query, k=4, workspace=None):
    """TF-IDF retrieval over the corpus. Never raises; [] if nothing relevant."""
    docs = [d for d in _read() if (not workspace or d.get("workspace") == workspace)]
    if not docs:
        return []
    N = len(docs)
    df = {}
    for d in docs:
        for t in set(d.get("tf", {})):
            df[t] = df.get(t, 0) + 1
    qtf = _tf(query)
    if not qtf:
        return []

    def score(d):
        tf = d.get("tf", {})
        s = 0.0
        for t, qc in qtf.items():
            if t in tf:
                idf = math.log((N + 1) / (df.get(t, 0) + 1)) + 1
                s += qc * tf[t] * idf
        ln = sum(tf.values()) or 1
        return s / math.sqrt(ln)

    ranked = sorted(((score(d), d) for d in docs), key=lambda x: x[0], reverse=True)
    out = []
    for sc, d in ranked[:k]:
        if sc <= 0:
            break
        out.append({"source": d.get("source"), "snippet": (d.get("text") or "")[:320], "score": round(sc, 3)})
    return out


def stats():
    docs = _read()
    return {"total_chunks": len(docs), "sources": len(list_docs()),
            "persisted": os.path.exists(_DOCS_PATH), "data_dir": _DATA_DIR}


if __name__ == "__main__":
    ingest("test-pnl", "Gross margin fell to 14% this year. Receivables are stuck at 85 days. Dead stock is 18% of inventory.")
    print(stats())
    print(search("what is the margin and receivables situation"))
