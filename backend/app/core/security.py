from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

security = HTTPBearer(auto_error=False)


def _raise_unauthorized(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if credentials is None or not credentials.credentials:
        _raise_unauthorized("Missing bearer token")

    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"])
    except JWTError:
        _raise_unauthorized("Invalid bearer token")

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        _raise_unauthorized("Invalid bearer token payload")

    return user_id
