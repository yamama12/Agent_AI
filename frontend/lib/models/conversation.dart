// lib/models/conversation.dart
import 'chat_message.dart';

class Conversation {
  final String id;
  String title;
  final DateTime createdAt;
  List<ChatMessage> messages;

  Conversation({
    required this.id,
    required this.title,
    required this.createdAt,
    required this.messages,
  });
}