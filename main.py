from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import time
import uuid
import logging
from collections import deque

EMAIL = "24f2005453@ds.study.iitm.ac.in"

app = FastAPI()

START = time.time()

# Prometheus counter
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests"
)

# In-memory log buffer
LOGS = deque(maxlen=1000)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    REQUEST_COUNTER.inc()

    request_id = str(uuid.uuid4())

    entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id,
    }

    LOGS.append(entry)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/work")
def work(n: int = 1):
    for _ in range(n):
        pass
    return {
        "email": EMAIL,
        "done": n
    }


@app.get("/healthz")
def health():
    return {
        "status": "ok",
        "uptime_s": time.time() - START
    }


@app.get("/logs/tail")
def logs_tail(limit: int = 10):
    return list(LOGS)[-limit:]


@app.get("/metrics")
def metrics():
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
