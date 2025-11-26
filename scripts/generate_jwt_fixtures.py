#!/usr/bin/env python3
"""Generate JWT token fixtures for testing."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.auth.jwt_manual import JWTEncoder


def generateHS256Token(outputPath: Path) -> None:
    """Generate valid HS256 JWT token fixture.

    Args:
        outputPath: Path to save token
    """
    payload = {
        "sub": "user123",
        "username": "testuser",
        "role": "admin",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    secretKey = "test_secret_key_for_hs256"
    token = JWTEncoder.encode(payload, secretKey=secretKey, algorithm="HS256")
    outputPath.write_text(token)
    print(f"Generated HS256 token: {outputPath}")


def generateRS256Token(outputPath: Path, privateKeyPath: Path) -> None:
    """Generate valid RS256 JWT token fixture.

    Args:
        outputPath: Path to save token
        privateKeyPath: Path to RSA private key
    """
    payload = {
        "sub": "user456",
        "username": "testuser",
        "role": "user",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    privateKey = privateKeyPath.read_text()
    token = JWTEncoder.encode(payload, key=privateKey, algorithm="RS256")
    outputPath.write_text(token)
    print(f"Generated RS256 token: {outputPath}")


def generateES256Token(outputPath: Path, privateKeyPath: Path) -> None:
    """Generate valid ES256 JWT token fixture.

    Args:
        outputPath: Path to save token
        privateKeyPath: Path to ECDSA private key
    """
    payload = {
        "sub": "user789",
        "username": "testuser",
        "role": "guest",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    privateKey = privateKeyPath.read_text()
    token = JWTEncoder.encode(payload, key=privateKey, algorithm="ES256")
    outputPath.write_text(token)
    print(f"Generated ES256 token: {outputPath}")


def generateInvalidTokens(outputDir: Path) -> None:
    """Generate invalid JWT token fixtures.

    Args:
        outputDir: Directory to save invalid tokens
    """
    malformedToken = "not.a.valid.jwt.token"
    (outputDir / "malformed_token.txt").write_text(malformedToken)

    expiredPayload = {
        "sub": "user123",
        "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
    }
    expiredToken = JWTEncoder.encode(expiredPayload, secretKey="test_secret", algorithm="HS256")
    (outputDir / "expired_token.txt").write_text(expiredToken)

    validToken = JWTEncoder.encode({"sub": "user123"}, secretKey="test_secret", algorithm="HS256")
    parts = validToken.split(".")
    wrongSignatureToken = f"{parts[0]}.{parts[1]}.wrong_signature"
    (outputDir / "wrong_signature_token.txt").write_text(wrongSignatureToken)

    print(f"Generated invalid tokens in {outputDir}")


def main() -> None:
    """Generate all JWT token fixtures."""
    fixturesDir = Path(__file__).parent.parent / "tests" / "fixtures" / "jwt"
    validTokensDir = fixturesDir / "valid_tokens"
    invalidTokensDir = fixturesDir / "invalid_tokens"
    validTokensDir.mkdir(parents=True, exist_ok=True)
    invalidTokensDir.mkdir(parents=True, exist_ok=True)

    generateHS256Token(validTokensDir / "hs256_token.txt")
    generateRS256Token(validTokensDir / "rs256_token.txt", fixturesDir / "rsa_private_key.pem")
    generateES256Token(validTokensDir / "es256_token.txt", fixturesDir / "ecdsa_private_key.pem")
    generateInvalidTokens(invalidTokensDir)

    print("All JWT token fixtures generated successfully")


if __name__ == "__main__":
    main()

