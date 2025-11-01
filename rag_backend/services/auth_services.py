from fastapi import HTTPException, Header
from jose import jwt
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


class Auth_Services:
    @staticmethod
    def verify_token(authorization: str = Header(...)):
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token format")
        token = authorization.split(" ")[1]

        try:
            payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
            return payload  # contains user info like sub, email, etc.
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
