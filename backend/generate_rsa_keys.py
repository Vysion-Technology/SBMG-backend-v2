"""Generate a 2048-bit RSA key pair and print the PEM strings.

Usage:
    python generate_rsa_keys.py

The output is formatted for direct inclusion in a .env file.
Copy the output and paste it into your .env file.
"""

from Crypto.PublicKey import RSA


def main() -> None:
    key = RSA.generate(2048)

    private_pem = key.export_key().decode()
    public_pem = key.publickey().export_key().decode()

    # Escape newlines for .env file format
    private_env = private_pem.replace("\n", "\\n")
    public_env = public_pem.replace("\n", "\\n")

    print("=" * 60)
    print("RSA Key Pair Generated (2048-bit)")
    print("=" * 60)
    print()
    print("Add the following to your .env file:")
    print()
    print(f'RSA_PRIVATE_KEY_PEM="{private_env}"')
    print()
    print(f'RSA_PUBLIC_KEY_PEM="{public_env}"')
    print()
    print("=" * 60)
    print("IMPORTANT: Keep RSA_PRIVATE_KEY_PEM secret!")
    print("In production, use a secrets manager (AWS Secrets Manager, Vault, etc.)")
    print("=" * 60)


if __name__ == "__main__":
    main()
