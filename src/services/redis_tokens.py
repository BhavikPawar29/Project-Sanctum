from src.db.redis import redis_client

REFRESH_TTL = 7 * 24 * 60 * 60  # 7 days


def store_refresh_token(user_id:str, token: str):
    key = f"refresh_token:{user_id}"
    redis_client.setex(key, REFRESH_TTL, token)

def get_refresh_token(user_id:str):
    return redis_client.get(f"refresh_token:{user_id}")

def revoke_refresh_token(user_id:str):
    redis_client.delete(f"refresh_token:{user_id}")