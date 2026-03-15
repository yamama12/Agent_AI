import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';
import 'package:file_saver/file_saver.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/chat_message.dart';
import '../services/chat_api_service.dart';
import '../services/auth_service.dart';
import 'login_screen.dart';
import 'dart:convert';
import 'dart:typed_data';
import '../models/conversation.dart';
import 'user_management_screen.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, this.startNewConversationOnOpen = false});

  final bool startNewConversationOnOpen;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  // Historique des messages de la conversation active
  Conversation? _activeConversation;
  final List<Conversation> _conversations = [];
  final ScrollController _scrollController = ScrollController();
  final FocusNode _focusNode = FocusNode();

  bool _isLoading = false;
  bool _isComposing = false;
  bool _sidebarVisible = true;
  bool _isDownloadingGraph = false;
  List<String> _userRoles = [];
  static const String _historyStorageKeyPrefix = 'chat_history_conversations_';
  String _historyStorageKey = '${_historyStorageKeyPrefix}guest';

  // Palette de couleurs améliorée
  static const Color _primaryBlue = Color(0xFF0F2447);
  static const Color _lightYellow = Color(0xFFF8D17A);
  static const Color _darkYellow = Color(0xFFC69450);
  static const Color _backgroundLight = Color(0xFFF5F7FB);
  static const Color _white = Color(0xFFFFFFFF);
  static const Color _borderLight = Color(0xFFE8ECF2);
  static const Color _textPrimary = Color(0xFF1A2B3C);
  static const Color _textSecondary = Color(0xFF64748B);
  static const Color _hoverBlue = Color(0xFF1E3A5F);
  static const Color _surfaceLight = Color(0xFFF9FAFC);

  late AnimationController _typingController;
  late Animation<double> _typingAnimation;

  Future<void> _checkLoginStatus() async {
    final authService = AuthService();
    final isLoggedIn = await authService.isLoggedIn();

    if (!isLoggedIn && mounted) {
      // Si non connecté, rediriger vers login
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => LoginScreen()),
      );
    } else {
      // Afficher les infos de connexion
      final token = await authService.getToken();
      final role = await authService.getRole();
      print('✅ Utilisateur connecté - Token: ${token?.substring(0, 20)}...');
      print('👤 Rôle: $role');
      
      // Parser les rôles
      if (role != null) {
        try {
          _userRoles = List<String>.from(jsonDecode(role));
        } catch (e) {
          _userRoles = [role];
        }
      }
    }
  }

  @override
  void initState() {
    super.initState();
    _checkLoginStatus();
    _typingController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();

    _typingAnimation = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _typingController, curve: Curves.easeInOut),
    );

    _controller.addListener(_onTextChanged);
    _loadConversations().then((_) {
      if (!mounted) return;
      if (widget.startNewConversationOnOpen) {
        _startNewChat();
      }
    });
  }

  void _onTextChanged() {
    setState(() {
      _isComposing = _controller.text.trim().isNotEmpty;
    });
  }

  @override
  void dispose() {
    _controller.removeListener(_onTextChanged);
    _controller.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    _typingController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _toggleSidebar() {
    setState(() {
      _sidebarVisible = !_sidebarVisible;
    });
  }

  void _startNewChat() {
    final newConversation = Conversation(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: "Nouvelle conversation",
      createdAt: DateTime.now(),
      messages: [],
    );
    setState(() {
      _conversations.insert(0, newConversation);
      _activeConversation = newConversation;
      _controller.clear();
      _isComposing = false;
    });
    _saveConversations();
  }

  String _formatDate(DateTime date) {
    return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
  }
// Normalisation du texte pour la recherche (minuscules, suppression des espaces superflus)
  String _normalizeSearchText(String value) {
    return value.toLowerCase().replaceAll(RegExp(r'\s+'), ' ').trim();
  }

  Future<String> _resolveHistoryKey() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('user_email') ?? 'guest';
    final normalized = raw.trim().isEmpty
        ? 'guest'
        : raw.trim().toLowerCase().replaceAll(' ', '_');
    return '$_historyStorageKeyPrefix$normalized';
  }

  Future<void> _loadConversations() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _historyStorageKey = await _resolveHistoryKey();
      final raw = prefs.getString(_historyStorageKey);
      if (raw == null || raw.isEmpty) return;

      final decoded = jsonDecode(raw);
      if (decoded is! List) return;

      final loaded = <Conversation>[];
      for (final item in decoded) {
        if (item is! Map) continue;
        final map = Map<String, dynamic>.from(item);
        final messagesRaw = map['messages'];
        final messages = <ChatMessage>[];
        if (messagesRaw is List) {
          for (final msgItem in messagesRaw) {
            if (msgItem is! Map) continue;
            final msgMap = Map<String, dynamic>.from(msgItem);
            final sender = (msgMap['sender'] ?? 'bot').toString();
            final text = (msgMap['text'] ?? '').toString();
            final imageUrl = msgMap['imageUrl']?.toString();
            final timestampRaw = msgMap['timestamp']?.toString();
            DateTime timestamp;
            try {
              timestamp = timestampRaw != null
                  ? DateTime.parse(timestampRaw)
                  : DateTime.now();
            } catch (_) {
              timestamp = DateTime.now();
            }

            if (imageUrl != null && imageUrl.isNotEmpty && text.isEmpty) {
              messages.add(
                ChatMessage.imageUrl(
                  sender: sender,
                  imageUrl: imageUrl,
                  timestamp: timestamp,
                ),
              );
            } else if (text.isNotEmpty) {
              messages.add(
                ChatMessage.text(
                  sender: sender,
                  text: text,
                  timestamp: timestamp,
                ),
              );
            }
          }
        }

        final createdAtRaw = map['createdAt']?.toString();
        DateTime createdAt;
        try {
          createdAt = createdAtRaw != null
              ? DateTime.parse(createdAtRaw)
              : DateTime.now();
        } catch (_) {
          createdAt = DateTime.now();
        }

        loaded.add(
          Conversation(
            id: (map['id'] ?? DateTime.now().millisecondsSinceEpoch).toString(),
            title: (map['title'] ?? 'Nouvelle conversation').toString(),
            createdAt: createdAt,
            messages: messages,
          ),
        );
      }

      if (!mounted) return;
      setState(() {
        _conversations
          ..clear()
          ..addAll(loaded);
        if (_conversations.isNotEmpty) {
          _activeConversation ??= _conversations.first;
        }
      });
    } catch (e) {
      print('Erreur chargement historique: $e');
    }
  }

  Future<void> _saveConversations() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _historyStorageKey = await _resolveHistoryKey();
      final data =
          _conversations.map((conversation) => _conversationToJson(conversation))
              .toList();
      await prefs.setString(_historyStorageKey, jsonEncode(data));
    } catch (e) {
      print('Erreur sauvegarde historique: $e');
    }
  }

  Map<String, dynamic> _conversationToJson(Conversation conversation) {
    return {
      'id': conversation.id,
      'title': conversation.title,
      'createdAt': conversation.createdAt.toIso8601String(),
      'messages': conversation.messages.map((msg) {
        return {
          'sender': msg.sender,
          'text': msg.text,
          'imageUrl': msg.imageUrl,
          'timestamp': msg.timestamp.toIso8601String(),
        };
      }).toList(),
    };
  }

