import 'dart:convert';

class ProfileData {
  final int id;
  final String email;
  final String? nom;
  final String? prenom;
  final String? telephone;
  final String? cin;
  final String? emailPersonne;
  final List<String> roles;
  final DateTime dateCreation;

  ProfileData({
    required this.id,
    required this.email,
    this.nom,
    this.prenom,
    this.telephone,
    this.cin,
    this.emailPersonne,
    required this.roles,
    required this.dateCreation,
  });

  String get fullName => [prenom, nom].where((part) => part != null && part.isNotEmpty).join(' ');

  factory ProfileData.fromJson(Map<String, dynamic> json) {
    List<String> rolesList = [];
    if (json['roles'] is String) {
      try {
        final parsed = jsonDecode(json['roles']);
        if (parsed is List) {
          rolesList = List<String>.from(parsed);
        }
      } catch (_) {
        rolesList = [json['roles']];
      }
    } else if (json['roles'] is List) {
      rolesList = List<String>.from(json['roles']);
    }

    return ProfileData(
      id: json['id'] ?? 0,
      email: json['email'] ?? '',
      nom: json['nom'],
      prenom: json['prenom'],
      telephone: json['telephone'],
      cin: json['cin'],
      emailPersonne: json['email_personne'],
      roles: rolesList,
      dateCreation: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'nom': nom,
      'prenom': prenom,
      'telephone': telephone,
      'cin': cin,
      'email_personne': emailPersonne,
      'roles': roles,
      'created_at': dateCreation.toIso8601String(),
    };
  }
}

class ProfileUpdateRequest {
  final String? nom;
  final String? prenom;
  final String? telephone;
  final String? cin;
  final String? emailPersonne;
  final String? currentPassword;
  final String? newPassword;

  ProfileUpdateRequest({
    this.nom,
    this.prenom,
    this.telephone,
    this.cin,
    this.emailPersonne,
    this.currentPassword,
    this.newPassword,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    if (nom != null) map['nom'] = nom;
    if (prenom != null) map['prenom'] = prenom;
    if (telephone != null) map['telephone'] = telephone;
    if (cin != null) map['cin'] = cin;
    if (emailPersonne != null) map['email_personne'] = emailPersonne;
    if (currentPassword != null && newPassword != null) {
      map['current_password'] = currentPassword;
      map['new_password'] = newPassword;
    }
    return map;
  }
}