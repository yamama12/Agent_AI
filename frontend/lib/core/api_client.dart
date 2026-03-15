//Communication avec le backend
/* Gérer les appels HTTP vers FastAPI
Centraliser les URLs et requêtes
Éviter le code réseau dans l’UI */

import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiClient {
  static const String baseUrl = "http://127.0.0.1:8000";

  static Future<Map<String, dynamic>> postChat(String message) async {
    final response = await http.post(
      Uri.parse("$baseUrl/chat/"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"message": message}),
    );

    if (response.statusCode != 200) {
      throw Exception("Erreur serveur");
    }

    return jsonDecode(response.body);
  }
}


