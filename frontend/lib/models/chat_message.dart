// lib/models/chat_message.dart
import 'dart:typed_data';

enum ChatMessageType { user, bot }

class StudentCandidate {
  final String matricule;
  final String prenom;
  final String nom;

  // Getter pour fullName
  String get fullName => '$prenom $nom';

  const StudentCandidate({
    required this.matricule,
    required this.prenom,
    required this.nom,
  });

  factory StudentCandidate.fromJson(Map<String, dynamic> json) {
    return StudentCandidate(
      matricule: json['matricule'].toString(),
      prenom: json['prenom'].toString(),
      nom: json['nom'].toString(),
    );
  }
}

class ChatMessage {
  final ChatMessageType type;
  final String text;
  final Uint8List? imageBytes;
  final String? imageUrl;
  final List<StudentCandidate> candidates;
  final String? selectionRequest;
  final DateTime timestamp;

  // Getter pour sender (compatibilité avec le code existant)
  String get sender => type == ChatMessageType.user ? "user" : "bot";

  ChatMessage({
    required this.type,
    required this.text,
    this.imageBytes,
    this.imageUrl,
    this.candidates = const [],
    this.selectionRequest,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  // Constructeur nommé pour les messages texte
  factory ChatMessage.text({
    required String sender,
    required String text,
    required DateTime timestamp,
    List<StudentCandidate> candidates = const [],
    String? selectionRequest,
  }) {
    return ChatMessage(
      type: sender == "user" ? ChatMessageType.user : ChatMessageType.bot,
      text: text,
      timestamp: timestamp,
      candidates: candidates,
      selectionRequest: selectionRequest,
    );
  }

  // Constructeur nommé pour les images (binaires)
  factory ChatMessage.image({
    required String sender,
    required Uint8List imageBytes,
    required DateTime timestamp,
  }) {
    return ChatMessage(
      type: sender == "user" ? ChatMessageType.user : ChatMessageType.bot,
      text: "",
      imageBytes: imageBytes,
      timestamp: timestamp,
    );
  }

  // NOUVEAU: Constructeur nommé pour les images URL
  factory ChatMessage.imageUrl({
    required String sender,
    required String imageUrl,
    required DateTime timestamp,
  }) {
    return ChatMessage(
      type: sender == "user" ? ChatMessageType.user : ChatMessageType.bot,
      text: "",
      imageUrl: imageUrl,
      timestamp: timestamp,
    );
  }
}