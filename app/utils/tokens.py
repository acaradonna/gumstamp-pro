from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from typing import Optional, Dict, Any
from ..settings import settings


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=settings.secret_key, salt="gumstamp")


def sign_token(data: Dict[str, Any]) -> str:
    s = _serializer()
    return s.dumps(data)


def verify_token(token: str, max_age: int = 60 * 60 * 24 * 14) -> Optional[Dict[str, Any]]:
    s = _serializer()
    try:
        return s.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
