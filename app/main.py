# Here's your updated main.py file with the new AI routes added:

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.routing import APIRoute
from app.api.routes import auth, users, ai_enhancement, mobile_upload
from app.core.config import settings
from app.api.routes.ai_enhancement import router as ai_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])


# ⭐ ADD THESE TWO NEW ROUTES:
app.include_router(
    ai_enhancement.router, prefix=f"{settings.API_V1_STR}/ai", tags=["ai_enhancement"]
)
app.include_router(
    mobile_upload.router, prefix=f"{settings.API_V1_STR}/mobile", tags=["mobile_upload"]
)
app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])


@app.get("/")
async def root():
    return {"message": "Welcome to MyTenSecondStory API"}


@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"})


@app.get("/routes-simple", response_class=PlainTextResponse)
async def get_routes_simple():
    """
    Returns a concise list of all routes with their paths and methods.
    """
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ", ".join(route.methods)
            routes.append(f"{methods}: {route.path}")
    return "\n".join(routes)
