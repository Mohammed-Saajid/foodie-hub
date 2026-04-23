def test_hash_password(passwd_context):
    password = "TestPassword123"
    hashed = passwd_context.hash(password)
    assert passwd_context.verify(password, hashed)


def test_hash_password_wrapper_function():
    from app.core.security import hash_password

    hashed = hash_password("WrapperPassword123")
    assert isinstance(hashed, str)
    assert hashed != "WrapperPassword123"


def test_verify_password(passwd_context):
    password = "AnotherTestPassword456"
    hashed = passwd_context.hash(password)
    assert passwd_context.verify(password, hashed)
    assert not passwd_context.verify("WrongPassword", hashed)


def test_verify_password_wrapper_function():
    from app.core.security import hash_password, verify_password

    hashed = hash_password("WrapperVerify123")
    assert verify_password("WrapperVerify123", hashed) is True
    assert verify_password("WrongWrapperVerify123", hashed) is False


def test_create_and_decode_token():
    from app.core.security import create_access_token, decode_token

    subject = "testuser"
    token = create_access_token(subject)
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded.get("sub") == subject


def test_decode_invalid_token():
    from app.core.security import decode_token

    invalid_token = "invalid.token.value"
    decoded = decode_token(invalid_token)
    assert decoded is None


def test_decode_empty_token_returns_none():
    from app.core.security import decode_token

    assert decode_token("") is None


def test_create_token_with_custom_expiry():
    from app.core.security import create_access_token, decode_token

    token = create_access_token("custom-exp-user", expires_minutes=1)
    decoded = decode_token(token)

    assert decoded is not None
    assert decoded.get("sub") == "custom-exp-user"
    assert "exp" in decoded


def test_create_reset_token():
    from app.core.security import create_reset_token

    token1 = create_reset_token()
    token2 = create_reset_token()
    assert token1 != token2  # Ensure tokens are unique
    assert len(token1) > 0  # Ensure token is not empty


def test_hash_token():
    from app.core.security import hash_token

    token = "sometokenvalue"
    hashed = hash_token(token)
    assert hashed != token  # Ensure the token is hashed
    assert len(hashed) == 64  # SHA-256 produces a 64-character hexadecimal string


def test_generate_otp():
    from app.core.security import generate_otp

    otp_length = 6
    otp = generate_otp(otp_length)
    assert len(otp) == otp_length
    assert otp.isdigit()  # Ensure OTP consists of digits only
