#!/usr/bin/env python3
"""Generate RSA and ECDSA test keys for JWT testing."""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa


def generateRSAKeys(outputDir: Path) -> None:
    """Generate RSA private and public keys for testing.

    Args:
        outputDir: Directory to save keys
    """
    privateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    publicKey = privateKey.public_key()

    privatePem = privateKey.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    publicPem = publicKey.public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    privateKeyPath = outputDir / "rsa_private_key.pem"
    publicKeyPath = outputDir / "rsa_public_key.pem"

    privateKeyPath.write_bytes(privatePem)
    publicKeyPath.write_bytes(publicPem)

    print(f"Generated RSA keys: {privateKeyPath}, {publicKeyPath}")


def generateECDSAKeys(outputDir: Path) -> None:
    """Generate ECDSA private and public keys for testing.

    Args:
        outputDir: Directory to save keys
    """
    privateKey = ec.generate_private_key(ec.SECP256R1())
    publicKey = privateKey.public_key()

    privatePem = privateKey.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    publicPem = publicKey.public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    privateKeyPath = outputDir / "ecdsa_private_key.pem"
    publicKeyPath = outputDir / "ecdsa_public_key.pem"

    privateKeyPath.write_bytes(privatePem)
    publicKeyPath.write_bytes(publicPem)

    print(f"Generated ECDSA keys: {privateKeyPath}, {publicKeyPath}")


def main() -> None:
    """Generate all test keys."""
    fixturesDir = Path(__file__).parent.parent / "tests" / "fixtures" / "jwt"
    fixturesDir.mkdir(parents=True, exist_ok=True)

    generateRSAKeys(fixturesDir)
    generateECDSAKeys(fixturesDir)

    print("All test keys generated successfully")


if __name__ == "__main__":
    main()


