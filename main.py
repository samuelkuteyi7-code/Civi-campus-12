from fastapi.responses import FileResponse, JSONResponse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from App.config.limiter import limiter
from App.database.db import Base, engine
from App.routes import auth
from App.routes import sug
from App.routes import promise
from App.routes import report
from App.routes import media
from App.routes import article
from App.routes import chat
from App.routes import debate
from App.routes import insights
from App.routes import notification
from App.routes import profile
from App.routes import location
from App.routes import admin

# --- Error monitoring ---
# SENTRY_DSN must be set in your environment. If it's missing, Sentry simply
# no-ops instead of crashing the app, so this is safe to deploy either way.
sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.2,   # 20% of requests get performance tracing
    send_default_pii=False,   # don't auto-attach request bodies/user data
    environment=os.environ.get("ENVIRONMENT", "production"),
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CiviAI Campus API")

# --- Rate limiting ---
# Global default (100/min/IP) from App.config.limiter. Login, register, and
# media upload override this with tighter limits directly on their routes.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
# Locked to known frontends only. ALLOWED_ORIGINS can be set as a
# comma-separated env var for flexibility across environments without a
# code change (e.g. staging domains).
default_origins = "https://civi-campus-12.fastapicloud.dev,http://localhost:3000,http://localhost:8000"
allowed_origins = os.environ.get("ALLOWED_ORIGINS", default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sug.router)
app.include_router(promise.router)
app.include_router(report.router)
app.include_router(media.router)
app.include_router(article.router)
app.include_router(chat.router)
app.include_router(debate.router)
app.include_router(insights.router)
app.include_router(notification.router)
app.include_router(profile.router)
app.include_router(location.router)
app.include_router(admin.router)


@app.get("/")
def read_root():
    return FileResponse("index.html")


@app.get("/privacy")
def privacy_policy():
    return FileResponse("privacy.html")


# Generic fallback so unhandled exceptions return a clean JSON error instead
# of leaking stack traces, while Sentry still captures the full detail.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    sentry_sdk.capture_exception(exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
