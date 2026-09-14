from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
import redis.asyncio as redis
from app.core.config import settings
from supabase import create_client, Client

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Initialize Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Initialize Supabase Admin client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

class ResendOTPRequest(BaseModel):
    email: EmailStr

@router.post("/resend-otp")
async def resend_otp(request: ResendOTPRequest, req: Request):
    email = request.email.lower().strip()
    redis_key = f"otp_resend_count:{email}"

    # 1. Check current resend count
    current_count_str = await redis_client.get(redis_key)
    current_count = int(current_count_str) if current_count_str else 0

    if current_count >= 5:
        # User is blocked
        ttl = await redis_client.ttl(redis_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"OTP resend limit exceeded. Try again in {ttl // 3600} hours and {(ttl % 3600) // 60} minutes."
        )

    # 2. Trigger Supabase OTP Resend
    # Note: To route this through Resend, Custom SMTP must be configured in the Supabase Dashboard!
    try:
        # We use the admin client or anon client to trigger resend. 
        # Actually, resend requires standard auth API
        res = supabase.auth.resend({
            "type": "signup",
            "email": email
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend OTP: {str(e)}"
        )

    # 3. Increment counter and handle 24h block logic
    new_count = await redis_client.incr(redis_key)
    
    if new_count >= 5:
        # Block for 24 hours (86400 seconds)
        await redis_client.expire(redis_key, 86400)
    elif new_count == 1:
        # Give them some initial window to use their 5 attempts, e.g., 1 hour.
        # But if we just want a strict "after 5 times, block 24hr", we can set the initial expire.
        # Let's say if they don't hit 5, the count expires in 1 hour.
        await redis_client.expire(redis_key, 3600)

    return {"message": "OTP resent successfully", "attempts_remaining": 5 - new_count}
