# rag_chat_service/auth.py
import logging
import httpx
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """
    Получает user_id из JWT токена через Django API.
    """
    token = credentials.credentials
    
    try:
        # Отправляем токен в Django для валидации и получения user_id
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "http://django:8000/api/auth/me/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get("id")
            else:
                logger.error(f"JWT validation failed: {response.status_code}")
                raise HTTPException(status_code=401, detail="Invalid token")
                
    except Exception as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")