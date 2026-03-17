/// RSA-OAEP Encryption Helper for Flutter/Dart
///
/// Dependencies (add to pubspec.yaml):
///   encrypt: ^5.0.3
///   pointycastle: ^3.9.1
///   http: ^1.2.0
///
/// This helper fetches the RSA public key from the backend and encrypts
/// each credential field individually using RSA-OAEP with SHA-256 padding.

import 'dart:convert';
import 'package:encrypt/encrypt.dart';
import 'package:pointycastle/asymmetric/api.dart';
import 'package:http/http.dart' as http;

class EncryptionHelper {
  /// Base URL of the backend API (configure per environment)
  final String baseUrl;

  /// Cached RSA public key
  RSAPublicKey? _publicKey;

  /// Cached Encrypter instance
  Encrypter? _encrypter;

  EncryptionHelper({required this.baseUrl});

  /// Fetch the RSA public key from the backend.
  Future<void> _ensureKeyLoaded() async {
    if (_encrypter != null) return;

    final response = await http.get(
      Uri.parse('$baseUrl/api/v1/auth/public-key'),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to fetch public key: ${response.statusCode}');
    }

    final body = jsonDecode(response.body);
    final pemString = body['public_key'] as String;

    // Parse the PEM public key
    final parser = RSAKeyParser();
    _publicKey = parser.parse(pemString) as RSAPublicKey;
    _encrypter = Encrypter(RSA(
      publicKey: _publicKey,
      encoding: RSAEncoding.OAEP,
      digest: RSADigest.SHA256,
    ));
  }

  /// Encrypt a single string field using RSA-OAEP/SHA-256.
  /// Returns a base64-encoded ciphertext string.
  Future<String> encryptField(String plaintext) async {
    await _ensureKeyLoaded();
    final encrypted = _encrypter!.encrypt(plaintext);
    return encrypted.base64;
  }

  /// Encrypt login credentials and return the request body.
  ///
  /// Returns a Map with `username` and `password` fields, each individually
  /// RSA-OAEP encrypted (base64). The JSON shape is identical to a plain
  /// login request — only the values are encrypted.
  Future<Map<String, String>> encryptLoginBody({
    required String username,
    required String password,
  }) async {
    return {
      'username': await encryptField(username),
      'password': await encryptField(password),
    };
  }

  /// Encrypt a new password for the password-reset endpoint.
  ///
  /// Returns the RSA-OAEP encrypted (base64) new_password string.
  Future<String> encryptNewPassword(String newPassword) async {
    return await encryptField(newPassword);
  }
}

// ---------------------------------------------------------------------------
// Usage Example
// ---------------------------------------------------------------------------
//
// final encryptionHelper = EncryptionHelper(
//   baseUrl: 'https://your-api-domain.com',
// );
//
// // --- Login ---
// final loginBody = await encryptionHelper.encryptLoginBody(
//   username: 'john_doe',
//   password: 'my_secure_password',
// );
//
// final loginResponse = await http.post(
//   Uri.parse('https://your-api-domain.com/api/v1/auth/login'),
//   headers: {'Content-Type': 'application/json'},
//   body: jsonEncode(loginBody),
//   // Sends: {"username": "<encrypted>", "password": "<encrypted>"}
// );
//
// // --- Password Reset ---
// final encryptedPassword = await encryptionHelper.encryptNewPassword(
//   'new_secure_password',
// );
//
// final resetResponse = await http.post(
//   Uri.parse('https://your-api-domain.com/api/v1/auth/password-reset/verify-otp'),
//   headers: {'Content-Type': 'application/json'},
//   body: jsonEncode({
//     'user_id': 123,
//     'otp': '456789',
//     'new_password': encryptedPassword,
//   }),
// );
