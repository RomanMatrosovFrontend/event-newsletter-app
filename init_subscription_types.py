# init_subscription_types.py
from app.database import get_db
from app.models import SubscriptionType

def init_subscription_types(db):
    types = [
        {"code": "weekly"},
        {"code": "monthly"},
        {"code": "bi_monthly"},
    ]
    for type_data in types:
        if not db.query(SubscriptionType).filter(SubscriptionType.code == type_data["code"]).first():
            db.add(SubscriptionType(**type_data))
    db.commit()

if __name__ == "__main__":
    db = next(get_db())
    init_subscription_types(db)

