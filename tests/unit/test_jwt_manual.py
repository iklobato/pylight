"""Unit tests for manual JWT implementation."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.domain.errors import AuthenticationError
from src.infrastructure.auth.jwt_manual import JWTDecoder, JWTEncoder


@pytest.fixture
def secretKey() -> str:
    """Fixture for HS256 secret key."""
    return "test_secret_key_for_hs256"


@pytest.fixture
def rsaPrivateKey() -> str:
    """Fixture for RSA private key."""
    keyPath = Path(__file__).parent.parent / "fixtures" / "jwt" / "rsa_private_key.pem"
    return keyPath.read_text()


@pytest.fixture
def rsaPublicKey() -> str:
    """Fixture for RSA public key."""
    keyPath = Path(__file__).parent.parent / "fixtures" / "jwt" / "rsa_public_key.pem"
    return keyPath.read_text()


@pytest.fixture
def ecdsaPrivateKey() -> str:
    """Fixture for ECDSA private key."""
    keyPath = Path(__file__).parent.parent / "fixtures" / "jwt" / "ecdsa_private_key.pem"
    return keyPath.read_text()


@pytest.fixture
def ecdsaPublicKey() -> str:
    """Fixture for ECDSA public key."""
    keyPath = Path(__file__).parent.parent / "fixtures" / "jwt" / "ecdsa_public_key.pem"
    return keyPath.read_text()


@pytest.fixture
def samplePayload() -> dict:
    """Fixture for sample JWT payload."""
    return {
        "sub": "user123",
        "username": "testuser",
        "role": "admin",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }


class TestJWTEncoder:
    """Test JWT encoding for all algorithms."""

    def test_jwt_encode_hs256_returns_valid_token(self, secretKey: str, samplePayload: dict) -> None:
        """Test HS256 encoding returns valid token."""
        token = JWTEncoder.encode(samplePayload, secretKey=secretKey, algorithm="HS256")

        assert token is not None
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3
        assert parts[0]  # Header
        assert parts[1]  # Payload
        assert parts[2]  # Signature

    def test_jwt_encode_rs256_returns_valid_token(
        self, rsaPrivateKey: str, samplePayload: dict
    ) -> None:
        """Test RS256 encoding returns valid token."""
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS256")

        assert token is not None
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_jwt_encode_rs384_returns_valid_token(
        self, rsaPrivateKey: str, samplePayload: dict
    ) -> None:
        """Test RS384 encoding returns valid token."""
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS384")

        assert token is not None
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_jwt_encode_rs512_returns_valid_token(
        self, rsaPrivateKey: str, samplePayload: dict
    ) -> None:
        """Test RS512 encoding returns valid token."""
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS512")

        assert token is not None
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_jwt_encode_es256_returns_valid_token(
        self, ecdsaPrivateKey: str, samplePayload: dict
    ) -> None:
        """Test ES256 encoding returns valid token."""
        token = JWTEncoder.encode(samplePayload, key=ecdsaPrivateKey, algorithm="ES256")

        assert token is not None
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_jwt_encode_es384_returns_valid_token(
        self, ecdsaPrivateKey: str, samplePayload: dict
    ) -> None:
        """Test ES384 encoding returns valid token."""
        token = JWTEncoder.encode(samplePayload, key=ecdsaPrivateKey, algorithm="ES384")

        assert token is not None
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_jwt_encode_es512_returns_valid_token(
        self, ecdsaPrivateKey: str, samplePayload: dict
    ) -> None:
        """Test ES512 encoding returns valid token."""
        token = JWTEncoder.encode(samplePayload, key=ecdsaPrivateKey, algorithm="ES512")

        assert token is not None
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_jwt_encode_invalid_payload_type_raises_type_error(self, secretKey: str) -> None:
        """Test encoding with invalid payload type raises TypeError."""
        with pytest.raises(TypeError, match="Payload must be a dictionary"):
            JWTEncoder.encode("not a dict", secretKey=secretKey, algorithm="HS256")

    def test_jwt_encode_unsupported_algorithm_raises_value_error(
        self, secretKey: str, samplePayload: dict
    ) -> None:
        """Test encoding with unsupported algorithm raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            JWTEncoder.encode(samplePayload, secretKey=secretKey, algorithm="HS512")


