//Logique métier du service chatbot
/* Faire le lien entre UI et API
Contenir la logique du chatbot */

// lib/services/chat_api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ChatApiService {
  static const String baseUrl = "http://127.0.0.1:8000";

  static Future<Map<String, String>> _buildAuthHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final role = prefs.getString('role');
    String rolesHeader = '[]';
    if (role != null && role.isNotEmpty) {
      final trimmed = role.trim();
      rolesHeader = trimmed.startsWith('[') ? trimmed : jsonEncode([trimmed]);
    }

    return {
      "Content-Type": "application/json",
      "x-user-roles": rolesHeader,
    };
  }

  static Future<Map<String, dynamic>> sendMessage(String message) async {
    final headers = await _buildAuthHeaders();
    final response = await http.post(
      Uri.parse("$baseUrl/chat/"),
      headers: headers,
      body: jsonEncode({"message": message}),
    );

    if (response.statusCode != 200) {
      throw Exception("Erreur serveur");
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  // NOUVELLE MÉTHODE: sendMessageRaw qui retourne la réponse brute
  static Future<http.Response> sendMessageRaw(String message) async {
    final headers = await _buildAuthHeaders();
    final response = await http.post(
      Uri.parse("$baseUrl/chat/"),
      headers: headers,
      body: jsonEncode({"message": message}),
    );

    if (response.statusCode != 200) {
      throw Exception("Erreur serveur: ${response.statusCode}");
    }

    return response;
  }

  static Future<String> createConversation() async {
    final res = await http.post(Uri.parse("$baseUrl/conversations"));
    return jsonDecode(res.body)['id'];
  }

  static Future<List> fetchConversations() async {
    final res = await http.get(Uri.parse("$baseUrl/conversations"));
    return jsonDecode(res.body);
  }

  static Future<List> fetchMessages(String convId) async {
    final res = await http.get(
      Uri.parse("$baseUrl/conversations/$convId/messages"),
    );
    return jsonDecode(res.body);
  }

  static Future<Map<String, dynamic>> sendConversationMessage(
      String convId, String text) async {
    final res = await http.post(
      Uri.parse("$baseUrl/conversations/$convId/messages"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"text": text}),
    );
    return jsonDecode(res.body);
  }

  static Future<void> deleteFiles(List<String> files) async {
    if (files.isEmpty) return;
    final response = await http.post(
      Uri.parse("$baseUrl/chat/delete-files"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"files": files}),
    );

    if (response.statusCode != 200) {
      throw Exception("Erreur suppression fichiers: ${response.statusCode}");
    }
  }
}
