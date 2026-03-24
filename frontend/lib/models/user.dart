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
  final String? nom;
  final String? prenom;
  final String? telephone;
  final String? cin;
  final String? emailPersonne;

  User({
    required this.id,
    required this.email,
    this.password,
    required this.idpersonne,
    required this.roles,
    this.token,
    required this.changepassword,
    this.nom,
    this.prenom,
    this.telephone,
    this.cin,
    this.emailPersonne,
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
      changepassword: _parseBool(json['changepassword']),
      nom: json['nom'],
      prenom: json['prenom'],
      telephone: json['telephone'],
      cin: json['cin'],
      emailPersonne: json['email_personne'],
    );
  }

  static bool _parseBool(dynamic value) {
    if (value is bool) return value;
    if (value is String) {
      final v = value.trim().toLowerCase();
      return v == 'true' || v == '1' || v == 'yes';
    }
    if (value is num) return value != 0;
    return false;
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'idpersonne': idpersonne,
      'roles': roles,
      'changepassword': changepassword,
      'nom': nom,
      'prenom': prenom,
      'telephone': telephone,
      'cin': cin,
      'email_personne': emailPersonne,
      if (token != null) 'token': token,
    };
  }
}
