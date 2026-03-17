/**
 * RSA-OAEP Encryption Helper for JavaScript/TypeScript
 *
 * Dependencies:
 *   npm install node-forge
 *   npm install --save-dev @types/node-forge  (for TypeScript)
 *
 * This helper fetches the RSA public key from the backend and encrypts
 * each credential field individually using RSA-OAEP with SHA-256 padding.
 * The JSON request shape stays the same — only the values are encrypted.
 */

import * as forge from "node-forge";

interface EncryptionHelperConfig {
    /** Base URL of the backend API (e.g., "https://api.example.com") */
    baseUrl: string;
}

class EncryptionHelper {
    private baseUrl: string;
    private publicKey: forge.pki.rsa.PublicKey | null = null;

    constructor(config: EncryptionHelperConfig) {
        this.baseUrl = config.baseUrl;
    }

    /** Fetch the RSA public key from the backend. */
    private async ensureKeyLoaded(): Promise<forge.pki.rsa.PublicKey> {
        if (this.publicKey) return this.publicKey;

        const response = await fetch(`${this.baseUrl}/api/v1/auth/public-key`);
        if (!response.ok) {
            throw new Error(`Failed to fetch public key: ${response.status}`);
        }

        const data = await response.json();
        this.publicKey = forge.pki.publicKeyFromPem(data.public_key);
        return this.publicKey;
    }

    /**
     * Encrypt a single string field using RSA-OAEP/SHA-256.
     * @returns Base64-encoded ciphertext.
     */
    async encryptField(plaintext: string): Promise<string> {
        const publicKey = await this.ensureKeyLoaded();

        const encrypted = publicKey.encrypt(plaintext, "RSA-OAEP", {
            md: forge.md.sha256.create(),
            mgf1: { md: forge.md.sha256.create() },
        });

        return forge.util.encode64(encrypted);
    }

    /**
     * Encrypt login credentials. Returns an object with the same shape
     * as a plain login request, but with encrypted values.
     *
     * @returns `{ username: "<encrypted>", password: "<encrypted>" }`
     */
    async encryptLoginBody(
        username: string,
        password: string
    ): Promise<{ username: string; password: string }> {
        return {
            username: await this.encryptField(username),
            password: await this.encryptField(password),
        };
    }

    /**
     * Encrypt a new password for the password-reset endpoint.
     * @returns Base64-encoded RSA-OAEP encrypted string.
     */
    async encryptNewPassword(newPassword: string): Promise<string> {
        return this.encryptField(newPassword);
    }
}

export { EncryptionHelper, EncryptionHelperConfig };

// ---------------------------------------------------------------------------
// Usage Examples
// ---------------------------------------------------------------------------
//
// const helper = new EncryptionHelper({
//   baseUrl: "https://your-api-domain.com",
// });
//
// // --- Login ---
// async function login(username: string, password: string) {
//   const body = await helper.encryptLoginBody(username, password);
//   // body = { username: "<encrypted>", password: "<encrypted>" }
//
//   const response = await fetch(
//     "https://your-api-domain.com/api/v1/auth/login",
//     {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify(body),
//     }
//   );
//
//   return response.json();
// }
//
// // --- Password Reset ---
// async function resetPassword(
//   userId: number,
//   otp: string,
//   newPassword: string
// ) {
//   const encryptedPassword = await helper.encryptNewPassword(newPassword);
//
//   const response = await fetch(
//     "https://your-api-domain.com/api/v1/auth/password-reset/verify-otp",
//     {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({
//         user_id: userId,
//         otp: otp,
//         new_password: encryptedPassword,
//       }),
//     }
//   );
//
//   return response.json();
// }