// Affichage du dialogue de recherche dans l'historique avec filtrage en temps réel et aperçu des conversations
  void _showHistorySearchDialog() {
    final searchController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          final double dialogWidth =
              (MediaQuery.of(context).size.width * 0.9)
                  .clamp(280.0, 520.0)
                  .toDouble();
          final query = _normalizeSearchText(searchController.text);
          final filtered = query.isEmpty
              ? _conversations
              : _conversations.where((conversation) {
                  final titleMatch = _normalizeSearchText(
                    conversation.title,
                  ).contains(query);

                  final messageMatch = conversation.messages.any((msg) {
                    final msgText = _normalizeSearchText(msg.text);
                    final urlText = msg.imageUrl != null
                        ? _normalizeSearchText(msg.imageUrl!)
                        : "";
                    return msgText.contains(query) || urlText.contains(query);
                  });

                  return titleMatch || messageMatch;
                }).toList();

          return Dialog(
            backgroundColor: Colors.transparent,
            child: Container(
              width: dialogWidth,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: _white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: _primaryBlue.withOpacity(0.12),
                    blurRadius: 20,
                    offset: const Offset(0, 6),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      const Icon(
                        Icons.search_rounded,
                        color: _primaryBlue,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          "Rechercher dans l'historique",
                          style: TextStyle(
                            color: _textPrimary,
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      IconButton(
                        onPressed: () => Navigator.pop(context),
                        icon: const Icon(Icons.close_rounded),
                        color: _textSecondary,
                        tooltip: "Fermer",
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Container(
                    decoration: BoxDecoration(
                      color: _surfaceLight,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: _borderLight, width: 1),
                    ),
                    child: TextField(
                      controller: searchController,
                      onChanged: (_) => setDialogState(() {}),
                      decoration: InputDecoration(
                        hintText: "Rechercher une conversation...",
                        hintStyle: TextStyle(
                          color: _textSecondary.withOpacity(0.6),
                          fontSize: 13,
                        ),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 12,
                        ),
                        prefixIcon: Icon(
                          Icons.search_rounded,
                          color: _darkYellow,
                          size: 18,
                        ),
                      ),
                      style: const TextStyle(
                        fontSize: 13,
                        color: _textPrimary,
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      "Historique (${filtered.length})",
                      style: TextStyle(
                        fontSize: 12,
                        color: _textSecondary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (filtered.isEmpty)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 24),
                      alignment: Alignment.center,
                      child: Text(
                        "Aucun r\u00e9sultat",
                        style: TextStyle(
                          color: _textSecondary,
                          fontSize: 12,
                        ),
                      ),
                    )
                  else
                    ConstrainedBox(
                      constraints: const BoxConstraints(maxHeight: 360),
                      child: ListView.separated(
                        shrinkWrap: true,
                        itemCount: filtered.length,
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 6),
                        itemBuilder: (context, index) {
                          final conversation = filtered[index];
                          final preview = conversation.messages.isNotEmpty
                              ? conversation.messages.last.text
                              : "Conversation vide";
                          final dateText = _formatDate(conversation.createdAt);

                          return Material(
                            color: Colors.transparent,
                            child: InkWell(
                              onTap: () {
                                setState(() {
                                  _activeConversation = conversation;
                                });
                                Navigator.pop(context);
                              },
                              borderRadius: BorderRadius.circular(12),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 10,
                                ),
                                decoration: BoxDecoration(
                                  color: conversation == _activeConversation
                                      ? _primaryBlue.withOpacity(0.05)
                                      : _surfaceLight,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color:
                                        conversation == _activeConversation
                                            ? _primaryBlue.withOpacity(0.12)
                                            : _borderLight,
                                    width: 1,
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: _primaryBlue.withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: const Icon(
                                        Icons.chat_bubble_outline_rounded,
                                        size: 16,
                                        color: _primaryBlue,
                                      ),
                                    ),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            conversation.title,
                                            style: TextStyle(
                                              fontSize: 13,
                                              fontWeight: FontWeight.w600,
                                              color: _textPrimary,
                                            ),
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                          const SizedBox(height: 2),
                                          Text(
                                            preview,
                                            style: TextStyle(
                                              fontSize: 11,
                                              color: _textSecondary,
                                            ),
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                          const SizedBox(height: 2),
                                          Text(
                                            dateText,
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: _darkYellow,
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    IconButton(
                                      onPressed: () {
                                        _confirmDeleteConversation(
                                          conversation,
                                          onDeleted: () =>
                                              setDialogState(() {}),
                                        );
                                      },
                                      icon: const Icon(
                                        Icons.delete_outline_rounded,
                                        size: 18,
                                        color: _textSecondary,
                                      ),
                                      tooltip: "Supprimer",
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                ],
              ),
            ),
          );
        },
      ),
    ).then((_) => searchController.dispose());
  }

  String _generateConversationTitle(String text) {
    final normalized = text.replaceAll(RegExp(r'\s+'), ' ').trim();
    if (normalized.isEmpty) {
      return "Nouvelle conversation";
    }
    const maxLen = 45;
    if (normalized.length <= maxLen) {
      return normalized;
    }
    return '${normalized.substring(0, maxLen).trimRight()}...';
  }

  Future<void> _sendMessage({
    String? messageOverride,
    String? userVisibleText,
  }) async {
    final outboundText = (messageOverride ?? _controller.text).trim();
    if (outboundText.isEmpty) return;

    final userText = (userVisibleText ?? outboundText).trim();

    // Désactiver l'envoi pendant le chargement
    setState(() {
      _isLoading = true;
    });

    // Ajouter le message utilisateur
    final userMessage = ChatMessage.text(
      sender: "user",
      text: userText,
      timestamp: DateTime.now(),
    );

    // S'assure qu'une conversation active existe
    _activeConversation ??= Conversation(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: "Nouvelle conversation",
      createdAt: DateTime.now(),
      messages: [],
    );

    if (!_conversations.contains(_activeConversation)) {
      _conversations.insert(0, _activeConversation!);
    }

    setState(() {
      _activeConversation!.messages.add(userMessage);
      _controller.clear();
      _isComposing = false;
    });
    _saveConversations();

    // Mettre à jour le titre si c'est une nouvelle conversation
    if (_activeConversation!.title == "Nouvelle conversation") {
      final updatedConversation = Conversation(
        id: _activeConversation!.id,
        title: _generateConversationTitle(userText),
        createdAt: _activeConversation!.createdAt,
        messages: _activeConversation!.messages,
      );
      final index = _conversations.indexWhere(
        (c) => c.id == _activeConversation!.id,
      );
      if (index != -1) {
        _conversations[index] = updatedConversation;
      }
      _activeConversation = updatedConversation;
    }
    _saveConversations();

    _scrollToBottom();
    _focusNode.unfocus();

    try {
      final response = await ChatApiService.sendMessageRaw(outboundText);
      final contentType = response.headers['content-type'] ?? "";

      // CAS GRAPHE (image/png) - Image seule
      if (contentType.contains("image/png")) {
        setState(() {
          _activeConversation!.messages.add(
            ChatMessage.image(
              sender: "bot",
              imageBytes: response.bodyBytes,
              timestamp: DateTime.now(),
            ),
          );
        });
        _saveConversations();
      }
      // CAS TEXTE JSON
      else {
        final decoded = jsonDecode(response.body);

        final rawCandidates = decoded['candidates'];
        final candidates = <StudentCandidate>[];

        if (rawCandidates is List) {
          for (final item in rawCandidates) {
            if (item is Map) {
              candidates.add(
                StudentCandidate.fromJson(Map<String, dynamic>.from(item)),
              );
            }
          }
        }

        // Ajouter d'abord le message texte
        setState(() {
          _activeConversation!.messages.add(
            ChatMessage.text(
              sender: "bot",
              text:
                  decoded['response'] ??
                  "Je n'ai pas de réponse pour le moment.",
              timestamp: DateTime.now(),
              candidates: candidates,
              selectionRequest: decoded['selection_request']?.toString(),
            ),
          );
        });
        _saveConversations();

        // Ensuite, s'il y a une image, l'ajouter comme message séparé (sans bulle)
        if (decoded['graph'] != null) {
          if (decoded['graph']['url'] != null) {
            // Image URL dans un message séparé
            Future.delayed(const Duration(milliseconds: 100), () {
              setState(() {
                _activeConversation!.messages.add(
                  ChatMessage.imageUrl(
                    sender: "bot",
                    imageUrl: decoded['graph']['url'],
                    timestamp: DateTime.now(),
                  ),
                );
              });
              _saveConversations();
              _scrollToBottom();
            });
          } else if (decoded['graph']['image_base64'] != null) {
            // Image base64 dans un message séparé
            try {
              final base64String = decoded['graph']['image_base64'];
              final imageBytes = base64Decode(base64String);
              Future.delayed(const Duration(milliseconds: 100), () {
                setState(() {
                  _activeConversation!.messages.add(
                    ChatMessage.image(
                      sender: "bot",
                      imageBytes: imageBytes,
                      timestamp: DateTime.now(),
                    ),
                  );
                });
                _saveConversations();
                _scrollToBottom();
              });
            } catch (e) {
              print('Erreur décodage base64: $e');
            }
          }
        }
      }
    } catch (e) {
      print('Erreur: $e');
      setState(() {
        _activeConversation!.messages.add(
          ChatMessage.text(
            sender: "bot",
            text: "Désolé, je rencontre des difficultés. ($e)",
            timestamp: DateTime.now(),
          ),
        );
      });
      _saveConversations();
    } finally {
      setState(() {
        _isLoading = false;
      });
      _scrollToBottom();
    }
  }

  Future<void> _selectCandidate(
    ChatMessage sourceMessage,
    StudentCandidate candidate,
  ) async {
    if (_isLoading) return;

    final selectionBase = (sourceMessage.selectionRequest ?? '').trim();
    final outboundText = selectionBase.isEmpty
        ? candidate.matricule
        : '$selectionBase ${candidate.matricule}';
    final visibleChoice = '${candidate.fullName}';

    await _sendMessage(
      messageOverride: outboundText,
      userVisibleText: visibleChoice,
    );
  }

  void _showMenu(BuildContext context) async {
    List<PopupMenuEntry<String>> items = [
      const PopupMenuItem<String>(
        value: 'profile',
        child: Row(
          children: [
            Icon(
              Icons.person_outline_rounded,
              color: Color(0xFF0F2447),
              size: 20,
            ),
            SizedBox(width: 12),
            Text('Mon profil', style: TextStyle(fontSize: 14)),
          ],
        ),
      ),
    ];

    if (_userRoles.contains('ROLE_SUPER_ADMIN')) {
      items.add(
        const PopupMenuItem<String>(
          value: 'user_management',
          child: Row(
            children: [
              Icon(
                Icons.people_outline_rounded,
                color: Color(0xFF0F2447),
                size: 20,
              ),
              SizedBox(width: 12),
              Text('Gestion des utilisateurs', style: TextStyle(fontSize: 14)),
            ],
          ),
        ),
      );
    }

    items.add(const PopupMenuDivider());

    items.add(
      PopupMenuItem<String>(
        value: 'logout',
        child: Row(
          children: [
            Icon(Icons.logout_rounded, color: Colors.red, size: 20),
            const SizedBox(width: 12),
            Text(
              'Déconnexion',
              style: TextStyle(color: Colors.red, fontSize: 14),
            ),
          ],
        ),
      ),
    );

    final result = await showMenu<String>(
      context: context,
      position: const RelativeRect.fromLTRB(10, 90, 0, 0),
      items: items,
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    );

    if (result != null) {
      _handleMenuSelection(result, context);
    }
  }

  void _handleMenuSelection(String value, BuildContext context) {
    switch (value) {
      case 'profile':
        // TODO: Naviguer vers le profil
        break;
      case 'user_management':
        // TODO: Naviguer vers la gestion des utilisateurs
        Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => UserManagementScreen()),
        );
        break;
      case 'logout':
        _confirmLogout(context);
        break;
    }
  }

  void _confirmLogout(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.logout_rounded, color: Colors.red, size: 24),
            SizedBox(width: 12),
            Text(
              'Déconnexion',
              style: TextStyle(
                color: Colors.red,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        content: const Text(
          'Êtes-vous sûr de vouloir vous déconnecter ?',
          style: TextStyle(fontSize: 15, color: Colors.black87),
        ),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            ),
            child: Text(
              'Annuler',
              style: TextStyle(color: Colors.blue.shade800, fontSize: 15),
            ),
          ),
          ElevatedButton(
            onPressed: () async {
              // Fermer le dialogue
              Navigator.pop(context);

              // Créer une instance de AuthService
              final authService = AuthService();

              // Effacer les données
              await authService.logout();

              // Naviguer vers l'écran de login (l'historique reste sauvegardé)
              if (!context.mounted) return;
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => LoginScreen()),
                (route) => false, // Supprime toutes les routes précédentes
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            ),
            child: const Text('Déconnexion', style: TextStyle(fontSize: 15)),
          ),
        ],
      ),
    );
  }

  Future<void> _downloadGraph(ChatMessage msg) async {
    if (_isDownloadingGraph) return;

    setState(() {
      _isDownloadingGraph = true;
    });

    try {
      Uint8List pngBytes;

      if (msg.imageBytes != null) {
        pngBytes = msg.imageBytes!;
      } else if (msg.imageUrl != null) {
        final response = await http.get(Uri.parse(msg.imageUrl!));
        if (response.statusCode != 200) {
          throw Exception(
            "Impossible de recuperer l'image (${response.statusCode})",
          );
        }
        pngBytes = response.bodyBytes;
      } else {
        throw Exception("Aucune image a telecharger");
      }

      final now = DateTime.now();
      final fileName =
          "graphe_${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}_${now.hour.toString().padLeft(2, '0')}${now.minute.toString().padLeft(2, '0')}${now.second.toString().padLeft(2, '0')}";

      await FileSaver.instance.saveFile(
        name: fileName,
        bytes: pngBytes,
        fileExtension: "png",
        mimeType: MimeType.png,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Graphe telecharge en PNG"),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Echec du telechargement: $e"),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isDownloadingGraph = false;
        });
      }
    }
  }

  Widget _buildMessageText(String text, bool isUser) {
    final urlRegex = RegExp(r'(https?:\/\/[^\s]+)');
    final matches = urlRegex.allMatches(text);

    if (matches.isEmpty) {
      return SelectableText(
        text,
        style: TextStyle(
          fontSize: 14,
          color: isUser ? _white : _textPrimary,
          height: 1.5,
          fontWeight: FontWeight.w400,
        ),
      );
    }

    final List<TextSpan> spans = [];
    int lastIndex = 0;

    for (final match in matches) {
      if (match.start > lastIndex) {
        spans.add(
          TextSpan(
            text: text.substring(lastIndex, match.start),
            style: TextStyle(
              fontSize: 14,
              color: isUser ? _white : _textPrimary,
              height: 1.5,
            ),
          ),
        );
      }

      final url = match.group(0)!;
      spans.add(
        TextSpan(
          text: url,
          style: TextStyle(
            fontSize: 14,
            color: isUser ? _lightYellow : _darkYellow,
            decoration: TextDecoration.underline,
            fontWeight: FontWeight.w600,
            decorationColor: isUser ? _lightYellow : _darkYellow,
            decorationThickness: 1.5,
          ),
          recognizer: TapGestureRecognizer()
            ..onTap = () async {
              final uri = Uri.parse(url);
              if (await canLaunchUrl(uri)) {
                await launchUrl(uri, mode: LaunchMode.externalApplication);
              }
            },
        ),
      );

      lastIndex = match.end;
    }

    if (lastIndex < text.length) {
      spans.add(
        TextSpan(
          text: text.substring(lastIndex),
          style: TextStyle(
            fontSize: 14,
            color: isUser ? _white : _textPrimary,
            height: 1.5,
          ),
        ),
      );
    }

    return RichText(text: TextSpan(children: spans));
  }

  // Boutons de sélection de candidats - petits, colorés avec noms complets
  Widget _buildCandidateButtons(ChatMessage msg) {
    if (msg.candidates.isEmpty) return const SizedBox.shrink();

    // Palette de couleurs pastel élégantes
    final List<Color> buttonColors = [
      const Color(0xFF16537e), // Bleu ardoise
      const Color(0xFF38761d), // Vert sauge
      const Color(0xFFcc0000), // Rouge brique
      const Color(0xFF6A7B8C), // Bleu-gris
      const Color(0xFF8F7A6B), // Brun doux
    ];

    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Wrap(
        spacing: 6,
        runSpacing: 6,
        children: msg.candidates.asMap().entries.map((entry) {
          int index = entry.key;
          var candidate = entry.value;
          Color buttonColor = buttonColors[index % buttonColors.length];

          return TweenAnimationBuilder<double>(
            tween: Tween<double>(begin: 0.0, end: 1.0),
            duration: Duration(milliseconds: 200 + (index * 50)),
            curve: Curves.easeOutBack,
            builder: (context, double scale, child) {
              return Transform.scale(
                scale: scale,
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: _isLoading
                        ? null
                        : () => _selectCandidate(msg, candidate),
                    borderRadius: BorderRadius.circular(25),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: buttonColor,
                        borderRadius: BorderRadius.circular(25),
                        boxShadow: [
                          BoxShadow(
                            color: buttonColor.withOpacity(0.3),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Text(
                        candidate.fullName,
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                ),
              );
            },
          );
        }).toList(),
      ),
    );
  }

  // Indicateur de saisie avec animation fluide et design moderne
  Widget _buildTypingIndicator() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: BoxDecoration(
        color: _white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _lightYellow.withOpacity(0.2)),
        boxShadow: [
          BoxShadow(
            color: _primaryBlue.withOpacity(0.03),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (index) => _buildTypingDot(index)),
      ),
    );
  }

  Widget _buildTypingDot(int index) {
    return AnimatedBuilder(
      animation: _typingAnimation,
      builder: (context, child) {
        return Container(
          width: 8,
          height: 8,
          margin: EdgeInsets.only(right: index < 2 ? 5 : 0),
          decoration: BoxDecoration(
            color: _darkYellow.withOpacity(
              0.3 + (_typingAnimation.value * (0.7 - (index * 0.2))),
            ),
            shape: BoxShape.circle,
          ),
        );
      },
    );
  }

  String _formatTime(DateTime timestamp) {
    return '${timestamp.hour.toString().padLeft(2, '0')}:${timestamp.minute.toString().padLeft(2, '0')}';
  }

  // NOUVELLE NAVBAR ÉLÉGANTE ET MODERNE
  Widget _buildNavbar() {
    final isMobile = MediaQuery.of(context).size.width < 600;

    return Container(
      height: isMobile ? 70 : 80,
      decoration: BoxDecoration(
        color: _white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          // Menu hamburger avec design minimaliste
          if (isMobile) _buildMenuButton() else _buildSidebarToggle(),

          // Logo et titre
          Expanded(child: _buildLogoSection(isMobile)),

          // Actions avec design épuré
          _buildNavbarActions(isMobile),
        ],
      ),
    );
  }

  Widget _buildMenuButton() {
    return Container(
      margin: const EdgeInsets.only(left: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _toggleSidebar,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: Colors.transparent,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              _sidebarVisible ? Icons.close_rounded : Icons.menu_rounded,
              color: _primaryBlue,
              size: 26,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSidebarToggle() {
    return Container(
      margin: const EdgeInsets.only(left: 20),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _toggleSidebar,
          borderRadius: BorderRadius.circular(10),
          child: Container(
            padding: const EdgeInsets.all(10),
            child: AnimatedCrossFade(
              duration: const Duration(milliseconds: 300),
              crossFadeState: _sidebarVisible
                  ? CrossFadeState.showFirst
                  : CrossFadeState.showSecond,
              firstChild: const Icon(
                Icons.menu_open_rounded,
                color: _primaryBlue,
                size: 28,
              ),
              secondChild: const Icon(
                Icons.menu_rounded,
                color: _primaryBlue,
                size: 28,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLogoSection(bool isMobile) {
    return Container(
      margin: const EdgeInsets.only(left: 16),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Logo sans background
          MouseRegion(
            cursor: SystemMouseCursors.click,
            child: SizedBox(
              width: isMobile ? 40 : 50,
              height: isMobile ? 40 : 50,
              child: Image.asset(
                'assets/images/chatbot_logo.png',
                fit: BoxFit.contain,
                errorBuilder: (context, error, stackTrace) {
                  return Icon(
                    Icons.school_rounded,
                    color: _primaryBlue.withOpacity(0.8),
                    size: isMobile ? 40 : 50,
                  );
                },
              ),
            ),
          ),

          const SizedBox(width: 12),

          // Titre élégant
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                "Agent IA",
                style: TextStyle(
                  fontSize: isMobile ? 16 : 18,
                  fontWeight: FontWeight.w500,
                  color: _primaryBlue,
                  letterSpacing: -0.3,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildNavbarActions(bool isMobile) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Bouton info minimaliste
        IconButton(
          icon: Icon(
            Icons.info_outline_rounded,
            color: _primaryBlue.withOpacity(0.7),
            size: isMobile ? 22 : 24,
          ),
          onPressed: _showInfoDialog,
        ),

        if (!isMobile) ...[
          const SizedBox(width: 8),

          // Séparateur vertical élégant
          Container(height: 30, width: 1, color: _borderLight),

          const SizedBox(width: 12),
        ],

        // Menu utilisateur élégant
        Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: () => _showMenu(context),
            borderRadius: BorderRadius.circular(30),
            child: Container(
              margin: const EdgeInsets.only(right: 20, left: 4),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _surfaceLight,
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: _borderLight.withOpacity(0.5)),
              ),
              child: Row(
                children: [
                  // Avatar utilisateur
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [_primaryBlue, _primaryBlue.withOpacity(0.8)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(30),
                    ),
                    child: const Icon(
                      Icons.person_rounded,
                      color: Colors.white,
                      size: 18,
                    ),
                  ),

                  if (!isMobile) ...[
                    const SizedBox(width: 10),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          "Admin",
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: _textPrimary,
                          ),
                        ),
                        Text(
                          "Compte actif",
                          style: TextStyle(fontSize: 10, color: _darkYellow),
                        ),
                      ],
                    ),
                    const SizedBox(width: 6),
                  ],

                  Icon(
                    Icons.keyboard_arrow_down_rounded,
                    color: _darkYellow,
                    size: 20,
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBotAvatar() {
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0.8, end: 1.0),
      duration: const Duration(milliseconds: 800),
      curve: Curves.easeInOutBack,
      builder: (context, double scale, child) {
        return Transform.scale(
          scale: scale,
          child: Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [_lightYellow, _darkYellow],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: _darkYellow.withOpacity(0.3),
                  blurRadius: 8,
                  offset: const Offset(0, 3),
                  spreadRadius: 1,
                ),
              ],
            ),
            child: const Icon(
              Icons.auto_awesome_rounded,
              color: Colors.white,
              size: 20,
            ),
          ),
        );
      },
    );
  }

  Widget _buildUserAvatar() {
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0.8, end: 1.0),
      duration: const Duration(milliseconds: 800),
      curve: Curves.easeInOutBack,
      builder: (context, double scale, child) {
        return Transform.scale(
          scale: scale,
          child: Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [_primaryBlue, _hoverBlue],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: _primaryBlue.withOpacity(0.3),
                  blurRadius: 8,
                  offset: const Offset(0, 3),
                  spreadRadius: 1,
                ),
              ],
            ),
            child: Icon(Icons.person_rounded, color: _lightYellow, size: 20),
          ),
        );
      },
    );
  }

