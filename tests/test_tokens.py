from app.utils.tokens import sign_token, verify_token


def test_token_roundtrip():
    data = {"product_id": "p_1", "email": "a@b.com"}
    token = sign_token(data)
    out = verify_token(token)
    assert out["product_id"] == "p_1"
    assert out["email"] == "a@b.com"
