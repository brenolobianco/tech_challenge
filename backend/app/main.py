import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.routers import campaigns, upload, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RevfySegment",
    description="""
## Marketing Audience Campaign Builder

RevfySegment allows you to upload CSV files with user data and automatically
generate marketing campaigns based on predefined segmentation rules.

### Segmentation Rules

| Campaign | Rule |
|---|---|
| **Starter** | age < 30 AND income < 3000 |
| **Growth** | 30 ≤ age ≤ 50 AND 3000 ≤ income ≤ 10000 |
| **Premium** | age > 50 OR income > 10000 |
| **High Value Youth** | age < 30 AND income > 5000 |

### Features
- CSV upload with row-level validation
- Automatic campaign generation via background processing
- Real-time status updates via **SSE (Server-Sent Events)**
- Rate limiting on upload endpoint
- Paginated endpoints with filtering support
""",
    version="1.0.0",
    contact={"name": "Revfy Engineering"},
    openapi_tags=[
        {
            "name": "Upload",
            "description": "Upload CSV files and track processing status via SSE.",
        },
        {
            "name": "Campaigns",
            "description": "List and inspect auto-generated marketing campaigns.",
        },
        {
            "name": "Users",
            "description": "Browse and filter uploaded users.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "error",
            "message": str(exc.detail),
            "details": None,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "details": None,
        },
    )


app.include_router(upload.router, tags=["Upload"])
app.include_router(campaigns.router, tags=["Campaigns"])
app.include_router(users.router, tags=["Users"])
