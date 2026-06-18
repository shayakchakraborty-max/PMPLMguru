"""
blob_store.py — document storage for receipts, contracts and engagement letters.

Two backends behind one contract (put_blob / get_blob / blob_url):
  * Amazon S3 when BLOB_BUCKET (+ AWS creds / role) is set — the production path;
    objects at s3://$BLOB_BUCKET/<owner>/<scope>/<key>, served via presigned GET URLs.
  * Local disk under BRAIN_DATA_DIR/blobs otherwise — the zero-infra fallback (works
    locally; mount EFS to persist on App Runner). Same API, so wiring is a deploy flip.

Used by firm_ops (expense receipts) and clients (signed contracts / engagement-letter
PDFs). Endpoints in main.py: POST /blob (upload base64), GET /blob?owner=&key= .
"""

import os
import json
import time
import base64
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.getenv("BRAIN_DATA_DIR", "").strip() or os.path.join(_HERE, "brain_data")
_BLOB_DIR = os.path.join(_DATA_DIR, "blobs")
_BUCKET = os.getenv("BLOB_BUCKET", "").strip()
_REGION = os.getenv("AWS_REGION", "").strip() or None
_MAX_BYTES = 8 * 1024 * 1024  # 8 MB cap

_s3 = None
_USE_S3 = False
if _BUCKET:
    try:
        import boto3  # type: ignore
        _s3 = boto3.client("s3", region_name=_REGION)
        _USE_S3 = True
        print(f"[blob_store] S3 backend active (bucket {_BUCKET}).", flush=True)
    except Exception as e:  # pragma: no cover
        print(f"[blob_store] BLOB_BUCKET set but boto3/S3 unavailable ({e}); using local disk.", flush=True)
        _USE_S3 = False


def _owner(o):
    return (o or "").strip() or "demo"


def _safe(name):
    return "".join(c for c in (name or "file") if c.isalnum() or c in ("-", "_", ".", " ")).strip().replace(" ", "_")[:80] or "file"


def _key(scope, filename):
    h = hashlib.sha1(f"{scope}:{filename}:{time.time()}".encode()).hexdigest()[:12]
    return f"{(scope or 'doc').strip('/')}/{h}_{_safe(filename)}"


def put_blob(body):
    """Store a base64 document. body: {owner, scope, filename, content_base64, content_type}."""
    owner = _owner(body.get("owner"))
    b64 = body.get("content_base64") or ""
    if "," in b64[:64] and b64[:5] == "data:":  # strip data URL prefix if present
        b64 = b64.split(",", 1)[1]
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return {"error": "invalid base64 content"}
    if not raw:
        return {"error": "empty document"}
    if len(raw) > _MAX_BYTES:
        return {"error": f"document too large (> {_MAX_BYTES // (1024*1024)} MB)"}
    filename = _safe(body.get("filename") or "document")
    scope = (body.get("scope") or "doc").strip()
    ctype = (body.get("content_type") or "application/octet-stream").strip()
    key = _key(scope, filename)
    full = f"{owner}/{key}"
    if _USE_S3:
        try:
            _s3.put_object(Bucket=_BUCKET, Key=full, Body=raw, ContentType=ctype, Metadata={"owner": owner, "filename": filename})
            return {"ok": True, "backend": "s3", "key": full, "filename": filename, "size": len(raw), "url": blob_url(owner, full)}
        except Exception as e:  # pragma: no cover
            print(f"[blob_store] s3 put failed: {e}", flush=True)
            return {"error": "upload failed"}
    # local-disk fallback
    try:
        path = os.path.join(_BLOB_DIR, owner, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(raw)
        with open(path + ".meta", "w", encoding="utf-8") as f:
            json.dump({"filename": filename, "content_type": ctype, "size": len(raw), "ts": int(time.time())}, f)
        return {"ok": True, "backend": "local", "key": full, "filename": filename, "size": len(raw),
                "url": f"/blob?owner={owner}&key={full}"}
    except Exception as e:  # pragma: no cover
        print(f"[blob_store] local put failed: {e}", flush=True)
        return {"error": "upload failed"}


def blob_url(owner, key, expires=3600):
    """Presigned GET URL (S3) or the local /blob endpoint path."""
    owner = _owner(owner)
    if _USE_S3:
        try:
            return _s3.generate_presigned_url("get_object", Params={"Bucket": _BUCKET, "Key": key}, ExpiresIn=expires)
        except Exception:  # pragma: no cover
            return None
    return f"/blob?owner={owner}&key={key}"


def get_blob(owner, key):
    """Return the document (base64) — for the local backend; for S3 callers use the presigned url."""
    owner = _owner(owner)
    if not key or not key.startswith(owner + "/"):
        return {"error": "not found"}
    if _USE_S3:
        return {"ok": True, "backend": "s3", "url": blob_url(owner, key)}
    rel = key[len(owner) + 1:]
    path = os.path.join(_BLOB_DIR, owner, rel)
    if not os.path.exists(path):
        return {"error": "not found"}
    try:
        with open(path, "rb") as f:
            raw = f.read()
        meta = {}
        if os.path.exists(path + ".meta"):
            meta = json.load(open(path + ".meta", encoding="utf-8"))
        return {"ok": True, "backend": "local", "filename": meta.get("filename"),
                "content_type": meta.get("content_type", "application/octet-stream"),
                "content_base64": base64.b64encode(raw).decode("ascii")}
    except Exception:  # pragma: no cover
        return {"error": "read failed"}


def meta():
    return {"backend": "s3" if _USE_S3 else "local", "bucket": _BUCKET or None,
            "max_mb": _MAX_BYTES // (1024 * 1024),
            "endpoints": ["POST /blob", "GET /blob?owner=&key="]}


def run_blob_tests():
    cases = []
    o = "__blob_test__"
    payload = base64.b64encode(b"hello receipt PDF bytes").decode("ascii")
    up = put_blob({"owner": o, "scope": "receipt", "filename": "ola receipt.pdf", "content_base64": payload, "content_type": "application/pdf"})
    cases.append(("put", up.get("ok") and up.get("key", "").startswith(o + "/receipt/") and up.get("size") == 23))
    got = get_blob(o, up.get("key"))
    cases.append(("get", got.get("ok") and (got.get("content_base64") == payload or got.get("backend") == "s3")))
    cases.append(("reject_bad", "error" in put_blob({"owner": o, "content_base64": "%%notbase64%%@@"})))
    # cleanup local
    try:
        import shutil
        shutil.rmtree(os.path.join(_BLOB_DIR, o), ignore_errors=True)
    except Exception:
        pass
    passed = sum(1 for _, ok in cases if ok)
    return {"summary": {"total": len(cases), "passed": passed, "deployment_ready": passed == len(cases),
                        "backend": "s3" if _USE_S3 else "local"},
            "results": [{"case": n, "ok": ok} for n, ok in cases]}


if __name__ == "__main__":
    print(json.dumps(run_blob_tests(), indent=2))
