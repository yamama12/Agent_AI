import 'package:flutter/material.dart';

class ChatInput extends StatelessWidget {
  final TextEditingController controller;
  final Function(String) onSend;

  const ChatInput({
    super.key,
    required this.controller,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: controller,
            decoration: const InputDecoration(
              hintText: "Tapez votre message...",
            ),
            onSubmitted: onSend,
          ),
        ),
        IconButton(
          icon: const Icon(Icons.send),
          onPressed: () => onSend(controller.text),
        ),
      ],
    );
  }
}
