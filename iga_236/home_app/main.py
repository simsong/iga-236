"""
Lambda function for password lab.
This function will serve the password cracker and gets reports of correct decrypts.
"""
import base64
import binascii
import functools
import json
import logging
import mimetypes
import os
import sys
from datetime import datetime
from os.path import dirname,join,isdir
from pathlib import Path
from typing import Optional,Any,Dict
from zoneinfo import ZoneInfo

import jinja2
import boto3

# GitHub Repository
GITHUB_REPO_URL = "https://github.com/simsong/iga-236"

MY_DIR = dirname(__file__)
TEMPLATE_DIR = join(MY_DIR,"templates")
STATIC_DIR = Path(__file__).parent / "static"
LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s")

sys.path.append(MY_DIR)

# Content Types
JPEG_MIME_TYPE = "image/jpeg"
JSON_CONTENT_TYPE = "application/json"
HTML_CONTENT_TYPE = "text/html; charset=utf-8"
PNG_CONTENT_TYPE = "image/png"
CSS_CONTENT_TYPE = "text/css; charset=utf-8"

# HTTP Headers
CORS_HEADER = "Access-Control-Allow-Origin"
CORS_WILDCARD = "*"
CONTENT_TYPE_HEADER = "Content-Type"

# HTTP Status Codes
HTTP_OK = 200
HTTP_FOUND = 302
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500

COURSE_DOMAIN='cybersecurity-policy.org'
LAB_TIMEZONE = ZoneInfo("America/New_York")  # Eastern timezone for lab deadlines

# API Endpoints
API_PATH = "/api/v1"
API_ENDPOINT = f'https://{COURSE_DOMAIN}{API_PATH}'
STAGE_ENDPOINT = f'https://stage.{COURSE_DOMAIN}{API_PATH}'

DDB = boto3.resource("dynamodb")
guids_table = DDB.Table(os.environ["GUIDS_TABLE_NAME"])   # was assignments



def eastern_filter(value):
    """Format a time_t (epoch seconds) as ISO 8601 in EST5EDT."""
    if value in (None, jinja2.Undefined):  # catch both
        return ""
    try:
        dt = datetime.fromtimestamp(round(value), tz=LAB_TIMEZONE)
    except TypeError as e:
        LOGGER.debug("value=%s type(value)=%s e=%s", value, type(value), e)
        return "n/a"
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


# jinja2 environment for template substitution
@functools.lru_cache(maxsize=1)
def env():
    """Return the jinja2 environment"""
    e = jinja2.Environment(
        loader=jinja2.FileSystemLoader( ["templates", TEMPLATE_DIR] )
    )
    e.globals["API_PATH"] = API_PATH
    e.filters["eastern"] = eastern_filter
    e.globals["GITHUB_REPO_URL"] = GITHUB_REPO_URL
    return e

################################################################

