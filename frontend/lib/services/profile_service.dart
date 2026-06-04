// lib/services/profile_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/profile.dart';
import 'auth_service.dart';

class ProfileService {
  static const String baseUrl = 'http://localhost:8000';
  final AuthService _authService = AuthService();

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  String _extractErrorMessage(http.Response response) {
    if (response.body.isEmpty) return 'Erreur ${response.statusCode}';
    try {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic> && decoded['detail'] != null) {
        final detail = decoded['detail'];
        if (detail is String) return detail;
        if (detail is List) {
          return detail.map((e) => e is Map ? e['msg'] ?? e.toString() : e.toString()).join(', ');
        }
        return detail.toString();
      }
      return decoded.toString();
    } catch (_) {
      return response.body;
    }
  }

  // Récupérer le profil de l'utilisateur connecté
  Future<ProfileData> getProfile() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/users/me'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return ProfileData.fromJson(jsonDecode(response.body));
      } else {
        throw Exception(_extractErrorMessage(response));
      }
    } catch (e) {
      print('Erreur getProfile: $e');
      rethrow;
    }
  }

  // Changer le mot de passe uniquement
  Future<void> changePassword(String currentPassword, String newPassword) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/users/me/change-password'),
        headers: headers,
        body: jsonEncode({
          'current_password': currentPassword,
          'new_password': newPassword,
        }),
      );

      if (response.statusCode != 200) {
        throw Exception(_extractErrorMessage(response));
      }
    } catch (e) {
      print('Erreur changePassword: $e');
      rethrow;
    }
  }
}