"""Manual JWT implementation using Python standard library and cryptography library."""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature
from cryptography.exceptions import InvalidSignature

from src.domain.errors import AuthenticationError


class JWTEncoder:
    """JWT token encoder supporting HS256, RS256, RS384, RS512, ES256, ES384, ES512 algorithms."""

    @staticmethod
    def encode(
        payload: dict[str, Any],
        key: str | bytes | object | None = None,
        secretKey: str | None = None,
        algorithm: str = "HS256",
    ) -> str:
        """Encode JWT token with specified algorithm.

        Args:
            payload: JWT claims (username, role, sub, exp, etc.)
            key: Key for signing (new API)
                - For HS256: Secret key (str)
                - For RS256/RS384/RS512: RSA private key (PEM str, bytes, or cryptography object)
                - For ES256/ES384/ES512: ECDSA private key (PEM str, bytes, or cryptography object)
            secretKey: Secret key for HS256 (backward compatibility, deprecated - use key)
            algorithm: Algorithm name (default: "HS256", supported: HS256, RS256, RS384, RS512, ES256, ES384, ES512)

        Returns:
            Base64url-encoded JWT token string

        Raises:
            ValueError: If algorithm is not supported
            TypeError: If payload is not a dictionary
            AuthenticationError: If key type doesn't match algorithm requirements
        """
        if not isinstance(payload, dict):
            raise TypeError("Payload must be a dictionary")

        if key is None and secretKey is not None:
            key = secretKey
        elif key is None:
            raise AuthenticationError("Either key or secretKey parameter must be provided")

        header = {"alg": algorithm, "typ": "JWT"}

        headerEncoded = JWTEncoder._base64urlEncode(json.dumps(header, separators=(",", ":")))
        payloadEncoded = JWTEncoder._base64urlEncode(json.dumps(payload, separators=(",", ":")))

        message = f"{headerEncoded}.{payloadEncoded}"

        if algorithm == "HS256":
            if not isinstance(key, str):
                raise AuthenticationError("HS256 requires secret key (str)")
            signature = JWTEncoder._signHS256(message, key)
        elif algorithm in ["RS256", "RS384", "RS512"]:
            privateKey = JWTEncoder._loadRSAPrivateKey(key)
            signature = JWTEncoder._signRSA(message, privateKey, algorithm)
        elif algorithm in ["ES256", "ES384", "ES512"]:
            privateKey = JWTEncoder._loadECDSAPrivateKey(key)
            signature = JWTEncoder._signECDSA(message, privateKey, algorithm)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        return f"{message}.{signature}"

    @staticmethod
    def _base64urlEncode(data: str) -> str:
        """Encode string to base64url format (RFC 4648).

        Args:
            data: String to encode

        Returns:
            Base64url-encoded string without padding
        """
        encoded = base64.urlsafe_b64encode(data.encode("utf-8"))
        return encoded.decode("utf-8").rstrip("=")

    @staticmethod
    def _signHS256(message: str, secretKey: str) -> str:
        """Sign message using HMAC-SHA256.

        Args:
            message: Message to sign
            secretKey: Secret key for signing

        Returns:
            Base64url-encoded signature
        """
        signature = hmac.new(
            secretKey.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).digest()
        encoded = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
        return encoded

    @staticmethod
    def _loadRSAPrivateKey(key: str | bytes | object) -> rsa.RSAPrivateKey:
        """Load RSA private key from various formats.

        Args:
            key: RSA private key (PEM str, bytes, or cryptography object)

        Returns:
            RSA private key object

        Raises:
            AuthenticationError: If key cannot be loaded or is invalid
        """
        if isinstance(key, rsa.RSAPrivateKey):
            return key

        if isinstance(key, bytes):
            keyStr = key.decode("utf-8")
        elif isinstance(key, str):
            keyStr = key
        else:
            raise AuthenticationError("RSA private key must be PEM string, bytes, or cryptography object")

        try:
            return serialization.load_pem_private_key(keyStr.encode("utf-8"), password=None)
        except Exception as e:
            raise AuthenticationError(f"Invalid RSA private key: {e}") from e

    @staticmethod
    def _loadECDSAPrivateKey(key: str | bytes | object) -> ec.EllipticCurvePrivateKey:
        """Load ECDSA private key from various formats.

        Args:
            key: ECDSA private key (PEM str, bytes, or cryptography object)

        Returns:
            ECDSA private key object

        Raises:
            AuthenticationError: If key cannot be loaded or is invalid
        """
        if isinstance(key, ec.EllipticCurvePrivateKey):
            return key

        if isinstance(key, bytes):
            keyStr = key.decode("utf-8")
        elif isinstance(key, str):
            keyStr = key
        else:
            raise AuthenticationError("ECDSA private key must be PEM string, bytes, or cryptography object")

        try:
            loadedKey = serialization.load_pem_private_key(keyStr.encode("utf-8"), password=None)
            if not isinstance(loadedKey, ec.EllipticCurvePrivateKey):
                raise AuthenticationError("Key is not an ECDSA private key")
            return loadedKey
        except Exception as e:
            raise AuthenticationError(f"Invalid ECDSA private key: {e}") from e

    @staticmethod
    def _signRSA(message: str, privateKey: rsa.RSAPrivateKey, algorithm: str) -> str:
        """Sign message using RSA with specified hash algorithm.

        Args:
            message: Message to sign
            privateKey: RSA private key
            algorithm: Algorithm name (RS256, RS384, RS512)

        Returns:
            Base64url-encoded signature
        """
        hashAlgorithm = {
            "RS256": hashes.SHA256(),
            "RS384": hashes.SHA384(),
            "RS512": hashes.SHA512(),
        }.get(algorithm)

        if not hashAlgorithm:
            raise ValueError(f"Unsupported RSA algorithm: {algorithm}")

        signature = privateKey.sign(message.encode("utf-8"), padding.PKCS1v15(), hashAlgorithm)
        encoded = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
        return encoded

    @staticmethod
    def _signECDSA(message: str, privateKey: ec.EllipticCurvePrivateKey, algorithm: str) -> str:
        """Sign message using ECDSA with specified hash algorithm.

        Args:
            message: Message to sign
            privateKey: ECDSA private key
            algorithm: Algorithm name (ES256, ES384, ES512)

        Returns:
            Base64url-encoded signature
        """
        hashAlgorithm = {
            "ES256": hashes.SHA256(),
            "ES384": hashes.SHA384(),
            "ES512": hashes.SHA512(),
        }.get(algorithm)

        if not hashAlgorithm:
            raise ValueError(f"Unsupported ECDSA algorithm: {algorithm}")

        signature = privateKey.sign(message.encode("utf-8"), ec.ECDSA(hashAlgorithm))
        r, s = decode_dss_signature(signature)

        keySize = privateKey.curve.key_size
        signatureBytes = r.to_bytes(keySize // 8, "big") + s.to_bytes(keySize // 8, "big")
        encoded = base64.urlsafe_b64encode(signatureBytes).decode("utf-8").rstrip("=")
        return encoded


class JWTDecoder:
    """JWT token decoder with signature verification and expiration checking."""

    def __init__(self, allowlist: list[str] | None = None):
        """Initialize JWT decoder with algorithm allowlist.

        Args:
            allowlist: List of allowed algorithms (default: ["HS256"])
        """
        self.allowlist = allowlist if allowlist is not None else ["HS256"]

    @staticmethod
    def decode(
        token: str,
        key: str | bytes | object | None = None,
        secretKey: str | None = None,
        algorithms: list[str] | None = None,
        allowlist: list[str] | None = None,
    ) -> dict[str, Any]:
        """Decode and verify JWT token.

        Args:
            token: Base64url-encoded JWT token string
            key: Key for verification (new API)
                - For HS256: Secret key (str)
                - For RS256/RS384/RS512: RSA public key (PEM str, bytes, or cryptography object)
                - For ES256/ES384/ES512: ECDSA public key (PEM str, bytes, or cryptography object)
            secretKey: Secret key for HS256 (backward compatibility - can be passed as keyword argument)
            algorithms: List of allowed algorithms (backward compatibility, deprecated - use allowlist)
            allowlist: Algorithm allowlist (default: ["HS256"])

        Returns:
            Decoded JWT payload (claims)

        Raises:
            AuthenticationError: If algorithm is not in allowlist (before signature verification)
            AuthenticationError: If signature verification fails
            AuthenticationError: If token is expired (exp claim in past)
            AuthenticationError: If token is malformed (invalid base64, wrong structure)
            AuthenticationError: If key type doesn't match algorithm requirements
        """
        if key is None:
            if secretKey is not None:
                key = secretKey
            else:
                raise AuthenticationError("Either key or secretKey parameter must be provided")

        if allowlist is None:
            allowlist = algorithms if algorithms is not None else ["HS256"]

        parts = token.split(".")
        if len(parts) != 3:
            raise AuthenticationError("Invalid JWT token structure: must have 3 parts separated by dots")

        try:
            headerJson = JWTDecoder._base64urlDecode(parts[0])
            payloadJson = JWTDecoder._base64urlDecode(parts[1])
        except Exception as e:
            raise AuthenticationError(f"Invalid JWT token encoding: {e}") from e

        try:
            header = json.loads(headerJson)
            payload = json.loads(payloadJson)
        except json.JSONDecodeError as e:
            raise AuthenticationError(f"Invalid JWT token JSON: {e}") from e

        algorithm = header.get("alg")
        if algorithm not in allowlist:
            raise AuthenticationError(
                f"Algorithm '{algorithm}' is not in the allowed list: {allowlist}"
            )

        message = f"{parts[0]}.{parts[1]}"
        signature = parts[2]

        if algorithm == "HS256":
            if not isinstance(key, str):
                raise AuthenticationError("HS256 requires secret key (str)")
            JWTDecoder._verifyHS256(message, signature, key)
        elif algorithm in ["RS256", "RS384", "RS512"]:
            publicKey = JWTDecoder._loadRSAPublicKey(key)
            JWTDecoder._verifyRSA(message, signature, publicKey, algorithm)
        elif algorithm in ["ES256", "ES384", "ES512"]:
            publicKey = JWTDecoder._loadECDSAPublicKey(key)
            JWTDecoder._verifyECDSA(message, signature, publicKey, algorithm)
        else:
            raise AuthenticationError(f"Unsupported algorithm: {algorithm}")

        exp = payload.get("exp")
        if exp is not None:
            if isinstance(exp, (int, float)):
                expTimestamp = exp
            else:
                raise AuthenticationError("Invalid exp claim: must be numeric timestamp")

            currentTimestamp = datetime.now(timezone.utc).timestamp()
            if expTimestamp < currentTimestamp:
                raise AuthenticationError("JWT token has expired")

        return payload

    @staticmethod
    def _base64urlDecode(data: str) -> str:
        """Decode base64url string to original data.

        Args:
            data: Base64url-encoded string

        Returns:
            Decoded string

        Raises:
            Exception: If decoding fails
        """
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += "=" * padding

        decoded = base64.urlsafe_b64decode(data.encode("utf-8"))
        return decoded.decode("utf-8")

    @staticmethod
    def _verifyHS256(message: str, signature: str, secretKey: str) -> None:
        """Verify HMAC-SHA256 signature.

        Args:
            message: Message that was signed
            signature: Base64url-encoded signature
            secretKey: Secret key for verification

        Raises:
            AuthenticationError: If signature verification fails
        """
        expectedSignature = JWTEncoder._signHS256(message, secretKey)
        if signature != expectedSignature:
            raise AuthenticationError("Invalid JWT token signature")

    @staticmethod
    def _loadRSAPublicKey(key: str | bytes | object) -> rsa.RSAPublicKey:
        """Load RSA public key from various formats.

        Args:
            key: RSA public key (PEM str, bytes, or cryptography object)

        Returns:
            RSA public key object

        Raises:
            AuthenticationError: If key cannot be loaded or is invalid
        """
        if isinstance(key, rsa.RSAPublicKey):
            return key

        if isinstance(key, bytes):
            keyStr = key.decode("utf-8")
        elif isinstance(key, str):
            keyStr = key
        else:
            raise AuthenticationError("RSA public key must be PEM string, bytes, or cryptography object")

        try:
            return serialization.load_pem_public_key(keyStr.encode("utf-8"))
        except Exception as e:
            raise AuthenticationError(f"Invalid RSA public key: {e}") from e

    @staticmethod
    def _loadECDSAPublicKey(key: str | bytes | object) -> ec.EllipticCurvePublicKey:
        """Load ECDSA public key from various formats.

        Args:
            key: ECDSA public key (PEM str, bytes, or cryptography object)

        Returns:
            ECDSA public key object

        Raises:
            AuthenticationError: If key cannot be loaded or is invalid
        """
        if isinstance(key, ec.EllipticCurvePublicKey):
            return key

        if isinstance(key, bytes):
            keyStr = key.decode("utf-8")
        elif isinstance(key, str):
            keyStr = key
        else:
            raise AuthenticationError("ECDSA public key must be PEM string, bytes, or cryptography object")

        try:
            loadedKey = serialization.load_pem_public_key(keyStr.encode("utf-8"))
            if not isinstance(loadedKey, ec.EllipticCurvePublicKey):
                raise AuthenticationError("Key is not an ECDSA public key")
            return loadedKey
        except Exception as e:
            raise AuthenticationError(f"Invalid ECDSA public key: {e}") from e

    @staticmethod
    def _verifyRSA(message: str, signature: str, publicKey: rsa.RSAPublicKey, algorithm: str) -> None:
        """Verify RSA signature.

        Args:
            message: Message that was signed
            signature: Base64url-encoded signature
            publicKey: RSA public key
            algorithm: Algorithm name (RS256, RS384, RS512)

        Raises:
            AuthenticationError: If signature verification fails
        """
        hashAlgorithm = {
            "RS256": hashes.SHA256(),
            "RS384": hashes.SHA384(),
            "RS512": hashes.SHA512(),
        }.get(algorithm)

        if not hashAlgorithm:
            raise ValueError(f"Unsupported RSA algorithm: {algorithm}")

        paddingLength = 4 - (len(signature) % 4)
        if paddingLength != 4:
            signature += "=" * paddingLength

        try:
            signatureBytes = base64.urlsafe_b64decode(signature.encode("utf-8"))
            publicKey.verify(signatureBytes, message.encode("utf-8"), padding.PKCS1v15(), hashAlgorithm)
        except InvalidSignature:
            raise AuthenticationError("Invalid JWT token signature")
        except Exception as e:
            raise AuthenticationError(f"RSA signature verification failed: {e}") from e

    @staticmethod
    def _verifyECDSA(message: str, signature: str, publicKey: ec.EllipticCurvePublicKey, algorithm: str) -> None:
        """Verify ECDSA signature.

        Args:
            message: Message that was signed
            signature: Base64url-encoded signature
            publicKey: ECDSA public key
            algorithm: Algorithm name (ES256, ES384, ES512)

        Raises:
            AuthenticationError: If signature verification fails
        """
        hashAlgorithm = {
            "ES256": hashes.SHA256(),
            "ES384": hashes.SHA384(),
            "ES512": hashes.SHA512(),
        }.get(algorithm)

        if not hashAlgorithm:
            raise ValueError(f"Unsupported ECDSA algorithm: {algorithm}")

        padding = 4 - (len(signature) % 4)
        if padding != 4:
            signature += "=" * padding

        try:
            signatureBytes = base64.urlsafe_b64decode(signature.encode("utf-8"))
            keySize = publicKey.curve.key_size
            r = int.from_bytes(signatureBytes[: keySize // 8], "big")
            s = int.from_bytes(signatureBytes[keySize // 8 :], "big")
            dssSignature = encode_dss_signature(r, s)
            publicKey.verify(dssSignature, message.encode("utf-8"), ec.ECDSA(hashAlgorithm))
        except InvalidSignature:
            raise AuthenticationError("Invalid JWT token signature")
        except Exception as e:
            raise AuthenticationError(f"ECDSA signature verification failed: {e}") from e
