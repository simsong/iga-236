"""
Lambda function for password lab.
This function will serve the password cracker and gets reports of correct decrypts.
"""
import os, json, hmac, hashlib, logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
import boto3


LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s")

DDB = boto3.resource("dynamodb")
TAB_CHAL = DDB.Table(os.environ["DDB_CHALLENGES_TABLE"])   # was assignments
TAB_SUB  = DDB.Table(os.environ["DDB_SUBMISSIONS_TABLE"])
ALLOWED = {o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()}


def _cors_headers(origin: str | None) -> Dict[str, str]:
    allow = origin if origin in ALLOWED else (next(iter(ALLOWED)) if ALLOWED else "*")
    return {
        "Access-Control-Allow-Origin": allow,
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS, POST",
        "Access-Control-Allow-Credentials": "true" if allow != "*" else "false",
        "Content-Type": "application/json; charset=utf-8",
    }

def _resp(status: int, data: Dict[str, Any], origin: str | None) -> Dict[str, Any]:
    return {"statusCode": status, "headers": _cors_headers(origin), "body": json.dumps(data)}

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _secure_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)

def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def _json(event) -> Dict[str, Any]:
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        import base64; raw = base64.b64decode(raw).decode("utf-8", "replace")
    try:
        return json.loads(raw or "{}")
    except Exception:
        return {}

def _load_challenge(challenge_id: str) -> Dict[str, Any]:
    return TAB_CHAL.get_item(Key={"challenge_id": challenge_id}).get("Item") or {}

def _store_first_success(student_id: str, assignment_id: str) -> Tuple[bool, str]:
    pk = f"{student_id}#{assignment_id}"
    sk = "success"
    ts = _now_iso()
    receipt = f"{assignment_id}:{student_id}:{ts.replace('-','').replace(':','')}"
    try:
        TAB_SUB.put_item(
            Item={"pk": pk, "sk": sk, "accepted_at": ts, "receipt_id": receipt, "first_success": True},
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )
        return True, receipt
    except DDB.meta.client.exceptions.ConditionalCheckFailedException:
        return False, receipt

def handler(event, _context):
    origin = event.get("headers", {}).get("origin")
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return _resp(200, {"ok": True}, origin)

    path = event.get("rawPath") or event.get("path", "")
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    if path == "/api/v1/cracks/submit" and method == "POST":
        body = _json(event)
        challenge_id = (body.get("challenge_id") or "").strip()
        candidate    = (body.get("candidate") or "")
        if not challenge_id or not candidate:
            return _resp(400, {"ok": False, "error": "missing challenge_id or candidate"}, origin)
        if len(candidate) > 256:
            return _resp(400, {"ok": False, "error": "candidate too long"}, origin)

        chal = _load_challenge(challenge_id)
        if not chal:
            return _resp(404, {"ok": False, "error": "challenge not found"}, origin)

        salt_hex = chal.get("salt"); want_hex = chal.get("hash")
        if not salt_hex or not want_hex:
            return _resp(500, {"ok": False, "error": "challenge misconfigured"}, origin)

        got = _sha256_hex(bytes.fromhex(salt_hex) + candidate.encode("utf-8"))
        if not _secure_eq(got, want_hex):
            return _resp(200, {"ok": False, "message": "Not correct"}, origin)

        first, receipt = _store_first_success(chal["student_id"], chal["assignment_id"])
        return _resp(200, {"ok": True, "accepted_at": _now_iso(), "first_success": first, "receipt_id": receipt}, origin)

    return _resp(404, {"ok": False, "error": "not found"}, origin)
