import json
import random
from faker import Faker
import os

fake = Faker()

def generate_users(n=100):
    tiers = ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'vip']
    countries = ["US", "UK", "CA", "AU", "DE", "FR", "ES", "IT", "NL", "SE","IN", "CN", "JP", "KR", "BR", "MX","ZA", "RU", "AR", "TR", "ID"]

    users = []
    for _ in range(n):
        level = random.randint(1, 50)
        user = {
            "player_id": fake.uuid4(),
            "level": level,
            "spend_tier": random.choice(tiers),
            "days_since_last_purchase": random.randint(0, 60),
            "total_spent": round(random.uniform(10, 20000), 2),
            "current_balance": round(random.uniform(0, 5000), 2),
            "country": random.choice(countries),
            "registration_date": fake.date_between(start_date='-5y', end_date='today').isoformat()
        }
        users.append(user)

    return users

def save_users_to_json(filepath="data/generated_users.json", n=100):
    users = generate_users(n)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(users, f, indent=2)
    print(f"[✔] Generated {n} users and saved to {filepath}")

if __name__ == "__main__":
    save_users_to_json()
