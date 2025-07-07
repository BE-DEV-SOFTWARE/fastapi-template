from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.core.config import EnvTag, settings

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.TAG == EnvTag.PROD:
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                str(origin)
                for origin in settings.BACKEND_CORS_ORIGINS
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
elif settings.TAG == EnvTag.STAG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        # allow_origin_regex=r"https://.*\.yourdomain.com", 
        # Remove allow_origins and add regex check if you want enable cors 
        # on preview URL for example (Vercel, or Coolify deployment for example)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
elif settings.TAG == EnvTag.DEV:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    raise Exception(f"Provided tag: {settings.TAG} is not supported")

app.include_router(api_router, prefix=settings.API_V1_STR)