// Bulles de messages avec animations - UNE SEULE FONCTION POUR TOUT
Widget _buildMessageBubble(ChatMessage msg, bool isUser) {
  // Si c'est une image, on l'affiche avec un bouton de téléchargement intégré
  if (msg.imageBytes != null || msg.imageUrl != null) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.6,
        ),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Stack(
              children: [
                // Image cliquable pour agrandir
                GestureDetector(
                  onTap: () => _showFullScreenImage(msg),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: msg.imageBytes != null
                        ? Image.memory(
                            msg.imageBytes!,
                            fit: BoxFit.contain,
                            errorBuilder: (context, error, stackTrace) {
                              return Container(
                                height: 250,
                                color: Colors.grey[200],
                                child: const Center(
                                  child: Icon(
                                    Icons.broken_image,
                                    color: Colors.grey,
                                    size: 50,
                                  ),
                                ),
                              );
                            },
                          )
                        : Image.network(
                            msg.imageUrl!,
                            fit: BoxFit.contain,
                            loadingBuilder: (context, child, loadingProgress) {
                              if (loadingProgress == null) return child;
                              return Container(
                                height: 250,
                                color: Colors.grey[200],
                                child: Center(
                                  child: CircularProgressIndicator(
                                    value:
                                        loadingProgress.expectedTotalBytes != null
                                            ? loadingProgress.cumulativeBytesLoaded /
                                                loadingProgress.expectedTotalBytes!
                                            : null,
                                  ),
                                ),
                              );
                            },
                            errorBuilder: (context, error, stackTrace) {
                              return Container(
                                height: 250,
                                color: Colors.grey[200],
                                child: const Center(
                                  child: Icon(Icons.error, color: Colors.red),
                                ),
                              );
                            },
                          ),
                  ),
                ),
                
                // Overlay avec boutons d'action
                Positioned(
                  top: 12,
                  right: 12,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Bouton Agrandir
                      Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: () => _showFullScreenImage(msg),
                          borderRadius: BorderRadius.circular(30),
                          child: Container(
                            padding: const EdgeInsets.all(8),
                            margin: const EdgeInsets.only(right: 8),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.9),
                              borderRadius: BorderRadius.circular(30),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.1),
                                  blurRadius: 8,
                                  offset: const Offset(0, 2),
                                ),
                              ],
                            ),
                            child: const Icon(
                              Icons.fullscreen_rounded,
                              color: _primaryBlue,
                              size: 18,
                            ),
                          ),
                        ),
                      ),
                      
                      // Bouton Télécharger
                      Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: _isDownloadingGraph
                              ? null
                              : () => _downloadGraph(msg),
                          borderRadius: BorderRadius.circular(30),
                          child: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.9),
                              borderRadius: BorderRadius.circular(30),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.1),
                                  blurRadius: 8,
                                  offset: const Offset(0, 2),
                                ),
                              ],
                            ),
                            child: _isDownloadingGraph
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      valueColor: AlwaysStoppedAnimation<Color>(_primaryBlue),
                                    ),
                                  )
                                : const Icon(
                                    Icons.download_rounded,
                                    color: _primaryBlue,
                                    size: 18,
                                  ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                
                // Badge "Graphique" en bas à gauche
                Positioned(
                  bottom: 12,
                  left: 12,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 5,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.6),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.bar_chart_rounded,
                          color: Colors.white,
                          size: 12,
                        ),
                        SizedBox(width: 4),
                        Text(
                          "Graphique",
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            
            // Informations supplémentaires en bas
            Padding(
              padding: const EdgeInsets.only(top: 8, right: 4),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    _formatTime(msg.timestamp),
                    style: TextStyle(
                      fontSize: 10,
                      color: _textSecondary.withOpacity(0.7),
                    ),
                  ),
                  Text(
                    "PNG • ${msg.imageBytes != null ? (msg.imageBytes!.length / 1024).toStringAsFixed(0) : '?'} KB",
                    style: TextStyle(
                      fontSize: 10,
                      color: _darkYellow,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Pour les messages texte, on garde la bulle normale
  return TweenAnimationBuilder<double>(
    tween: Tween<double>(begin: 0.0, end: 1.0),
    duration: Duration(milliseconds: isUser ? 300 : 500),
    curve: Curves.easeOutQuart,
    builder: (context, double opacity, child) {
      return Transform.scale(
        scale: 0.8 + (0.2 * opacity),
        child: Opacity(
          opacity: opacity,
          child: Container(
            decoration: BoxDecoration(
              color: isUser ? _primaryBlue : _white,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(20),
                topRight: const Radius.circular(20),
                bottomLeft: Radius.circular(isUser ? 20 : 4),
                bottomRight: Radius.circular(isUser ? 4 : 20),
              ),
              boxShadow: [
                BoxShadow(
                  color: (isUser ? _primaryBlue : _darkYellow).withOpacity(0.1),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                  spreadRadius: opacity * 2,
                ),
              ],
              border: !isUser
                  ? Border.all(color: _lightYellow.withOpacity(0.3))
                  : null,
            ),
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (!isUser)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [_lightYellow, _darkYellow],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(
                                Icons.auto_awesome_rounded,
                                size: 10,
                                color: Colors.white,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                "Agent IA",
                                style: TextStyle(
                                  fontSize: 9,
                                  color: _white,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),

                // Afficher le texte
                _buildMessageText(msg.text, isUser),

                // Afficher les boutons candidats
                if (!isUser && msg.candidates.isNotEmpty)
                  _buildCandidateButtons(msg),

                const SizedBox(height: 8),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.access_time_rounded,
                      size: 10,
                      color: isUser
                          ? _lightYellow.withOpacity(0.7)
                          : _textSecondary.withOpacity(0.5),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      _formatTime(msg.timestamp),
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w400,
                        color: isUser
                            ? _lightYellow.withOpacity(0.7)
                            : _textSecondary.withOpacity(0.5),
                      ),
                    ),
                    if (!isUser) ...[
                      const SizedBox(width: 12),
                      Icon(
                        Icons.check_circle_rounded,
                        size: 10,
                        color: _darkYellow,
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ),
      );
    },
  );
}

// Nouvelle fonction pour afficher l'image en plein écran
void _showFullScreenImage(ChatMessage msg) {
  showDialog(
    context: context,
    builder: (BuildContext context) {
      return Dialog(
        backgroundColor: Colors.transparent,
        insetPadding: const EdgeInsets.all(20),
        child: Stack(
          children: [
            // Image en plein écran
            Container(
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.5),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: InteractiveViewer(
                  panEnabled: true,
                  minScale: 0.5,
                  maxScale: 4.0,
                  child: msg.imageBytes != null
                      ? Image.memory(
                          msg.imageBytes!,
                          fit: BoxFit.contain,
                          errorBuilder: (context, error, stackTrace) {
                            return Container(
                              height: 400,
                              color: Colors.grey[900],
                              child: const Center(
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      Icons.broken_image,
                                      color: Colors.white,
                                      size: 50,
                                    ),
                                    SizedBox(height: 10),
                                    Text(
                                      "Impossible de charger l'image",
                                      style: TextStyle(color: Colors.white),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        )
                      : Image.network(
                          msg.imageUrl!,
                          fit: BoxFit.contain,
                          loadingBuilder: (context, child, loadingProgress) {
                            if (loadingProgress == null) return child;
                            return Container(
                              height: 400,
                              color: Colors.grey[900],
                              child: Center(
                                child: CircularProgressIndicator(
                                  valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
                                  value: loadingProgress.expectedTotalBytes != null
                                      ? loadingProgress.cumulativeBytesLoaded /
                                          loadingProgress.expectedTotalBytes!
                                      : null,
                                ),
                              ),
                            );
                          },
                          errorBuilder: (context, error, stackTrace) {
                            return Container(
                              height: 400,
                              color: Colors.grey[900],
                              child: const Center(
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.error, color: Colors.white, size: 50),
                                    SizedBox(height: 10),
                                    Text(
                                      "Erreur de chargement",
                                      style: TextStyle(color: Colors.white),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                ),
              ),
            ),
            
            // Bouton de fermeture
            Positioned(
              top: 10,
              right: 10,
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: () => Navigator.pop(context),
                  borderRadius: BorderRadius.circular(30),
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(
                        color: Colors.white.withOpacity(0.3),
                        width: 1,
                      ),
                    ),
                    child: const Icon(
                      Icons.close_rounded,
                      color: Colors.white,
                      size: 24,
                    ),
                  ),
                ),
              ),
            ),
            
            // Bouton de téléchargement en bas
            Positioned(
              bottom: 20,
              right: 20,
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: _isDownloadingGraph
                      ? null
                      : () {
                          Navigator.pop(context);
                          _downloadGraph(msg);
                        },
                  borderRadius: BorderRadius.circular(30),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 10,
                    ),
                    decoration: BoxDecoration(
                      color: _primaryBlue,
                      borderRadius: BorderRadius.circular(30),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.3),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.download_rounded,
                          color: Colors.white,
                          size: 18,
                        ),
                        const SizedBox(width: 8),
                        const Text(
                          "Télécharger",
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            
            // Informations en haut à gauche
            Positioned(
              top: 20,
              left: 20,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: Colors.white.withOpacity(0.2),
                    width: 1,
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.auto_awesome_rounded,
                      color: _lightYellow,
                      size: 14,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      "Graphique - ${_formatTime(msg.timestamp)}",
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // Indication de zoom
            Positioned(
              bottom: 20,
              left: 20,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Row(
                  children: [
                    Icon(
                      Icons.zoom_in_rounded,
                      color: Colors.white,
                      size: 14,
                    ),
                    SizedBox(width: 4),
                    Text(
                      "Pinch pour zoomer",
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    },
  );
}

  Widget _buildEmptyState() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(height: 24),
            const Text(
              "Bienvenue !",
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w700,
                color: _textPrimary,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              "Comment puis-je vous aider ?",
              style: TextStyle(fontSize: 15, color: _textSecondary),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildSuggestionItem({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => _sendMessage(messageOverride: title),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: _lightYellow.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: _darkYellow, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        color: _textPrimary,
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: TextStyle(color: _textSecondary, fontSize: 12),
                    ),
                  ],
                ),
              ),
              Icon(Icons.arrow_forward_rounded, color: _darkYellow, size: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChatHistoryItem(Conversation conversation, bool isActive) {
    final preview = conversation.messages.isNotEmpty
        ? conversation.messages.last.text
        : "Conversation vide";
    final dateText = _formatDate(conversation.createdAt);

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      decoration: BoxDecoration(
        color: isActive ? _primaryBlue.withOpacity(0.03) : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isActive ? _primaryBlue.withOpacity(0.1) : Colors.transparent,
          width: 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            setState(() {
              _activeConversation = conversation;
            });
          },
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(10),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: _primaryBlue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.chat_rounded,
                    size: 16,
                    color: _primaryBlue,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        conversation.title,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: _textPrimary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        preview,
                        style: TextStyle(fontSize: 11, color: _textSecondary),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        dateText,
                        style: TextStyle(
                          fontSize: 9,
                          color: _darkYellow,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => _confirmDeleteConversation(conversation),
                  icon: const Icon(
                    Icons.delete_outline_rounded,
                    size: 18,
                    color: _textSecondary,
                  ),
                  tooltip: "Supprimer",
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  List<String> _extractFileNames(Conversation conversation) {
    final files = <String>{};
    final filesRegex = RegExp(r'https?:\/\/[^\s]+\/files\/([^\s]+)');
    final statsRegex = RegExp(r'https?:\/\/[^\s]+\/statistics\/([^\s]+)');

    for (final msg in conversation.messages) {
      final text = msg.text.trim();
      if (text.isEmpty) continue;
      for (final match in filesRegex.allMatches(text)) {
        final name = match.group(1);
        if (name != null && name.isNotEmpty) {
          files.add('files/$name');
        }
      }
      for (final match in statsRegex.allMatches(text)) {
        final name = match.group(1);
        if (name != null && name.isNotEmpty) {
          files.add('statistics/$name');
        }
      }
    }

    return files.toList();
  }

  Future<void> _deleteConversationFiles(Conversation conversation) async {
    final files = _extractFileNames(conversation);
    if (files.isEmpty) return;
    try {
      await ChatApiService.deleteFiles(files);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Erreur suppression fichiers: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _confirmDeleteConversation(
    Conversation conversation, {
    VoidCallback? onDeleted,
  }) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text(
          "Supprimer la conversation",
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
        content: const Text(
          "Cette action est irreversible. Voulez-vous continuer ?",
          style: TextStyle(fontSize: 13),
        ),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Annuler"),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              setState(() {
                _conversations.remove(conversation);
                if (_activeConversation == conversation) {
                  _activeConversation =
                      _conversations.isNotEmpty ? _conversations.first : null;
                }
              });
              onDeleted?.call();
              _saveConversations();
              await _deleteConversationFiles(conversation);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: const Text("Supprimer"),
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _white,
        border: Border(top: BorderSide(color: _borderLight, width: 1)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: _surfaceLight,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: _focusNode.hasFocus ? _lightYellow : _borderLight,
                  width: _focusNode.hasFocus ? 1.5 : 1,
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      focusNode: _focusNode,
                      decoration: InputDecoration(
                        hintText: "Votre message...",
                        hintStyle: TextStyle(
                          color: _textSecondary.withOpacity(0.5),
                          fontSize: 14,
                        ),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(
                          vertical: 12,
                        ),
                      ),
                      style: const TextStyle(fontSize: 14, color: _textPrimary),
                      maxLines: 4,
                      minLines: 1,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  IconButton(
                    onPressed: () {},
                    icon: Icon(
                      Icons.attach_file_rounded,
                      color: _darkYellow.withOpacity(0.5),
                      size: 20,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: _isComposing
                    ? [_lightYellow, _darkYellow]
                    : [_borderLight, _borderLight],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                if (_isComposing)
                  BoxShadow(
                    color: _darkYellow.withOpacity(0.2),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
              ],
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: _isComposing ? _sendMessage : null,
                borderRadius: BorderRadius.circular(12),
                child: Icon(
                  Icons.send_rounded,
                  color: _isComposing
                      ? _white
                      : _textSecondary.withOpacity(0.3),
                  size: 18,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showInfoDialog() {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: _white,
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(
                color: _primaryBlue.withOpacity(0.1),
                blurRadius: 20,
                offset: const Offset(0, 5),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 200,
                height: 100,
                margin: const EdgeInsets.only(bottom: 8),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: Image.asset(
                    'assets/images/ise_logo.png',
                    fit: BoxFit.contain,
                    errorBuilder: (context, error, stackTrace) {
                      return Container(
                        width: 100,
                        height: 100,
                        color: _primaryBlue,
                        child: const Icon(
                          Icons.school_rounded,
                          color: Colors.white,
                          size: 50,
                        ),
                      );
                    },
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                "Agent IA",
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  color: _textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                height: 3,
                width: 60,
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [_lightYellow, _darkYellow]),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  color: _lightYellow.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Text(
                  "Bienvenue sur l'agent du Collège & Lycée ISE",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 14,
                    color: _textPrimary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                "Je suis là pour vous aider avec :",
                style: TextStyle(fontSize: 14, color: _textSecondary),
              ),
              const SizedBox(height: 12),
              _buildInfoRow("Génération de documents"),
              const SizedBox(height: 8),
              _buildInfoRow("Analyse graphique"),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _primaryBlue,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    elevation: 0,
                  ),
                  child: const Text(
                    "Commencer",
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.check_circle_rounded, color: _darkYellow, size: 18),
        const SizedBox(width: 8),
        Text(text, style: const TextStyle(fontSize: 14, color: _textSecondary)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final screenSize = MediaQuery.of(context).size;
    final isMobile = screenSize.width < 600;

    return Scaffold(
      backgroundColor: _surfaceLight,
      // Utilisation de la nouvelle navbar
      appBar: PreferredSize(
        preferredSize: Size.fromHeight(isMobile ? 70 : 90),
        child: _buildNavbar(),
      ),
      body: Row(
        children: [
          // Barre latérale d'historique - responsive
          if (_sidebarVisible && (!isMobile || screenSize.width > 600))
            Container(
              width: isMobile ? screenSize.width * 0.8 : 280,
              decoration: BoxDecoration(
                color: _white,
                border: Border(
                  right: BorderSide(color: _borderLight, width: 1),
                ),
              ),
              child: Column(
                children: [
                  // En-tête de la barre latérale
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      border: Border(
                        bottom: BorderSide(color: _borderLight, width: 1),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Bouton Nouvelle conversation
                        Container(
                          width: double.infinity,
                          height: 44,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [_primaryBlue, _hoverBlue],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(12),
                            boxShadow: [
                              BoxShadow(
                                color: _primaryBlue.withOpacity(0.15),
                                blurRadius: 8,
                                offset: const Offset(0, 3),
                              ),
                            ],
                          ),
                          child: ElevatedButton(
                            onPressed: _startNewChat,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.transparent,
                              foregroundColor: Colors.white,
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.add_rounded, size: 18),
                                const SizedBox(width: 6),
                                const Text(
                                  "Nouvelle conversation",
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              "Historique",
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: _textPrimary,
                              ),
                            ),
                            Row(
                              children: [
                                IconButton(
                                  onPressed: _showHistorySearchDialog,
                                  icon: const Icon(
                                    Icons.search_rounded,
                                    size: 18,
                                    color: _textSecondary,
                                  ),
                                  tooltip: "Rechercher",
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 3,
                                  ),
                                  decoration: BoxDecoration(
                                    color: _lightYellow.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                  child: Text(
                                    "${_conversations.length}",
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w500,
                                      color: _darkYellow,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  // Liste des conversations
                  Expanded(
                    child: ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: _conversations.length,
                      itemBuilder: (context, index) {
                        final conversation = _conversations[index];
                        return _buildChatHistoryItem(
                          conversation,
                          conversation == _activeConversation,
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),

          // Contenu principal (chat)
          Expanded(
            child: Column(
              children: [
                // Welcome Banner
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    color: _white,
                    border: Border(
                      bottom: BorderSide(color: _borderLight, width: 1),
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(
                          color: _lightYellow.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(
                          Icons.info_outline_rounded,
                          color: _darkYellow,
                          size: 18,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          "Agent IA pour documents et analyses",
                          style: TextStyle(color: _textSecondary, fontSize: 13),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),

                // Messages List
                Expanded(
                  child: Container(
                    color: _surfaceLight,
                    child: _activeConversation?.messages.isEmpty ?? true
                        ? _buildEmptyState()
                        : ListView.builder(
                            controller: _scrollController,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 16,
                            ),
                            itemCount:
                                _activeConversation?.messages.length ?? 0,
                            itemBuilder: (context, index) {
                              final msg = _activeConversation!.messages[index];
                              final isUser = msg.sender == "user";
                              final isLastMessage =
                                  index ==
                                  _activeConversation!.messages.length - 1;

                              return Container(
                                margin: EdgeInsets.only(
                                  bottom: isLastMessage ? 16 : 12,
                                ),
                                child: Row(
                                  mainAxisAlignment: isUser
                                      ? MainAxisAlignment.end
                                      : MainAxisAlignment.start,
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    if (!isUser) ...[
                                      _buildBotAvatar(),
                                      const SizedBox(width: 8),
                                    ],
                                    Flexible(
                                      child: Container(
                                        constraints: BoxConstraints(
                                          maxWidth: screenSize.width * 0.6,
                                        ),
                                        // ✅ UTILISATION DE LA FONCTION UNIQUE
                                        child: _buildMessageBubble(msg, isUser),
                                      ),
                                    ),
                                    if (isUser) ...[
                                      const SizedBox(width: 8),
                                      _buildUserAvatar(),
                                    ],
                                  ],
                                ),
                              );
                            },
                          ),
                  ),
                ),

                // Loading indicator
                if (_isLoading)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      vertical: 12,
                      horizontal: 20,
                    ),
                    color: _white,
                    child: Row(
                      children: [
                        Container(
                          width: 32,
                          height: 32,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [_lightYellow, _darkYellow],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(
                            Icons.auto_awesome_rounded,
                            color: Colors.white,
                            size: 16,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "L'agent IA réfléchit...",
                                style: TextStyle(
                                  fontSize: 13,
                                  color: _textPrimary,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                              const SizedBox(height: 4),
                              LinearProgressIndicator(
                                backgroundColor: _borderLight,
                                color: _primaryBlue,
                                borderRadius: BorderRadius.circular(2),
                                minHeight: 4,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),

                // Chat Input
                _buildInputArea(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}




