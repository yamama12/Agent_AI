import 'package:flutter/material.dart';
import '../models/message_model.dart';
import 'package:url_launcher/url_launcher.dart';

class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.sender == "user";

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
        padding: const EdgeInsets.all(14),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.8,
        ),
        decoration: BoxDecoration(
          color: isUser ? Colors.blue[800] : Colors.grey[200],
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // 📝 TEXTE
            if (message.text.isNotEmpty)
              Text(
                message.text,
                style: TextStyle(
                  color: isUser ? Colors.white : Colors.black87,
                ),
              ),

            // 📊 GRAPHE
          if (message.imageUrl != null) ...[
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.network(
              message.imageUrl!,
              fit: BoxFit.contain,
              loadingBuilder: (context, child, loadingProgress) {
          if (loadingProgress == null) return child;
            return const Padding(
            padding: EdgeInsets.all(8.0),
            child: CircularProgressIndicator(),
          );
        },
        errorBuilder: (context, error, stackTrace) {
          return const Text("❌ Impossible de charger le graphe");
                  },
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}