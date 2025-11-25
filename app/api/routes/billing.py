from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import database
from app.services import auth

router = APIRouter()

@router.get("/subscription")
def get_subscription(
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Count user's chatbots
    chatbot_count = db.query(database.Chatbot).filter(
        database.Chatbot.user_id == current_user.id
    ).count()
    
    # Free tier limits
    return {
        "plan_tier": "free",
        "status": "active",
        "chatbot_count": chatbot_count,
        "chatbot_limit": 1,  # Free tier allows 1 chatbot
        "features": {
            "max_domains": 5,
            "max_messages": 1000
        }
    }

@router.post("/create-checkout-session")
def create_checkout_session(
    plan_data: dict,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return {
        "url": "https://checkout.stripe.com/pay/test_session",
        "session_id": "test_session_id"
    }

@router.post("/portal-session")
def create_portal_session(
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return {
        "url": "https://billing.stripe.com/session/test_portal"
    }