class TestJWTDecoder:
    """Test JWT decoding for all algorithms."""

    def test_jwt_decode_hs256_verifies_signature(
        self, secretKey: str, samplePayload: dict
    ) -> None:
        """Test HS256 decoding verifies signature correctly."""
        token = JWTEncoder.encode(samplePayload, secretKey=secretKey, algorithm="HS256")
        decoded = JWTDecoder.decode(token, secretKey=secretKey)

        assert decoded["sub"] == samplePayload["sub"]
        assert decoded["username"] == samplePayload["username"]
        assert decoded["role"] == samplePayload["role"]

    def test_jwt_decode_rs256_verifies_signature(
        self, rsaPrivateKey: str, rsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test RS256 decoding verifies signature correctly."""
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS256")
        decoded = JWTDecoder.decode(token, key=rsaPublicKey, allowlist=["RS256"])

        assert decoded["sub"] == samplePayload["sub"]
        assert decoded["username"] == samplePayload["username"]

    def test_jwt_decode_es256_verifies_signature(
        self, ecdsaPrivateKey: str, ecdsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test ES256 decoding verifies signature correctly."""
        token = JWTEncoder.encode(samplePayload, key=ecdsaPrivateKey, algorithm="ES256")
        decoded = JWTDecoder.decode(token, key=ecdsaPublicKey, allowlist=["ES256"])

        assert decoded["sub"] == samplePayload["sub"]
        assert decoded["username"] == samplePayload["username"]

    def test_jwt_decode_malformed_token_raises_authentication_error(
        self, secretKey: str
    ) -> None:
        """Test decoding malformed token raises AuthenticationError."""
        malformedToken = "not.a.valid.jwt.token"
        with pytest.raises(AuthenticationError, match="Invalid JWT token structure"):
            JWTDecoder.decode(malformedToken, secretKey=secretKey)

    def test_jwt_decode_expired_token_raises_authentication_error(
        self, secretKey: str
    ) -> None:
        """Test decoding expired token raises AuthenticationError."""
        expiredPayload = {
            "sub": "user123",
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
        }
        expiredToken = JWTEncoder.encode(expiredPayload, secretKey=secretKey, algorithm="HS256")
        with pytest.raises(AuthenticationError, match="JWT token has expired"):
            JWTDecoder.decode(expiredToken, secretKey=secretKey)

    def test_jwt_decode_wrong_signature_raises_authentication_error(
        self, secretKey: str, samplePayload: dict
    ) -> None:
        """Test decoding token with wrong signature raises AuthenticationError."""
        token = JWTEncoder.encode(samplePayload, secretKey=secretKey, algorithm="HS256")
        parts = token.split(".")
        wrongSignatureToken = f"{parts[0]}.{parts[1]}.wrong_signature"
        with pytest.raises(AuthenticationError, match="Invalid JWT token signature"):
            JWTDecoder.decode(wrongSignatureToken, secretKey=secretKey)

    def test_jwt_decode_algorithm_not_in_allowlist_raises_authentication_error(
        self, rsaPrivateKey: str, rsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test decoding token with algorithm not in allowlist raises AuthenticationError."""
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS256")
        with pytest.raises(AuthenticationError, match="not in the allowed list"):
            JWTDecoder.decode(token, key=rsaPublicKey, allowlist=["HS256"])

    def test_jwt_decode_key_type_mismatch_raises_authentication_error(
        self, rsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test decoding token with key type mismatch raises AuthenticationError."""
        token = JWTEncoder.encode(samplePayload, secretKey="test_secret", algorithm="HS256")
        with pytest.raises(AuthenticationError, match="Invalid JWT token signature"):
            JWTDecoder.decode(token, key=rsaPublicKey, allowlist=["HS256"])

    def test_jwt_encode_decode_backward_compatibility_secretkey_parameter(
        self, secretKey: str, samplePayload: dict
    ) -> None:
        """Test backward compatibility with secretKey parameter."""
        token = JWTEncoder.encode(samplePayload, secretKey=secretKey, algorithm="HS256")
        decoded = JWTDecoder.decode(token, secretKey=secretKey)

        assert decoded["sub"] == samplePayload["sub"]
        assert decoded["username"] == samplePayload["username"]

    def test_jwt_decode_allowlist_default_hs256_only(
        self, secretKey: str, samplePayload: dict
    ) -> None:
        """Test default allowlist only accepts HS256."""
        token = JWTEncoder.encode(samplePayload, secretKey=secretKey, algorithm="HS256")
        decoded = JWTDecoder.decode(token, secretKey=secretKey)

        assert decoded["sub"] == samplePayload["sub"]

    def test_jwt_decode_allowlist_custom_multiple_algorithms(
        self, rsaPrivateKey: str, rsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test custom allowlist accepts multiple algorithms."""
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS256")
        decoded = JWTDecoder.decode(token, key=rsaPublicKey, allowlist=["HS256", "RS256", "ES256"])

        assert decoded["sub"] == samplePayload["sub"]

    def test_jwt_decode_allowlist_per_call_override(
        self, rsaPrivateKey: str, rsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test allowlist can be overridden per decode call."""
        decoder = JWTDecoder(allowlist=["HS256"])
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS256")
        decoded = decoder.decode(token, key=rsaPublicKey, allowlist=["RS256"])

        assert decoded["sub"] == samplePayload["sub"]

    def test_jwt_decode_automatic_key_type_detection_rsa(
        self, rsaPrivateKey: str, rsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test automatic key type detection for RSA."""
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS256")
        decoded = JWTDecoder.decode(token, key=rsaPublicKey, allowlist=["RS256"])

        assert decoded["sub"] == samplePayload["sub"]

    def test_jwt_decode_automatic_key_type_detection_ecdsa(
        self, ecdsaPrivateKey: str, ecdsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test automatic key type detection for ECDSA."""
        token = JWTEncoder.encode(samplePayload, key=ecdsaPrivateKey, algorithm="ES256")
        decoded = JWTDecoder.decode(token, key=ecdsaPublicKey, allowlist=["ES256"])

        assert decoded["sub"] == samplePayload["sub"]

    def test_jwt_decode_invalid_base64_encoding_raises_authentication_error(
        self, secretKey: str
    ) -> None:
        """Test decoding token with invalid base64 encoding raises AuthenticationError."""
        invalidToken = "invalid.base64.encoding!"
        with pytest.raises(AuthenticationError, match="Invalid JWT token encoding"):
            JWTDecoder.decode(invalidToken, secretKey=secretKey)

    def test_jwt_decode_wrong_structure_not_3_parts_raises_authentication_error(
        self, secretKey: str
    ) -> None:
        """Test decoding token with wrong structure raises AuthenticationError."""
        wrongStructureToken = "header.payload"
        with pytest.raises(AuthenticationError, match="Invalid JWT token structure"):
            JWTDecoder.decode(wrongStructureToken, secretKey=secretKey)

    def test_jwt_decode_missing_algorithm_in_header_raises_authentication_error(
        self, secretKey: str
    ) -> None:
        """Test decoding token with missing algorithm in header raises AuthenticationError."""
        payload = {"sub": "user123"}
        header = {"typ": "JWT"}
        import base64
        import hashlib
        import hmac
        import json

        headerEncoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payloadEncoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        message = f"{headerEncoded}.{payloadEncoded}"
        signature = hmac.new(
            secretKey.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).digest()
        signatureEncoded = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
        tokenWithoutAlg = f"{headerEncoded}.{payloadEncoded}.{signatureEncoded}"

        with pytest.raises(AuthenticationError, match="not in the allowed list"):
            JWTDecoder.decode(tokenWithoutAlg, secretKey=secretKey)

    def test_jwt_decode_invalid_expiration_format_raises_authentication_error(
        self, secretKey: str
    ) -> None:
        """Test decoding token with invalid expiration format raises AuthenticationError."""
        import base64
        import json

        payload = {"sub": "user123", "exp": "not_a_number"}
        header = {"alg": "HS256", "typ": "JWT"}
        headerEncoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payloadEncoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        message = f"{headerEncoded}.{payloadEncoded}"
        import hashlib
        import hmac

        signature = hmac.new(
            secretKey.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).digest()
        signatureEncoded = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
        token = f"{headerEncoded}.{payloadEncoded}.{signatureEncoded}"
        with pytest.raises(AuthenticationError, match="Invalid exp claim"):
            JWTDecoder.decode(token, secretKey=secretKey)

    def test_jwt_decode_rs384_verifies_signature(
        self, rsaPrivateKey: str, rsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test RS384 decoding verifies signature correctly."""
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS384")
        decoded = JWTDecoder.decode(token, key=rsaPublicKey, allowlist=["RS384"])

        assert decoded["sub"] == samplePayload["sub"]

    def test_jwt_decode_rs512_verifies_signature(
        self, rsaPrivateKey: str, rsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test RS512 decoding verifies signature correctly."""
        token = JWTEncoder.encode(samplePayload, key=rsaPrivateKey, algorithm="RS512")
        decoded = JWTDecoder.decode(token, key=rsaPublicKey, allowlist=["RS512"])

        assert decoded["sub"] == samplePayload["sub"]

    def test_jwt_decode_es384_verifies_signature(
        self, ecdsaPrivateKey: str, ecdsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test ES384 decoding verifies signature correctly."""
        token = JWTEncoder.encode(samplePayload, key=ecdsaPrivateKey, algorithm="ES384")
        decoded = JWTDecoder.decode(token, key=ecdsaPublicKey, allowlist=["ES384"])

        assert decoded["sub"] == samplePayload["sub"]

    def test_jwt_decode_es512_verifies_signature(
        self, ecdsaPrivateKey: str, ecdsaPublicKey: str, samplePayload: dict
    ) -> None:
        """Test ES512 decoding verifies signature correctly."""
        token = JWTEncoder.encode(samplePayload, key=ecdsaPrivateKey, algorithm="ES512")
        decoded = JWTDecoder.decode(token, key=ecdsaPublicKey, allowlist=["ES512"])

        assert decoded["sub"] == samplePayload["sub"]

