import os

PLANS = {
    'free': {
        'name': 'Free',
        'chatbot_limit': 1,
        'price_monthly': 0,
        'stripe_price_id': None,
        'features': [
            '1 chatbot',
            'Unlimited domains',
            'Basic support',
            'Web scraping',
            'Document upload'
        ]
    },
    'basic': {
        'name': 'Basic',
        'chatbot_limit': 5,
        'price_monthly': 29,
        'stripe_price_id': os.getenv('STRIPE_PRICE_ID_BASIC', 'price_basic'),
        'features': [
            '5 chatbots',
            'Unlimited domains',
            'Priority support',
            'Web scraping',
            'Document upload',
            'Custom branding'
        ]
    },
    'pro': {
        'name': 'Pro',
        'chatbot_limit': 15,
        'price_monthly': 79,
        'stripe_price_id': os.getenv('STRIPE_PRICE_ID_PRO', 'price_pro'),
        'features': [
            '15 chatbots',
            'Unlimited domains',
            'Priority support',
            'Web scraping',
            'Document upload',
            'Custom branding',
            'Advanced analytics',
            'API access'
        ]
    },
    'enterprise': {
        'name': 'Enterprise',
        'chatbot_limit': -1,
        'price_monthly': 199,
        'stripe_price_id': os.getenv('STRIPE_PRICE_ID_ENTERPRISE', 'price_enterprise'),
        'features': [
            'Unlimited chatbots',
            'Unlimited domains',
            '24/7 dedicated support',
            'Web scraping',
            'Document upload',
            'Custom branding',
            'Advanced analytics',
            'API access',
            'White-label solution',
            'Custom integrations'
        ]
    }
}

def get_plan_limits(plan_tier: str) -> dict:
    return PLANS.get(plan_tier, PLANS['free'])

def can_create_chatbot(current_count: int, plan_tier: str) -> bool:
    plan = get_plan_limits(plan_tier)
    limit = plan['chatbot_limit']
    if limit == -1:
        return True
    return current_count < limit

