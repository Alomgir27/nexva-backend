from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.database import init_db
from app.services.search import init_elasticsearch
from app.api import api_router
from app.api.routes import websockets

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_elasticsearch()
    yield

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(websockets.router, prefix="/ws")
app.include_router(websockets.router, prefix=settings.API_V1_STR) # For HTTP endpoints in websockets.py

@app.get("/")
def root():
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "endpoints": {
            "auth": f"{settings.API_V1_STR}/auth/*",
            "chatbots": f"{settings.API_V1_STR}/chatbots",
            "domains": f"{settings.API_V1_STR}/domains",
            "websocket": "/ws/chat/{api_key}",
            "widget": "/widget.js"
        }
    }

@app.get("/widget.js")
async def serve_widget():
    widget_path = os.path.join(os.path.dirname(__file__), "..", "widget", "widget.js")
    return FileResponse(
        widget_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "X-Content-Type-Options": "nosniff"
        }
    )

@app.options("/widget.js")
async def serve_widget_options():
    from fastapi import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/src/{filename:path}")
async def serve_widget_src(filename: str):
    from fastapi import HTTPException
    src_path = os.path.join(os.path.dirname(__file__), "..", "widget", "src", filename)
    
    widget_src_dir = os.path.join(os.path.dirname(__file__), "..", "widget", "src")
    if not os.path.abspath(src_path).startswith(os.path.abspath(widget_src_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(src_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        src_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "X-Content-Type-Options": "nosniff"
        }
    )

@app.options("/src/{filename:path}")
async def serve_widget_src_options(filename: str):
    from fastapi import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

