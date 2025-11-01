import os

PLANS = {
    'free': {
        'name': 'Free',
        'chatbot_limit': 1,
        'price_monthly': 0,
        'price_annual': 0,
        'stripe_price_id_monthly': None,
        'stripe_price_id_annual': None,
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
        'price_monthly': 9.99,
        'price_annual': 95.99,
        'stripe_price_id_monthly': os.getenv('STRIPE_PRICE_ID_BASIC_MONTHLY', 'price_basic_monthly'),
        'stripe_price_id_annual': os.getenv('STRIPE_PRICE_ID_BASIC_ANNUAL', 'price_basic_annual'),
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
        'price_monthly': 24.99,
        'price_annual': 239.99,
        'stripe_price_id_monthly': os.getenv('STRIPE_PRICE_ID_PRO_MONTHLY', 'price_pro_monthly'),
        'stripe_price_id_annual': os.getenv('STRIPE_PRICE_ID_PRO_ANNUAL', 'price_pro_annual'),
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
        'price_monthly': 49.99,
        'price_annual': 479.99,
        'stripe_price_id_monthly': os.getenv('STRIPE_PRICE_ID_ENTERPRISE_MONTHLY', 'price_enterprise_monthly'),
        'stripe_price_id_annual': os.getenv('STRIPE_PRICE_ID_ENTERPRISE_ANNUAL', 'price_enterprise_annual'),
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

