import 'dart:convert';
import 'package:flutter/material.dart';


class User {
  final int id;
  final String email;
  final String? password; // Optionnel pour la sécurité
  final int idpersonne;
  final List<String> roles;
  final String? token;
  final bool changepassword;

  User({
    required this.id,
    required this.email,
    this.password,
    required this.idpersonne,
    required this.roles,
    this.token,
    required this.changepassword,
  });

  // Vérifier si l'utilisateur est super admin
  bool get isSuperAdmin => roles.contains('ROLE_SUPER_ADMIN');

  // Vérifier si l'utilisateur est admin
  bool get isAdmin => roles.contains('ROLE_ADMIN');

  // Rôle principal pour l'affichage
  String get displayRole {
    if (isSuperAdmin) return 'Super Admin';
    if (isAdmin) return 'Admin';
    return 'Utilisateur';
  }

  // Couleur selon le rôle
  Color get roleColor {
    if (isSuperAdmin) return const Color(0xFFC69450); // Doré
    if (isAdmin) return const Color(0xFF0F2447); // Bleu foncé
    return const Color(0xFF64748B); // Gris
  }

  factory User.fromJson(Map<String, dynamic> json) {
    // Gestion des roles qui peut être string ou liste
    List<String> rolesList = [];
    if (json['roles'] is String) {
      try {
        final parsed = jsonDecode(json['roles']);
        if (parsed is List) {
          rolesList = List<String>.from(parsed);
        }
      } catch (e) {
        rolesList = [json['roles']];
      }
    } else if (json['roles'] is List) {
      rolesList = List<String>.from(json['roles']);
    }

    return User(
      id: json['id'] ?? 0,
      email: json['email'] ?? '',
      password: json['password'],
      idpersonne: json['idpersonne'] ?? 0,
      roles: rolesList,
      token: json['token'],
      changepassword: json['changepassword'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'idpersonne': idpersonne,
      'roles': roles,
      'changepassword': changepassword,
      if (token != null) 'token': token,
    };
  }
}