
import 'package:flutter/material.dart';
import '../models/user.dart';
import '../services/user_service.dart';
import '../services/auth_service.dart';

class UserManagementScreen extends StatefulWidget {
  const UserManagementScreen({super.key});

  @override
  State<UserManagementScreen> createState() => _UserManagementScreenState();
}

class _UserManagementScreenState extends State<UserManagementScreen> with TickerProviderStateMixin {
  final UserService _userService = UserService();
  final AuthService _authService = AuthService();
  
  List<User> _users = [];
  List<User> _filteredUsers = [];
  bool _isLoading = true;
  String _searchQuery = '';
  final TextEditingController _searchController = TextEditingController();
  late TabController _tabController;

  // Couleurs
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
    // Initialiser le TabController APRÈS super.initState()
    _tabController = TabController(length: 3, vsync: this); // Correction: seulement 3 onglets
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
            user.displayRole.toLowerCase().contains(_searchQuery) ||
            (user.nom?.toLowerCase() ?? '').contains(_searchQuery) ||
            (user.prenom?.toLowerCase() ?? '').contains(_searchQuery) ||
            (user.telephone?.toLowerCase() ?? '').contains(_searchQuery) ||
            (user.cin?.toLowerCase() ?? '').contains(_searchQuery) ||
            (user.emailPersonne?.toLowerCase() ?? '').contains(_searchQuery);
      }).toList();
    }
    
    // Filtrer par onglet sélectionné
    _filterByTab();
  }

  void _filterByTab() {
    final int tabIndex = _tabController.index;
    setState(() {
      if (tabIndex == 0) {
        // Tous
        _filteredUsers = _users.where((u) => 
          _searchQuery.isEmpty || 
          u.email.toLowerCase().contains(_searchQuery) ||
          (u.nom?.toLowerCase() ?? '').contains(_searchQuery) ||
          (u.emailPersonne?.toLowerCase() ?? '').contains(_searchQuery)
        ).toList();
      } else if (tabIndex == 1) {
        // Super Admin
        _filteredUsers = _users.where((u) => 
          u.isSuperAdmin && (_searchQuery.isEmpty || 
          u.email.toLowerCase().contains(_searchQuery) ||
          (u.nom?.toLowerCase() ?? '').contains(_searchQuery) ||
          (u.emailPersonne?.toLowerCase() ?? '').contains(_searchQuery))
        ).toList();
      } else if (tabIndex == 2) {
        // Admin
        _filteredUsers = _users.where((u) => 
          u.isAdmin && !u.isSuperAdmin && (_searchQuery.isEmpty || 
          u.email.toLowerCase().contains(_searchQuery) ||
          (u.nom?.toLowerCase() ?? '').contains(_searchQuery) ||
          (u.emailPersonne?.toLowerCase() ?? '').contains(_searchQuery))
        ).toList();
      }
    });
  }

  Future<void> _loadUsers() async {
    setState(() => _isLoading = true);
    try {
      final users = await _userService.getAdmins();
      setState(() {
        _users = users;
        _filteredUsers = users;
      });
    } catch (e) {
      _showSnackBar('Erreur: ${_formatError(e)}', isError: true);
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

  String _formatError(Object error) {
    final text = error.toString();
    return text.startsWith('Exception: ') ? text.substring(11) : text;
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
          onTap: (index) {
            _filterByTab();
          },
          tabs: const [
            Tab(text: 'Tous', icon: Icon(Icons.people_rounded)),
            Tab(text: 'Super Admin', icon: Icon(Icons.admin_panel_settings_rounded)),
            Tab(text: 'Admin', icon: Icon(Icons.shield_rounded)),
          ],
        ),
        actions: [
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
          Container(
            padding: const EdgeInsets.all(16),
            color: _white,
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: 'Rechercher par identifiant, nom, email, CIN...',
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
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Total: ${_users.length}',
                    style: TextStyle(color: _textSecondary, fontSize: 12),
                  ),
                ),
              ],
            ),
          ),
          
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredUsers.isEmpty
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        onRefresh: _loadUsers,
                        color: _primaryBlue,
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.all(16),
                          physics: const AlwaysScrollableScrollPhysics(),
                          child: SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: DataTable(
                              headingRowColor: WidgetStateProperty.all(
                                _primaryBlue.withOpacity(0.05),
                              ),
                              headingTextStyle: TextStyle(
                                color: _primaryBlue,
                                fontWeight: FontWeight.w600,
                                fontSize: 13,
                              ),
                              dataTextStyle: TextStyle(
                                color: _textPrimary,
                                fontSize: 13,
                              ),
                              dividerThickness: 0,
                              horizontalMargin: 16,
                              columnSpacing: 20,
                              columns: const [
                                DataColumn(label: Text('Nom')),
                                DataColumn(label: Text('Prénom')),
                                DataColumn(label: Text('Téléphone')),
                                DataColumn(label: Text('CIN')),
                                DataColumn(label: Text('Email')),
                                DataColumn(label: Text('Identifiant')),
                                DataColumn(label: Text('Rôles')),
                                DataColumn(label: Text('Action')),
                              ],
                              rows: _filteredUsers.map((user) {
                                final roles = user.roles.isEmpty
                                    ? '-'
                                    : user.roles.map((role) {
                                        if (role == 'ROLE_SUPER_ADMIN') return 'Super Admin';
                                        if (role == 'ROLE_ADMIN') return 'Admin';
                                        return 'User';
                                      }).join(', ');
                                
                                return DataRow(
                                  cells: [
                                    DataCell(
                                      Container(
                                        padding: const EdgeInsets.symmetric(vertical: 8),
                                        child: Text(user.nom ?? '-'),
                                      ),
                                    ),
                                    DataCell(Text(user.prenom ?? '-')),
                                    DataCell(Text(user.telephone ?? '-')),
                                    DataCell(Text(user.cin ?? '-')),
                                    DataCell(Text(user.emailPersonne ?? '-')),
                                    DataCell(
                                      Row(
                                        children: [
                                          if (user.changepassword)
                                            Padding(
                                              padding: const EdgeInsets.only(right: 8),
                                              child: Icon(
                                                Icons.lock_reset_rounded,
                                                size: 14,
                                                color: _darkYellow,
                                              ),
                                            ),
                                          Expanded(
                                            child: Text(
                                              user.email,
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    DataCell(
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 8,
                                          vertical: 4,
                                        ),
                                        decoration: BoxDecoration(
                                          color: user.roleColor.withOpacity(0.15),
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: Text(
                                          roles,
                                          style: TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.w500,
                                            color: user.roleColor,
                                          ),
                                        ),
                                      ),
                                    ),
                                    DataCell(
                                      Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          IconButton(
                                            icon: Icon(
                                              Icons.edit_rounded,
                                              color: _primaryBlue,
                                              size: 18,
                                            ),
                                            tooltip: 'Modifier',
                                            onPressed: () => _showEditUserDialog(user),
                                          ),
                                          IconButton(
                                            icon: Icon(
                                              Icons.delete_rounded,
                                              color: _errorRed,
                                              size: 18,
                                            ),
                                            tooltip: 'Supprimer',
                                            onPressed: () => _confirmDeleteUser(user),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                );
                              }).toList(),
                            ),
                          ),
                        ),
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddUserDialog,
        backgroundColor: _primaryBlue,
        child: const Icon(Icons.add_rounded, color: Colors.white),
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
            'Cliquez sur le bouton + pour ajouter',
            style: TextStyle(fontSize: 13, color: _textSecondary.withOpacity(0.7)),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  void _showAddUserDialog() {
    final formKey = GlobalKey<FormState>();
    final nomController = TextEditingController();
    final prenomController = TextEditingController();
    final telephoneController = TextEditingController();
    final cinController = TextEditingController();
    final emailPersonneController = TextEditingController();
    final emailController = TextEditingController();
    final passwordController = TextEditingController();
    final confirmPasswordController = TextEditingController();
    String selectedRole = 'ROLE_ADMIN';
    bool isPasswordVisible = false;
    bool isConfirmPasswordVisible = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          elevation: 0,
          backgroundColor: Colors.transparent,
          child: Container(
            width: MediaQuery.of(context).size.width * 0.9,
            constraints: const BoxConstraints(maxWidth: 500),
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: _white,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: SingleChildScrollView(
              child: Form(
                key: formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [_lightYellow, _darkYellow],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(
                            Icons.person_add_rounded,
                            color: Colors.white,
                            size: 24,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Ajouter un utilisateur',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w600,
                                  color: _textPrimary,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Remplissez les informations ci-dessous',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: _textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                        IconButton(
                          onPressed: () => Navigator.pop(context),
                          icon: Icon(Icons.close_rounded, color: _textSecondary),
                        ),
                      ],
                    ),
                    
                    const SizedBox(height: 20),
                    
                    _buildLabel('Nom'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: nomController,
                      decoration: _buildInputDecoration(
                        icon: Icons.person_rounded,
                        hint: 'Entrez le nom',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Nom requis';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Prénom'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: prenomController,
                      decoration: _buildInputDecoration(
                        icon: Icons.person_outline_rounded,
                        hint: 'Entrez le prénom',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Prénom requis';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Téléphone'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: telephoneController,
                      keyboardType: TextInputType.phone,
                      decoration: _buildInputDecoration(
                        icon: Icons.phone_rounded,
                        hint: 'Entrez le téléphone',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Téléphone requis';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('CIN'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: cinController,
                      keyboardType: TextInputType.number,
                      decoration: _buildInputDecoration(
                        icon: Icons.credit_card_rounded,
                        hint: 'Entrez le CIN',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'CIN requis';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Email'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: emailPersonneController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: _buildInputDecoration(
                        icon: Icons.email_rounded,
                        hint: 'exemple@email.com',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Email requis';
                        }
                        if (!value.contains('@') || !value.contains('.')) {
                          return 'Email invalide';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Identifiant'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: emailController,
                      keyboardType: TextInputType.phone,
                      decoration: _buildInputDecoration(
                        icon: Icons.perm_identity_rounded,
                        hint: 'Entrez le meme numéro que téléphone',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Identifiant requis';
                        }
                        if (int.tryParse(value) == null) {
                          return 'Identifiant doit être le numéro de téléphone';
                        }
                        if (value.trim() != telephoneController.text.trim()) {
                          return 'L\'identifiant doit être le numéro de téléphone';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Rôle'),
                    const SizedBox(height: 6),
                    Container(
                      decoration: BoxDecoration(
                        color: _backgroundLight,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: DropdownButtonFormField<String>(
                        value: selectedRole,
                        decoration: const InputDecoration(
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        ),
                        icon: Icon(Icons.arrow_drop_down_rounded, color: _darkYellow),
                        items: const [
                          DropdownMenuItem(
                            value: 'ROLE_ADMIN',
                            child: Text('Admin'),
                          ),
                          DropdownMenuItem(
                            value: 'ROLE_SUPER_ADMIN',
                            child: Text('Super Admin'),
                          ),
                        ],
                        onChanged: (value) => setDialogState(() => selectedRole = value!),
                      ),
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Mot de passe'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: passwordController,
                      obscureText: !isPasswordVisible,
                      decoration: _buildInputDecoration(
                        icon: Icons.lock_rounded,
                        hint: '••••••••',
                        suffixIcon: IconButton(
                          icon: Icon(
                            isPasswordVisible ? Icons.visibility_off_rounded : Icons.visibility_rounded,
                            color: _textSecondary,
                            size: 20,
                          ),
                          onPressed: () {
                            setDialogState(() {
                              isPasswordVisible = !isPasswordVisible;
                            });
                          },
                        ),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Mot de passe requis';
                        }
                        if (value.length < 6) {
                          return 'Minimum 6 caractères';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Confirmer le mot de passe'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: confirmPasswordController,
                      obscureText: !isConfirmPasswordVisible,
                      decoration: _buildInputDecoration(
                        icon: Icons.lock_outline_rounded,
                        hint: '••••••••',
                        suffixIcon: IconButton(
                          icon: Icon(
                            isConfirmPasswordVisible ? Icons.visibility_off_rounded : Icons.visibility_rounded,
                            color: _textSecondary,
                            size: 20,
                          ),
                          onPressed: () {
                            setDialogState(() {
                              isConfirmPasswordVisible = !isConfirmPasswordVisible;
                            });
                          },
                        ),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Confirmation requise';
                        }
                        if (value != passwordController.text) {
                          return 'Les mots de passe ne correspondent pas';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 24),
                    
                    Row(
                      children: [
                        Expanded(
                          child: TextButton(
                            onPressed: () => Navigator.pop(context),
                            style: TextButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                                side: BorderSide(color: _borderLight),
                              ),
                            ),
                            child: Text(
                              'Annuler',
                              style: TextStyle(color: _textSecondary),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () async {
                              if (formKey.currentState!.validate()) {
                                try {
                                  await _userService.createUser(
                                    nom: nomController.text.trim(),
                                    prenom: prenomController.text.trim(),
                                    telephone: telephoneController.text.trim(),
                                    cin: cinController.text.trim(),
                                    emailPersonne: emailPersonneController.text.trim(),
                                    email: emailController.text.trim(),
                                    password: passwordController.text,
                                    roles: [selectedRole],
                                  );

                                  Navigator.pop(context);
                                  await _loadUsers();
                                  _showSnackBar('✅ Utilisateur ajouté avec succès');
                                } catch (e) {
                                  _showSnackBar('❌ Erreur: ${_formatError(e)}', isError: true);
                                }
                              }
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _primaryBlue,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              elevation: 0,
                            ),
                            child: const Text('Ajouter'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _showEditUserDialog(User user) {
    final formKey = GlobalKey<FormState>();
    final telephoneController = TextEditingController(text: user.telephone ?? '');
    final emailPersonneController = TextEditingController(text: user.emailPersonne ?? '');
    String selectedRole = user.roles.isNotEmpty ? user.roles.first : 'ROLE_ADMIN';
    final displayName = [
      user.nom?.trim() ?? '',
      user.prenom?.trim() ?? '',
    ].where((part) => part.isNotEmpty).join(' ');
    final userLabel = displayName.isNotEmpty ? displayName : user.email;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          child: Container(
            width: MediaQuery.of(context).size.width * 0.9,
            constraints: const BoxConstraints(maxWidth: 500),
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: _white,
              borderRadius: BorderRadius.circular(20),
            ),
            child: SingleChildScrollView(
              child: Form(
                key: formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: _primaryBlue.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(Icons.edit_rounded, color: _primaryBlue),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Text(
                            'Modifier utilisateur',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                              color: _textPrimary,
                            ),
                          ),
                        ),
                        IconButton(
                          onPressed: () => Navigator.pop(context),
                          icon: Icon(Icons.close_rounded, color: _textSecondary),
                        ),
                      ],
                    ),
                    
                    const SizedBox(height: 20),
                    
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: _primaryBlue.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: _borderLight),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            userLabel,
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                              color: _textPrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'L\'identifiant de connexion sera mis a jour automatiquement avec le téléphone.',
                            style: TextStyle(
                              fontSize: 12,
                              color: _textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Téléphone'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: telephoneController,
                      keyboardType: TextInputType.phone,
                      decoration: _buildInputDecoration(
                        icon: Icons.phone_rounded,
                        hint: 'Entrez le téléphone',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Téléphone requis';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Email'),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: emailPersonneController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: _buildInputDecoration(
                        icon: Icons.email_rounded,
                        hint: 'exemple@email.com',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Email requis';
                        }
                        if (!value.contains('@') || !value.contains('.')) {
                          return 'Email invalide';
                        }
                        return null;
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    _buildLabel('Rôle'),
                    const SizedBox(height: 6),
                    Container(
                      decoration: BoxDecoration(
                        color: _backgroundLight,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: DropdownButtonFormField<String>(
                        value: selectedRole,
                        decoration: const InputDecoration(
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        ),
                        icon: Icon(Icons.arrow_drop_down_rounded, color: _darkYellow),
                        items: const [
                          DropdownMenuItem(
                            value: 'ROLE_ADMIN',
                            child: Text('Admin'),
                          ),
                          DropdownMenuItem(
                            value: 'ROLE_SUPER_ADMIN',
                            child: Text('Super Admin'),
                          ),
                        ],
                        onChanged: (value) => setDialogState(() => selectedRole = value!),
                      ),
                    ),
                    
                    const SizedBox(height: 24),
                    
                    Row(
                      children: [
                        Expanded(
                          child: TextButton(
                            onPressed: () => Navigator.pop(context),
                            style: TextButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                                side: BorderSide(color: _borderLight),
                              ),
                            ),
                            child: Text(
                              'Annuler',
                              style: TextStyle(color: _textSecondary),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () async {
                              if (formKey.currentState!.validate()) {
                                try {
                                  await _userService.updateUser(
                                    id: user.id,
                                    telephone: telephoneController.text.trim(),
                                    emailPersonne: emailPersonneController.text.trim(),
                                    roles: [selectedRole],
                                  );

                                  Navigator.pop(context);
                                  await _loadUsers();
                                  _showSnackBar('✅ Utilisateur modifié avec succès');
                                } catch (e) {
                                  _showSnackBar('❌ Erreur: ${_formatError(e)}', isError: true);
                                }
                              }
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _primaryBlue,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              elevation: 0,
                            ),
                            child: const Text('Modifier'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w500,
        color: _textPrimary,
      ),
    );
  }

  InputDecoration _buildInputDecoration({
    required IconData icon,
    required String hint,
    Widget? suffixIcon,
  }) {
    return InputDecoration(
      hintText: hint,
      prefixIcon: Icon(icon, color: _textSecondary, size: 20),
      suffixIcon: suffixIcon,
      filled: true,
      fillColor: _backgroundLight,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: _darkYellow, width: 2),
      ),
      contentPadding: const EdgeInsets.symmetric(vertical: 14),
    );
  }

  void _confirmDeleteUser(User user) {
    final userFullName = [
      user.nom?.trim() ?? '',
      user.prenom?.trim() ?? '',
    ].where((part) => part.isNotEmpty).join(' ');
    final userLabel = userFullName.isNotEmpty ? userFullName : user.email;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmer la suppression'),
        content: Text('Supprimer définitivement $userLabel ?'),
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
                await _loadUsers();
                _showSnackBar('$userLabel a été supprimé');
              } catch (e) {
                _showSnackBar('Erreur: ${_formatError(e)}', isError: true);
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: _errorRed,
              foregroundColor: Colors.white,
            ),
            child: const Text('Supprimer'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    _tabController.dispose();
    super.dispose();
  }
}