def resp_json( status: int, body: Dict[str, Any],
               headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """End HTTP event processing with a JSON object"""
    LOGGER.debug("resp_json(status=%s) body=%s", status, body)
    return {
        "statusCode": status,
        "headers": {
            CONTENT_TYPE_HEADER: JSON_CONTENT_TYPE,
            CORS_HEADER: CORS_WILDCARD,
            **(headers or {}),
        },
        "body": json.dumps(body, default=str),
    }

def resp_text(    status: int,    body: str, headers: Optional[Dict[str, str]] = None,
                  cookies: Optional[list[str]] = None) -> Dict[str, Any]:
    """End HTTP event processing with text/html"""
    LOGGER.debug("resp_text(status=%s)", status)
    return {
        "statusCode": status,
        "headers": {
            CONTENT_TYPE_HEADER: HTML_CONTENT_TYPE,
            CORS_HEADER: CORS_WILDCARD,
            **(headers or {}),
        },
        "body": body,
        "cookies": cookies or [],
    }

def resp_png( status: int, png_bytes: bytes, headers: Optional[Dict[str, str]] = None,
              cookies: Optional[list[str]] = None ) -> Dict[str, Any]:
    """End HTTP event processing with binary PNG"""
    LOGGER.debug("resp_png(status=%s, len=%s)", status, len(png_bytes))
    return {
        "statusCode": status,
        "headers": {
            CONTENT_TYPE_HEADER: PNG_CONTENT_TYPE,
            CORS_HEADER: CORS_WILDCARD,
            **(headers or {}),
        },
        "body": base64.b64encode(png_bytes).decode("ascii"),
        "isBase64Encoded": True,
        "cookies": cookies or [],
    }


def redirect( location: str, extra_headers: Optional[dict] = None, cookies: Optional[list] = None ) -> Dict[str, Any]:
    """End HTTP event processing with redirect to another website"""
    LOGGER.debug("redirect(%s,%s,%s)", location, extra_headers, cookies)
    headers = {"Location": location}
    if extra_headers:
        headers.update(extra_headers)
    return {"statusCode": HTTP_FOUND, "headers": headers, "cookies": cookies or [], "body": ""}

def error_404(page) -> Dict[str, Any]:
    """Generate an error"""
    template = env().get_template("404.html")
    return resp_text(HTTP_NOT_FOUND, template.render(page=page))


def static_file(file_path_str) -> Dict[str, Any]:
    """Serve a static file"""
    requested_path = (STATIC_DIR / file_path_str).resolve()
    if not requested_path.is_relative_to(STATIC_DIR) or not requested_path.is_file():
        return error_404(file_path_str)

    mime_type, _ = mimetypes.guess_type(requested_path)
    mime_type = mime_type or "application/octet-stream"

    # Check if it's a binary file (images, fonts, etc.)
    is_binary = not mime_type.startswith(("text/", "application/json", "application/javascript"))

    with open(join(STATIC_DIR, file_path_str), "rb" if is_binary else "r") as f:
        content = f.read()

    # pylint: disable=line-too-long
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": mime_type,
            "Cache-Control": "public, max-age=31536000, immutable" if "assets/" in file_path_str else "no-cache"
        },
        "isBase64Encoded": is_binary,
        "body": base64.b64encode(content).decode("utf-8") if is_binary else content
    }

def lambda_handler(event, _context) -> Dict[str, Any]:
    """Handle the lambda"""
    origin = event.get("headers", {}).get("origin")
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return resp_json(200, {"ok": True}, origin)

    path   = event.get("rawPath") or event.get("path", "")
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    sourceIp = event.get("requestContext",{}).get("http",{}).get("sourceIp")
    body   = event.get("body")
    if event.get("isBase64Encoded"):
        try:
            body = base64.b64decode(body or "").decode("utf-8", "replace")
        except binascii.Error:
            body = None
    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        payload = {}

    match ( method, path):
        case ("GET", "/api/v1/decrypt/submit"):
            # Extract guid from ?guid= parameter
            query_params = event.get("queryStringParameters") or {}
            guid = query_params.get("guid")
            if not guid:
                return resp_json(HTTP_BAD_REQUEST, {"ok": False, "error": "Missing guid"})

            now = datetime.now().isoformat()
            try:
                guids_table.put_item(Item={'guid':guid,
                                           'sk':now,
                                           't':now,
                                           'sourceIp':sourceIp})
                return resp_json(200, {"ok": True})
            except Exception as e:
                LOGGER.error(f"DynamoDB Error: {e}")
                return resp_json(HTTP_INTERNAL_ERROR, {"ok": False, "error": "Database error"})

        # This must be last - catch all GETs, check for /static
        # used for serving css and javascript
        case ("GET", p):
            if p.startswith("/static"):
                return static_file(p.removeprefix("/static/"))
            return error_404(p)

        case (_m,_p):
            template = env().get_template("404.html")
            return resp_text(HTTP_FOUND, template.render())
