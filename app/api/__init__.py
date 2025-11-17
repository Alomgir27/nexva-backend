from fastapi import APIRouter
from app.api.routes import auth, chatbots, domains, support, websockets, documents

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chatbots.router, prefix="/chatbots", tags=["chatbots"])
api_router.include_router(domains.router, prefix="/domains", tags=["domains"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(support.router, prefix="/support", tags=["support"])

