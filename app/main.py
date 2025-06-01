from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.routing import APIRoute
from app.api.routes import auth, users
from app.api.routes.videos import router as videos_router
from app.api.routes.replicate_videos import router as replicate_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="MyTenSecondStory Backend API - Create AI-enhanced 10-second video stories",
    version="1.0.0",
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
app.include_router(
    videos_router, prefix=f"{settings.API_V1_STR}/videos", tags=["videos"]
)
app.include_router(
    replicate_router, prefix=f"{settings.API_V1_STR}/replicate", tags=["replicate"]
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to MyTenSecondStory API",
        "version": "1.0.0",
        "features": [
            "User authentication",
            "Video upload and processing",
            "AI background removal via Replicate",
        ],
    }


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
