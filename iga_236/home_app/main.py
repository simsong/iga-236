"""
improved main.py using powertools.
"""

# pylint: disable=missing-function-docstring

import os
import mimetypes
from typing import cast, Any
from datetime import datetime

# https://docs.aws.amazon.com/powertools/python/latest/tutorial/
# https://docs.aws.amazon.com/powertools/python/latest/core/event_handler/api_gateway/#using-regex-patterns

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response, content_types
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = Logger(service="APP") # Automatically picks up LOG_LEVEL from env
app = APIGatewayHttpResolver(enable_validation=False)
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = Environment(loader=FileSystemLoader(template_dir))

### ADD ###
DDB = boto3.resource("dynamodb")
guids_table = DDB.Table(os.environ["GUIDS_TABLE_NAME"])   # was assignments
### ADD END ###

def get_dir_content(which, proxy: str):
    """Safely finds and reads static files from the /static folder."""
    logger.debug("get_dir_context(%s, %s)", which, proxy)
    base_dir = os.path.dirname(__file__)
    # Securely join and resolve the path to prevent directory traversal
    path = os.path.abspath(os.path.join(base_dir, which, proxy))
    static_root = os.path.abspath(os.path.join(base_dir, which))

    if not path.startswith(static_root):
        return None, 403 # Forbidden (Traversal attempt)

    if not os.path.exists(path) or not os.path.isfile(path):
        return None, 404 # Not Found

    mtype, _ = mimetypes.guess_type(path)
    # Ensure common web types are correct
    if path.endswith('.js'):
        mtype = 'application/javascript'
    elif path.endswith('.css'):
        mtype = 'text/css'
    if mtype is None:
        mtype = 'application/octet-stream'

    # Read as binary to let Powertools handle auto-Base64 encoding if needed
    with open(path, "rb") as f:
        return f.read(), mtype

def render_dynamic_template(template_name: str) -> Response:
    """Helper to find a template, inject query params, and return a Response."""
    logger.debug("render_dynamic_template(%s)", template_name)

    # Extract query parameters to pass to the template automatically
    # Example: ?name=Bob becomes {{ name }} in the template
    query_params = app.current_event.query_string_parameters or {}

    try:
        template = jinja_env.get_template(template_name)
        html = template.render(**query_params, path_name=template_name)
        return Response(
            status_code=200,
            content_type=content_types.TEXT_HTML,
            body=html
        )
    except TemplateNotFound:
        logger.warning("Template not found: %s",template_name)
        return Response(
            status_code=404,
            body="404 - Page Not Found",
            content_type=content_types.TEXT_PLAIN
        )

@app.not_found
def handle_not_found_route(rt) -> Response:
    """Log the event details, return a custom message, or raise a different error"""
    return Response(status_code=404,
                    body=f"Not found: '{type(rt)} {str(rt)}'",
                    content_type=content_types.TEXT_PLAIN)

@app.get("/")
def get_index():
    """Explicitly handle the root path."""
    return render_dynamic_template("index.html")

@app.get("/hello")
def hello() -> dict:
    return {"message": "Hello world!"}

@app.get("/hello/<name>")
def hello_name(name):
    logger.info(f"Request from {name} received")
    return {"message": f"hello {name}!"}

@app.get("/static/.+")
def serve_static():
    """Serves CSS, JS, and Images from the static/ directory."""
    file_path = app.current_event.path.replace("/static/", "")

    logger.debug("serve_static(%s)",file_path)
    content, status_or_type = get_dir_content("static",file_path)

    if status_or_type == 403:
        return Response(status_code=403, body="Forbidden", content_type="text/plain")
    if status_or_type == 404:
        return Response(status_code=404, body="File Not Found", content_type="text/plain")

    return Response(
        status_code=200,
        content_type=status_or_type,
        body=content # Powertools auto-encodes binary 'bytes' to Base64
    )

@app.get("/assets/.+")
def serve_assets():
    """Serves CSS, JS, and Images from the assets/ directory."""
    file_path = app.current_event.path.replace("/assets/", "")
    logger.debug("serve_assets(%s)",file_path)
    content, status_or_type = get_dir_content("assets",file_path)

    if status_or_type == 403:
        return Response(status_code=403, body="Forbidden", content_type="text/plain")
    if status_or_type == 404:
        return Response(status_code=404, body="File Not Found", content_type="text/plain")

    return Response(
        status_code=200,
        content_type=status_or_type,
        body=content # Powertools auto-encodes binary 'bytes' to Base64
    )


@app.get("/api/v1/ping")
def app_point():
    now = datetime.now().isoformat()
    return {"type":"pong","t":now}

@app.get("/api/v1/decrypt/submit")
def app_submit():
    event = APIGatewayProxyEventV2(cast(dict[str, Any], app.current_event))
    query_params = event.query_string_parameters or {}
    guid = query_params.get("guid")
    if not guid:
        return Response(status_code=403,
                        content_type=content_types.APPLICATION_JSON,
                        body={"ok": False, "error": "Missing guid"})

    now = datetime.now().isoformat()
    try:
        guids_table.put_item(Item={'guid':guid,
                                   'sk':now,
                                   't':now,
                                   'sourceIp':event.request_context.http.source_ip})
        return Response(status_code=200,
                        content_type=content_types.APPLICATION_JSON,
                        body={"ok": True})

    except Exception as e: # pylint: disable=broad-exception-caught
        logger.error("DynamoDB Error") # includes stack trace
        return Response(status_code=500,
                        content_type=content_types.APPLICATION_JSON,
                        body={"ok": False, "error": "Database error", "e":str(e)})

@app.get("/<proxy+>")
def catch_all_templates(proxy):
    """
    Greedy route that catches any other path and tries to find
    a matching .html file in the templates folder.
    """
    logger.info("catch_all_templates(%s)",proxy)
    return render_dynamic_template(proxy)

# --- 5. Main Lambda Handler ---
def lambda_handler(event, context):
    # Handle EventBridge/CloudWatch Heartbeats (Warm-up)
    logger.debug("event=%s context=%s",event,context)
    if event.get("source") == "aws.events":
        logger.info("aws.events event=%s",event)
        return {"warmed": True}

    # app.resolve handles the routing and converts our Response
    # objects into the dictionaries Lambda expects.
    return app.resolve(event, context)
