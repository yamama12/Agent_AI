// user_management_screen.dart
import 'package:flutter/material.dart';
import '../models/user.dart';
import '../services/user_service.dart';
import '../services/auth_service.dart';

class UserManagementScreen extends StatefulWidget {
  const UserManagementScreen({super.key});

  @override
  State<UserManagementScreen> createState() => _UserManagementScreenState();
}

class _UserManagementScreenState extends State<UserManagementScreen> 
    with SingleTickerProviderStateMixin {
  
  late TabController _tabController;
  final UserService _userService = UserService();
  final AuthService _authService = AuthService();
  
  List<User> _users = [];
  List<User> _filteredUsers = [];
  bool _isLoading = true;
  String _searchQuery = '';
  final TextEditingController _searchController = TextEditingController();
  
  // Pagination
  int _currentPage = 0;
  final int _itemsPerPage = 20;
  bool _hasMoreData = true;

  // Couleurs cohérentes avec ChatScreen
  static const Color _primaryBlue = Color(0xFF0F2447);
  static const Color _lightYellow = Color(0xFFF8D17A);
  static const Color _darkYellow = Color(0xFFC69450);
  static const Color _backgroundLight = Color(0xFFF5F7FB);
  static const Color _white = Color(0xFFFFFFFF);
  static const Color _borderLight = Color(0xFFE8ECF2);
  static const Color _textPrimary = Color(0xFF1A2B3C);
  static const Color _textSecondary = Color(0xFF64748B);
  static const Color _successGreen = Color(0xFF2E7D32);
  static const Color _warningOrange = Color(0xFFED6C02);
  static const Color _errorRed = Color(0xFFD32F2F);

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this); // Tous, Super Admin, Admin, User
    _loadUsers();
    _searchController.addListener(_onSearchChanged);
  }

  void _onSearchChanged() {
    setState(() {
      _searchQuery = _searchController.text.toLowerCase();
      _filterUsers();
    });
  }

  void _filterUsers() {
    if (_searchQuery.isEmpty) {
      _filteredUsers = List.from(_users);
    } else {
      _filteredUsers = _users.where((user) {
        return user.email.toLowerCase().contains(_searchQuery) ||
               user.id.toString().contains(_searchQuery) ||
               user.displayRole.toLowerCase().contains(_searchQuery);
      }).toList();
    }
  }

  Future<void> _loadUsers() async {
    setState(() => _isLoading = true);
    try {
      final users = await _userService.getAllUsers();
      setState(() {
        _users = users;
        _filteredUsers = users;
      });
    } catch (e) {
      _showSnackBar('Erreur: $e', isError: true);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showSnackBar(String message, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? _errorRed : _successGreen,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        duration: const Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _backgroundLight,
      appBar: AppBar(
        backgroundColor: _white,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_rounded, color: _primaryBlue),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Gestion des utilisateurs',
          style: TextStyle(
            color: _textPrimary,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
        bottom: TabBar(
          controller: _tabController,
          labelColor: _primaryBlue,
          unselectedLabelColor: _textSecondary,
          indicatorColor: _darkYellow,
          indicatorWeight: 3,
          isScrollable: true,
          tabs: const [
            Tab(text: 'Tous', icon: Icon(Icons.people_rounded)),
            Tab(text: 'Super Admin', icon: Icon(Icons.admin_panel_settings_rounded)),
            Tab(text: 'Admin', icon: Icon(Icons.shield_rounded)),
          ],
        ),
        actions: [
          // Bouton d'ajout
          Container(
            margin: const EdgeInsets.only(right: 16),
            child: ElevatedButton.icon(
              onPressed: _showAddUserDialog,
              icon: const Icon(Icons.add_rounded, size: 20),
              label: const Text('Ajouter un utilisateur'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _primaryBlue,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Barre de recherche et filtres
          Container(
            padding: const EdgeInsets.all(16),
            color: _white,
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: 'Rechercher par email ou ID...',
                    prefixIcon: Icon(Icons.search_rounded, color: _textSecondary),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: _borderLight),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: _borderLight),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: _darkYellow, width: 2),
                    ),
                    contentPadding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
                const SizedBox(height: 12),
                // Statistiques rapides
                Row(
                  children: [
                    _buildStatCard(
                      'Total',
                      _users.length.toString(),
                      Icons.people_rounded,
                      _primaryBlue,
                    ),
                    const SizedBox(width: 8),
                    _buildStatCard(
                      'Super Admin',
                      _users.where((u) => u.isSuperAdmin).length.toString(),
                      Icons.admin_panel_settings_rounded,
                      _darkYellow,
                    ),
                    const SizedBox(width: 8),
                    _buildStatCard(
                      'Admin',
                      _users.where((u) => u.isAdmin && !u.isSuperAdmin).length.toString(),
                      Icons.shield_rounded,
                      _warningOrange,
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Liste des utilisateurs
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredUsers.isEmpty
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        onRefresh: _loadUsers,
                        color: _primaryBlue,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _filteredUsers.length,
                          itemBuilder: (context, index) {
                            final user = _filteredUsers[index];
                            
                            // Filtrer par onglet
                            if (_tabController.index == 1 && !user.isSuperAdmin) 
                              return const SizedBox.shrink();
                            if (_tabController.index == 2 && (!user.isAdmin || user.isSuperAdmin)) 
                              return const SizedBox.shrink();
                            if (_tabController.index == 3 && (user.isAdmin || user.isSuperAdmin)) 
                              return const SizedBox.shrink();
                            
                            return _buildUserCard(user);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 6),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 16),
            const SizedBox(height: 4),
            Text(
              value,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              label,
              style: TextStyle(fontSize: 9, color: _textSecondary),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildUserCard(User user) {
    final isSuperAdmin = user.isSuperAdmin;
    final isAdmin = user.isAdmin;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: _white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _borderLight),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => _showUserDetails(user),
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                // Avatar avec initiales de l'email
                Container(
                  width: 50,
                  height: 50,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: isSuperAdmin
                          ? [_lightYellow, _darkYellow]
                          : isAdmin
                              ? [_primaryBlue, _primaryBlue.withOpacity(0.8)]
                              : [Colors.grey.shade400, Colors.grey.shade600],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Center(
                    child: Text(
                      user.email.isNotEmpty ? user.email[0].toUpperCase() : '?',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                
                // Infos utilisateur
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              user.email,
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: _textPrimary,
                              ),
                            ),
                          ),
                          if (user.changepassword)
                            Container(
                              margin: const EdgeInsets.only(left: 8),
                              padding: const EdgeInsets.all(4),
                              decoration: BoxDecoration(
                                color: _warningOrange.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Icon(
                                Icons.lock_reset_rounded,
                                size: 14,
                                color: _warningOrange,
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Text(
                            'ID: ${user.id}',
                            style: TextStyle(
                              fontSize: 12,
                              color: _textSecondary,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Text(
                            'Personne: ${user.idpersonne}',
                            style: TextStyle(
                              fontSize: 12,
                              color: _textSecondary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: user.roleColor.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              user.displayRole,
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w500,
                                color: user.roleColor,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          if (user.token != null)
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 3,
                              ),
                              decoration: BoxDecoration(
                                color: _successGreen.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.check_circle_rounded,
                                    size: 10,
                                    color: _successGreen,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    'Connecté',
                                    style: TextStyle(
                                      fontSize: 10,
                                      color: _successGreen,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),
                ),
                
                // Menu d'actions
                PopupMenuButton<String>(
                  icon: Icon(Icons.more_vert_rounded, color: _textSecondary),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  onSelected: (value) => _handleUserAction(value, user),
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'edit',
                      child: Row(
                        children: [
                          Icon(Icons.edit_rounded, size: 18),
                          SizedBox(width: 8),
                          Text('Modifier'),
                        ],
                      ),
                    ),
                    if (isSuperAdmin)
                      const PopupMenuItem(
                        value: 'demote_super',
                        child: Row(
                          children: [
                            Icon(Icons.admin_panel_settings_rounded, size: 18),
                            SizedBox(width: 8),
                            Text('Rétrograder Super Admin'),
                          ],
                        ),
                      )
                    else if (isAdmin)
                      const PopupMenuItem(
                        value: 'promote_super',
                        child: Row(
                          children: [
                            Icon(Icons.star_rounded, size: 18),
                            SizedBox(width: 8),
                            Text('Promouvoir Super Admin'),
                          ],
                        ),
                      )
                    else
                      const PopupMenuItem(
                        value: 'promote_admin',
                        child: Row(
                          children: [
                            Icon(Icons.shield_rounded, size: 18),
                            SizedBox(width: 8),
                            Text('Promouvoir Admin'),
                          ],
                        ),
                      ),
                    const PopupMenuItem(
                      value: 'force_password',
                      child: Row(
                        children: [
                          Icon(Icons.lock_reset_rounded, size: 18),
                          SizedBox(width: 8),
                          Text('Forcer changement MDP'),
                        ],
                      ),
                    ),
                    const PopupMenuDivider(),
                    const PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete_rounded, size: 18, color: Colors.red),
                          SizedBox(width: 8),
                          Text('Supprimer', style: TextStyle(color: Colors.red)),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.people_outline_rounded,
            size: 80,
            color: _textSecondary.withOpacity(0.3),
          ),
          const SizedBox(height: 16),
          Text(
            'Aucun utilisateur trouvé',
            style: TextStyle(
              fontSize: 16,
              color: _textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Commencez par ajouter un utilisateur',
            style: TextStyle(fontSize: 13, color: _textSecondary.withOpacity(0.7)),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  void _showAddUserDialog() {
    final firstNameController = TextEditingController();
    final lastNameController = TextEditingController();
    final phoneController = TextEditingController();
    final cinController = TextEditingController();
    final emailController = TextEditingController();
    final passwordController = TextEditingController();
    final confirmPasswordController = TextEditingController();
    String selectedRole = 'ROLE_ADMIN';
    int stepIndex = 0;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Ajouter un utilisateur'),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildStepChip(stepIndex == 0, '1/2'),
                ],
              ),
            ],
          ),
          content: SingleChildScrollView(
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 200),
              child: stepIndex == 0
                  ? Column(
                      key: const ValueKey('step1'),
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        TextField(
                          controller: lastNameController,
                          decoration: const InputDecoration(
                            labelText: 'Nom',
                            prefixIcon: Icon(Icons.person_rounded ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: firstNameController,
                          decoration: const InputDecoration(
                            labelText: 'Prénom',
                            prefixIcon: Icon(Icons.person_rounded),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: phoneController,
                          keyboardType: TextInputType.phone,
                          decoration: const InputDecoration(
                            labelText: 'Téléphone',
                            prefixIcon: Icon(Icons.phone_rounded),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: cinController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            labelText: 'CIN',
                            prefixIcon: Icon(Icons.credit_card_rounded),
                          ),
                        ),
                      ],
                    )
                  : Column(
                      key: const ValueKey('step2'),
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        TextField(
                          controller: emailController,
                          decoration: const InputDecoration(
                            labelText: 'Email',
                            prefixIcon: Icon(Icons.email_rounded),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: passwordController,
                          obscureText: true,
                          decoration: const InputDecoration(
                            labelText: 'Mot de passe',
                            prefixIcon: Icon(Icons.lock_rounded),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: confirmPasswordController,
                          obscureText: true,
                          decoration: const InputDecoration(
                            labelText: 'Confirmer le mot de passe',
                            prefixIcon: Icon(Icons.lock_outline_rounded),
                          ),
                        ),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<String>(
                          value: selectedRole,
                          decoration: const InputDecoration(
                            labelText: 'Rôle',
                            prefixIcon: Icon(Icons.admin_panel_settings_rounded),
                          ),
                          items: const [
                            DropdownMenuItem(value: 'ROLE_ADMIN', child: Text('Admin')),
                            DropdownMenuItem(value: 'ROLE_SUPER_ADMIN', child: Text('Super Admin')),
                          ],
                          onChanged: (value) => selectedRole = value ?? 'Choisir un rôle',
                        ),
                      ],
                    ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Annuler'),
            ),
            if (stepIndex == 1)
              TextButton(
                onPressed: () => setDialogState(() => stepIndex = 0),
                child: const Text('Retour'),
              ),
            ElevatedButton(
              onPressed: () async {
                if (stepIndex == 0) {
                  if (lastNameController.text.trim().isEmpty ||
                      firstNameController.text.trim().isEmpty ||
                      phoneController.text.trim().isEmpty ||
                      cinController.text.trim().isEmpty) {
                    _showSnackBar('Veuillez remplir tous les champs', isError: true);
                    return;
                  }
                  setDialogState(() => stepIndex = 1);
                  return;
                }

                try {
                  if (emailController.text.trim().isEmpty ||
                      passwordController.text.isEmpty ||
                      confirmPasswordController.text.isEmpty) {
                    _showSnackBar('Veuillez remplir tous les champs', isError: true);
                    return;
                  }
                  if (passwordController.text != confirmPasswordController.text) {
                    _showSnackBar('Les mots de passe ne correspondent pas', isError: true);
                    return;
                  }

                  final idpersonne = int.tryParse(cinController.text.trim());
                  if (idpersonne == null) {
                    _showSnackBar('CIN invalide', isError: true);
                    return;
                  }

                  await _userService.createUser(
                    email: emailController.text.trim(),
                    password: passwordController.text,
                    idpersonne: idpersonne,
                    roles: [selectedRole],
                  );

                  Navigator.pop(context);
                  _loadUsers();
                  _showSnackBar('Utilisateur ajout? avec succ?s');
                } catch (e) {
                  _showSnackBar('Erreur: $e', isError: true);
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: _primaryBlue,
                foregroundColor: Colors.white,
              ),
              child: Text(stepIndex == 0 ? 'Suivant' : 'Ajouter'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStepChip(bool isActive, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: isActive ? _primaryBlue.withOpacity(0.1) : _borderLight,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isActive ? _primaryBlue : _borderLight,
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: isActive ? _primaryBlue : _textSecondary,
        ),
      ),
    );
  }

  void _showUserDetails(User user) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.5,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) {
          return Container(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: _borderLight,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Container(
                      width: 60,
                      height: 60,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: user.isSuperAdmin
                              ? [_lightYellow, _darkYellow]
                              : user.isAdmin
                                  ? [_primaryBlue, _primaryBlue.withOpacity(0.8)]
                                  : [Colors.grey.shade400, Colors.grey.shade600],
                        ),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Center(
                        child: Text(
                          user.email[0].toUpperCase(),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            user.email,
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            'ID: ${user.id}',
                            style: TextStyle(color: _textSecondary),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                const Text(
                  'Informations détaillées',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 12),
                _buildInfoRow('ID Personne', user.idpersonne.toString()),
                _buildInfoRow('Rôle', user.displayRole),
                _buildInfoRow('Statut', user.token != null ? 'Connecté' : 'Déconnecté'),
                _buildInfoRow('Changement MDP requis', user.changepassword ? 'Oui' : 'Non'),
                if (user.token != null) _buildInfoRow('Token', '${user.token!.substring(0, 20)}...'),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 150,
            child: Text(
              label,
              style: TextStyle(color: _textSecondary, fontSize: 13),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  void _handleUserAction(String action, User user) {
    switch (action) {
      case 'edit':
        _showEditUserDialog(user);
        break;
      case 'promote_admin':
        _changeUserRole(user, ['ROLE_ADMIN']);
        break;
      case 'promote_super':
        _changeUserRole(user, ['ROLE_SUPER_ADMIN']);
        break;
      case 'demote_super':
        _changeUserRole(user, ['ROLE_ADMIN']);
        break;
      case 'force_password':
        _forcePasswordChange(user);
        break;
      case 'delete':
        _confirmDeleteUser(user);
        break;
    }
  }

  void _changeUserRole(User user, List<String> newRoles) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Changer le rôle'),
        content: Text('Voulez-vous changer le rôle de ${user.email} ?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              try {
                await _userService.changeUserRole(user.id, newRoles);
                _loadUsers();
                _showSnackBar('Rôle modifié avec succès');
              } catch (e) {
                _showSnackBar('Erreur: $e', isError: true);
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: _primaryBlue,
              foregroundColor: Colors.white,
            ),
            child: const Text('Confirmer'),
          ),
        ],
      ),
    );
  }

  void _forcePasswordChange(User user) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Forcer changement de mot de passe'),
        content: Text('Voulez-vous forcer ${user.email} à changer son mot de passe ?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              try {
                await _userService.forcePasswordChange(user.id, force: true);
                _loadUsers();
                _showSnackBar('Changement de mot de passe forcé');
              } catch (e) {
                _showSnackBar('Erreur: $e', isError: true);
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: _warningOrange,
              foregroundColor: Colors.white,
            ),
            child: const Text('Forcer'),
          ),
        ],
      ),
    );
  }

  void _showEditUserDialog(User user) {
    final emailController = TextEditingController(text: user.email);
    final idpersonneController = TextEditingController(text: user.idpersonne.toString());
    String selectedRole = user.roles.isNotEmpty ? user.roles.first : 'ROLE_ADMIN';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Modifier utilisateur'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: emailController,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  prefixIcon: Icon(Icons.email_rounded),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: idpersonneController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'ID Personne',
                  prefixIcon: Icon(Icons.person_rounded),
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedRole,
                decoration: const InputDecoration(
                  labelText: 'Rôle',
                  prefixIcon: Icon(Icons.admin_panel_settings_rounded),
                ),
                items: const [
                  DropdownMenuItem(value: 'ROLE_ADMIN', child: Text('Admin')),
                  DropdownMenuItem(value: 'ROLE_SUPER_ADMIN', child: Text('Super Admin')),
                ],
                onChanged: (value) => selectedRole = value!,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            onPressed: () async {
              try {
                final idpersonne = int.tryParse(idpersonneController.text);
                if (idpersonne == null) {
                  _showSnackBar('ID Personne invalide', isError: true);
                  return;
                }

                await _userService.updateUser(
                  id: user.id,
                  email: emailController.text,
                  idpersonne: idpersonne,
                  roles: [selectedRole],
                );
                
                Navigator.pop(context);
                _loadUsers();
                _showSnackBar('Utilisateur modifié avec succès');
              } catch (e) {
                _showSnackBar('Erreur: $e', isError: true);
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: _primaryBlue,
              foregroundColor: Colors.white,
            ),
            child: const Text('Modifier'),
          ),
        ],
      ),
    );
  }

  void _confirmDeleteUser(User user) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmer la suppression'),
        content: Text('Supprimer définitivement ${user.email} ?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              try {
                await _userService.deleteUser(user.id);
                _loadUsers();
                _showSnackBar('${user.email} a été supprimé');
              } catch (e) {
                _showSnackBar('Erreur: $e', isError: true);
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: _errorRed),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }
} 