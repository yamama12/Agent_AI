// services/user_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/user.dart';
import 'auth_service.dart';

class UserService {
  static const String baseUrl = "http://127.0.0.1:8000"; 
  final AuthService _authService = AuthService();

  // Headers avec token d'authentification
  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  // Récupérer tous les utilisateurs
  Future<List<User>> getAllUsers() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/users'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => User.fromJson(json)).toList();
      } else {
        throw Exception('Erreur ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('Erreur getAllUsers: $e');
      rethrow;
    }
  }

  // Récupérer un utilisateur par ID
  Future<User> getUserById(int id) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/users/$id'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return User.fromJson(jsonDecode(response.body));
      } else {
        throw Exception('Erreur ${response.statusCode}');
      }
    } catch (e) {
      print('Erreur getUserById: $e');
      rethrow;
    }
  }

  // Créer un utilisateur
  Future<User> createUser({
    required String email,
    required String password,
    required int idpersonne,
    required List<String> roles,
  }) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/users'),
        headers: headers,
        body: jsonEncode({
          'email': email,
          'password': password,
          'idpersonne': idpersonne,
          'roles': roles,
          'changepassword': false,
        }),
      );

      if (response.statusCode == 201) {
        return User.fromJson(jsonDecode(response.body));
      } else {
        throw Exception('Erreur ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('Erreur createUser: $e');
      rethrow;
    }
  }

  // Mettre à jour un utilisateur
  Future<User> updateUser({
    required int id,
    String? email,
    String? password,
    int? idpersonne,
    List<String>? roles,
    bool? changepassword,
  }) async {
    try {
      final headers = await _getHeaders();
      final Map<String, dynamic> body = {};

      if (email != null) body['email'] = email;
      if (password != null) body['password'] = password;
      if (idpersonne != null) body['idpersonne'] = idpersonne;
      if (roles != null) body['roles'] = roles;
      if (changepassword != null) body['changepassword'] = changepassword;

      final response = await http.put(
        Uri.parse('$baseUrl/users/$id'),
        headers: headers,
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        return User.fromJson(jsonDecode(response.body));
      } else {
        throw Exception('Erreur ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('Erreur updateUser: $e');
      rethrow;
    }
  }

  // Supprimer un utilisateur
  Future<void> deleteUser(int id) async {
    try {
      final headers = await _getHeaders();
      final response = await http.delete(
        Uri.parse('$baseUrl/users/$id'),
        headers: headers,
      );

      if (response.statusCode != 204 && response.statusCode != 200) {
        throw Exception('Erreur ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('Erreur deleteUser: $e');
      rethrow;
    }
  }

  // Changer le rôle d'un utilisateur
  Future<User> changeUserRole(int userId, List<String> newRoles) async {
    return await updateUser(id: userId, roles: newRoles);
  }

  // Forcer le changement de mot de passe
  Future<User> forcePasswordChange(int userId, {required bool force}) async {
    return await updateUser(id: userId, changepassword: force);
  }

  // Rechercher des utilisateurs
  Future<List<User>> searchUsers(String query) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/users/search?q=$query'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => User.fromJson(json)).toList();
      } else {
        throw Exception('Erreur ${response.statusCode}');
      }
    } catch (e) {
      print('Erreur searchUsers: $e');
      return [];
    }
  }
}