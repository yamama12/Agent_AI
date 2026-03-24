// services/user_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/user.dart';
import 'auth_service.dart';

class UserService {
  static const String baseUrl = 'http://localhost:8000';
  final AuthService _authService = AuthService();

  String _extractErrorMessage(http.Response response) {
    final fallback = 'Erreur ${response.statusCode}';
    if (response.body.isEmpty) return fallback;
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

  // Headers avec token d'authentification
  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  // Recuperer les utilisateurs : ADMIN et SUPER_ADMIN uniquement
  Future<List<User>> getAdmins() async {
    final headers = await _getHeaders();

    final response = await http.get(
      Uri.parse('$baseUrl/users/admins'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      List data = jsonDecode(response.body);
      return data.map((e) => User.fromJson(e)).toList();
    } else {
      throw Exception("Erreur lors de la recuperation des admins");
    }
  }

  // Recuperer tous les utilisateurs avec infos personne
  Future<List<User>> getUsers() async {
    final headers = await _getHeaders();

    final response = await http.get(
      Uri.parse('$baseUrl/users'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      List data = jsonDecode(response.body);
      return data.map((e) => User.fromJson(e)).toList();
    } else {
      throw Exception("Erreur lors de la recuperation des utilisateurs");
    }
  }

  // Recuperer un utilisateur par ID
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

  // Creer un utilisateur (cree aussi la personne)
  Future<User> createUser({
    required String nom,
    required String prenom,
    required String telephone,
    required String cin,
    required String emailPersonne,
    required String email,
    required String password,
    required List<String> roles,
  }) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/users'),
        headers: headers,
        body: jsonEncode({
          'nom': nom,
          'prenom': prenom,
          'telephone': telephone,
          'cin': cin,
          'email_personne': emailPersonne,
          'email': email,
          'password': password,
          'roles': roles,
          'changepassword': false,
        }),
      );

      if (response.statusCode == 201) {
        return User.fromJson(jsonDecode(response.body));
      } else {
        final message = _extractErrorMessage(response);
        throw Exception(message);
      }
    } catch (e) {
      print('Erreur createUser: $e');
      rethrow;
    }
  }

  // Mettre a jour un utilisateur
  Future<User> updateUser({
    required int id,
    String? nom,
    String? prenom,
    String? telephone,
    String? cin,
    String? emailPersonne,
    String? email,
    String? password,
    List<String>? roles,
    bool? changepassword,
  }) async {
    try {
      final headers = await _getHeaders();
      final Map<String, dynamic> body = {};

      if (nom != null) body['nom'] = nom;
      if (prenom != null) body['prenom'] = prenom;
      if (telephone != null) body['telephone'] = telephone;
      if (cin != null) body['cin'] = cin;
      if (emailPersonne != null) body['email_personne'] = emailPersonne;
      if (email != null) body['email'] = email;
      if (password != null) body['password'] = password;
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
        final message = _extractErrorMessage(response);
        throw Exception(message);
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
        final message = _extractErrorMessage(response);
        throw Exception(message);
      }
    } catch (e) {
      print('Erreur deleteUser: $e');
      rethrow;
    }
  }

  // Changer le role d'un utilisateur
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
