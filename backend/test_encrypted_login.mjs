/**
 * Encrypted Login Test Script
 *
 * Tests the full encrypted login flow:
 *   1. Fetches the RSA public key from GET /api/v1/auth/public-key
 *   2. Encrypts username & password individually with RSA-OAEP / SHA-256
 *   3. Sends the encrypted fields to POST /api/v1/auth/login
 *   4. Prints the JWT token on success
 *
 * Usage:
 *   node test_encrypted_login.mjs [username] [password]
 *
 * Environment variables (optional):
 *   BASE_URL  – API base URL (default: http://localhost:8000)
 */

import crypto from "node:crypto";

// ── Configuration ──────────────────────────────────────────────────────
const BASE_URL = process.env.BASE_URL || "http://localhost:8000";
const USERNAME = process.argv[2] || "admin";
const PASSWORD = process.argv[3] || "admin123";

// ── Helpers ────────────────────────────────────────────────────────────

/**
 * Encrypt a plaintext string with the given PEM public key using
 * RSA-OAEP with SHA-256 and return a base64-encoded ciphertext.
 */
function rsaEncrypt(publicKeyPem, plaintext) {
    const encrypted = crypto.publicEncrypt(
        {
            key: publicKeyPem,
            padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
            oaepHash: "sha256",
        },
        Buffer.from(plaintext, "utf-8")
    );
    return encrypted.toString("base64");
}

/** Pretty-print a JSON object to the console. */
function logJson(label, obj) {
    console.log(`\n── ${label} ${"─".repeat(60 - label.length)}`);
    console.log(JSON.stringify(obj, null, 2));
}

// ── Main flow ──────────────────────────────────────────────────────────
async function main() {
    console.log("╔══════════════════════════════════════════════════════════╗");
    console.log("║          Encrypted Login Test Script                    ║");
    console.log("╚══════════════════════════════════════════════════════════╝");
    console.log(`  Base URL : ${BASE_URL}`);
    console.log(`  Username : ${USERNAME}`);
    console.log(`  Password : ${"*".repeat(PASSWORD.length)}`);

    // ── Step 1: Fetch the RSA public key ────────────────────────────────
    console.log("\n⏳ Step 1 — Fetching RSA public key …");

    const publicKeyRes = await fetch(`${BASE_URL}/api/v1/auth/public-key`);

    if (!publicKeyRes.ok) {
        const errBody = await publicKeyRes.text();
        console.error(`❌ Failed to fetch public key (HTTP ${publicKeyRes.status})`);
        console.error(errBody);
        process.exit(1);
    }

    const { public_key: publicKeyPem } = await publicKeyRes.json();
    console.log("✅ Public key received.");
    console.log(publicKeyPem.substring(0, 60) + " …");

    // ── Step 2: Encrypt credentials ─────────────────────────────────────
    console.log("\n⏳ Step 2 — Encrypting credentials with RSA-OAEP/SHA-256 …");

    const encryptedUsername = rsaEncrypt(publicKeyPem, USERNAME);
    const encryptedPassword = rsaEncrypt(publicKeyPem, PASSWORD);

    console.log("✅ Credentials encrypted.");
    console.log(`  Encrypted username (first 40 chars): ${encryptedUsername}…`);
    console.log(`  Encrypted password (first 40 chars): ${encryptedPassword}…`);

    // ── Step 3: Login ───────────────────────────────────────────────────
    console.log("\n⏳ Step 3 — Sending login request …");

    const loginPayload = {
        username: encryptedUsername,
        password: encryptedPassword,
    };

    const loginRes = await fetch(`${BASE_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginPayload),
    });

    const loginBody = await loginRes.json();

    if (!loginRes.ok) {
        console.error(`❌ Login failed (HTTP ${loginRes.status})`);
        logJson("Error Response", loginBody);
        process.exit(1);
    }

    // ── Step 4: Show the token ──────────────────────────────────────────
    console.log("✅ Login successful!");
    logJson("Token Response", loginBody);

    // Decode and display JWT payload (for debugging)
    try {
        const [, payloadB64] = loginBody.access_token.split(".");
        const payload = JSON.parse(
            Buffer.from(payloadB64, "base64url").toString("utf-8")
        );
        logJson("JWT Payload (decoded)", payload);
    } catch {
        console.log("  (could not decode JWT payload)");
    }
}

main().catch((err) => {
    console.error("\n💥 Unexpected error:", err.message || err);
    process.exit(1);
});
