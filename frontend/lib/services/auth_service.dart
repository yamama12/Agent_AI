import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/login_model.dart';

class AuthService {
  final String baseUrl = 'http://localhost:8000'; // Changez l'IP si nécessaire

  Future<bool> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );

      print('Status code: ${response.statusCode}');
      print('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final prefs = await SharedPreferences.getInstance(); 
        await prefs.setString('token', data['access_token']);
        await prefs.setString('role', data['role'] ?? '');
        await prefs.setBool('change_password', data['change_password'] ?? false);
        await prefs.setString('user_email', email);
        
        print('Données sauvegardées avec succès');
        return true;
      }
      return false;
    } catch (e) {
      print('Erreur de connexion: $e');
      return false;
    }
  }

  Future<void> logout() async {
    try {
      final prefs = await SharedPreferences.getInstance(); // CORRECTION ICI
      
      // Liste des clés à supprimer
      final keysToRemove = ['token', 'role', 'change_password', 'user_email'];
      
      // Supprimer chaque clé
      for (String key in keysToRemove) {
        await prefs.remove(key);
      }
      
      print('Déconnexion réussie');
      
    } catch (e) {
      print('Erreur lors de la déconnexion: $e');
    }
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }

  Future<String?> getRole() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('role');
  }
  
  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null;
  }
}
