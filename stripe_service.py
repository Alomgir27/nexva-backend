import stripe
import os
from typing import Optional, Dict
import models
from plan_config import PLANS

stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')

def create_customer(email: str, user_id: int) -> Optional[str]:
    try:
        customer = stripe.Customer.create(
            email=email,
            metadata={'user_id': user_id}
        )
        return customer.id
    except Exception as e:
        print(f"Error creating Stripe customer: {e}")
        return None

def create_checkout_session(user: models.User, plan_tier: str, success_url: str, cancel_url: str, db) -> Optional[Dict]:
    try:
        plan = PLANS.get(plan_tier)
        if not plan or not plan['stripe_price_id']:
            return None
        
        if not user.stripe_customer_id:
            customer_id = create_customer(user.email, user.id)
            if customer_id:
                user.stripe_customer_id = customer_id
                db.commit()
        else:
            customer_id = user.stripe_customer_id
        
        if not customer_id:
            return None
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': plan['stripe_price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': user.id,
                'plan_tier': plan_tier
            }
        )
        
        return {'session_id': session.id, 'url': session.url}
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return None

def create_portal_session(customer_id: str, return_url: str) -> Optional[str]:
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url
    except Exception as e:
        print(f"Error creating portal session: {e}")
        return None

def get_subscription_info(subscription_id: str) -> Optional[Dict]:
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return {
            'id': subscription.id,
            'status': subscription.status,
            'current_period_end': subscription.current_period_end,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'plan_id': subscription['items']['data'][0]['price']['id'] if subscription.get('items') else None
        }
    except Exception as e:
        print(f"Error retrieving subscription: {e}")
        return None

def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> bool:
    try:
        if at_period_end:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            stripe.Subscription.delete(subscription_id)
        return True
    except Exception as e:
        print(f"Error canceling subscription: {e}")
        return False

def handle_webhook(payload: bytes, sig_header: str, db) -> bool:
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        print("Invalid payload")
        return False
    except stripe.error.SignatureVerificationError:
        print("Invalid signature")
        return False
    
    event_type = event['type']
    data = event['data']['object']
    
    if event_type == 'customer.subscription.created':
        handle_subscription_created(data, db)
    elif event_type == 'customer.subscription.updated':
        handle_subscription_updated(data, db)
    elif event_type == 'customer.subscription.deleted':
        handle_subscription_deleted(data, db)
    elif event_type == 'invoice.paid':
        handle_invoice_paid(data, db)
    elif event_type == 'invoice.payment_failed':
        handle_invoice_payment_failed(data, db)
    
    return True

def handle_subscription_created(subscription_data: Dict, db):
    try:
        customer_id = subscription_data['customer']
        subscription_id = subscription_data['id']
        status = subscription_data['status']
        current_period_end = subscription_data['current_period_end']
        
        user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
        if not user:
            return
        
        price_id = subscription_data['items']['data'][0]['price']['id']
        plan_tier = get_plan_tier_from_price_id(price_id)
        
        subscription = models.Subscription(
            user_id=user.id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan_tier=plan_tier,
            status=status,
            current_period_end=models.datetime.fromtimestamp(current_period_end)
        )
        db.add(subscription)
        
        user.subscription_tier = plan_tier
        db.commit()
        print(f"Subscription created for user {user.id}: {plan_tier}")
    except Exception as e:
        print(f"Error handling subscription created: {e}")
        db.rollback()

def handle_subscription_updated(subscription_data: Dict, db):
    try:
        subscription_id = subscription_data['id']
        status = subscription_data['status']
        current_period_end = subscription_data['current_period_end']
        
        subscription = db.query(models.Subscription).filter(
            models.Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = status
            subscription.current_period_end = models.datetime.fromtimestamp(current_period_end)
            
            price_id = subscription_data['items']['data'][0]['price']['id']
            plan_tier = get_plan_tier_from_price_id(price_id)
            subscription.plan_tier = plan_tier
            
            user = db.query(models.User).filter(models.User.id == subscription.user_id).first()
            if user:
                user.subscription_tier = plan_tier if status == 'active' else 'free'
            
            db.commit()
            print(f"Subscription updated: {subscription_id}")
    except Exception as e:
        print(f"Error handling subscription updated: {e}")
        db.rollback()

def handle_subscription_deleted(subscription_data: Dict, db):
    try:
        subscription_id = subscription_data['id']
        
        subscription = db.query(models.Subscription).filter(
            models.Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if subscription:
            user = db.query(models.User).filter(models.User.id == subscription.user_id).first()
            if user:
                user.subscription_tier = 'free'
            
            subscription.status = 'canceled'
            db.commit()
            print(f"Subscription deleted for user {subscription.user_id}")
    except Exception as e:
        print(f"Error handling subscription deleted: {e}")
        db.rollback()

def handle_invoice_paid(invoice_data: Dict, db):
    try:
        customer_id = invoice_data['customer']
        subscription_id = invoice_data.get('subscription')
        
        if subscription_id:
            subscription = db.query(models.Subscription).filter(
                models.Subscription.stripe_subscription_id == subscription_id
            ).first()
            if subscription:
                subscription.status = 'active'
                db.commit()
                print(f"Invoice paid for subscription: {subscription_id}")
    except Exception as e:
        print(f"Error handling invoice paid: {e}")
        db.rollback()

def handle_invoice_payment_failed(invoice_data: Dict, db):
    try:
        customer_id = invoice_data['customer']
        subscription_id = invoice_data.get('subscription')
        
        if subscription_id:
            subscription = db.query(models.Subscription).filter(
                models.Subscription.stripe_subscription_id == subscription_id
            ).first()
            if subscription:
                subscription.status = 'past_due'
                db.commit()
                print(f"Payment failed for subscription: {subscription_id}")
    except Exception as e:
        print(f"Error handling payment failed: {e}")
        db.rollback()

def get_plan_tier_from_price_id(price_id: str) -> str:
    for tier, plan in PLANS.items():
        if plan.get('stripe_price_id') == price_id:
            return tier
    return 'free'

