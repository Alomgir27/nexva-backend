from fastapi import APIRouter
from app.api.routes import auth, chatbots, domains, support, websockets, documents, conversations, billing

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chatbots.router, prefix="/chatbots", tags=["chatbots"])
api_router.include_router(domains.router, prefix="/domains", tags=["domains"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(support.router, prefix="/support", tags=["support"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])

