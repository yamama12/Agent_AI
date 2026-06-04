// lib/screens/profile_screen.dart
import 'package:flutter/material.dart';
import '../services/profile_service.dart';
import '../models/profile.dart';
import '../core/role_labels.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> with SingleTickerProviderStateMixin {
  final ProfileService _profileService = ProfileService();
  
  ProfileData? _profile;
  bool _isLoading = true;
  
  // Contrôleurs pour le changement de mot de passe
  final _formKey = GlobalKey<FormState>();
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _isChangingPassword = false;
  bool _showPasswordForm = false;
  
  // États pour la visibilité des mots de passe
  bool _showCurrentPassword = false;
  bool _showNewPassword = false;
  bool _showConfirmPassword = false;
  
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

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
  static const Color _errorRed = Color(0xFFD32F2F);
  static const Color _cardShadow = Color(0xFF1A2B3C);

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );
    _loadProfile().then((_) {
      _animationController.forward();
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    setState(() => _isLoading = true);
    try {
      final profile = await _profileService.getProfile();
      setState(() {
        _profile = profile;
      });
    } catch (e) {
      _showSnackBar('Erreur: ${_formatError(e)}', isError: true);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _changePassword() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isChangingPassword = true);
    
    try {
      await _profileService.changePassword(
        _currentPasswordController.text,
        _newPasswordController.text,
      );
      
      _currentPasswordController.clear();
      _newPasswordController.clear();
      _confirmPasswordController.clear();
      setState(() => _showPasswordForm = false);
      
      _showSnackBar('✅ Mot de passe modifié avec succès');
    } catch (e) {
      _showSnackBar('❌ Erreur: ${_formatError(e)}', isError: true);
    } finally {
      setState(() => _isChangingPassword = false);
    }
  }

  void _showSnackBar(String message, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(isError ? Icons.error_outline : Icons.check_circle, color: Colors.white, size: 20),
            const SizedBox(width: 12),
            Expanded(child: Text(message)),
          ],
        ),
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

  Widget _buildInfoTile(String label, String? value, IconData icon) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
      decoration: BoxDecoration(
        color: _backgroundLight,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: _darkYellow.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: _darkYellow, size: 18),
          ),
          const SizedBox(width: 14),
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: TextStyle(
                fontSize: 13,
                color: _textSecondary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Text(
              value?.isNotEmpty == true ? value! : 'Non renseigné',
              style: TextStyle(
                fontSize: 14,
                color: value?.isNotEmpty == true ? _textPrimary : _textSecondary,
                fontWeight: value?.isNotEmpty == true ? FontWeight.w600 : FontWeight.normal,
              ),
              textAlign: TextAlign.end,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [_lightYellow, _darkYellow],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: Colors.white, size: 18),
        ),
        const SizedBox(width: 12),
        Text(
          title,
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w600,
            color: _textPrimary,
            letterSpacing: -0.3,
          ),
        ),
      ],
    );
  }

  Widget _buildHeader() {
    final primaryRole = primaryRoleLabel(_profile?.roles ?? []);
    final roleColor = _darkYellow;

    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          // Avatar avec animation
          TweenAnimationBuilder<double>(
            tween: Tween<double>(begin: 0.5, end: 1.0),
            duration: const Duration(milliseconds: 800),
            curve: Curves.elasticOut,
            builder: (context, scale, child) {
              return Transform.scale(
                scale: scale,
                child: Container(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: _darkYellow.withOpacity(0.2),
                        blurRadius: 20,
                        spreadRadius: 5,
                      ),
                    ],
                  ),
                  child: Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [_lightYellow, _darkYellow],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: Colors.white,
                        width: 3,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        _profile?.fullName.isNotEmpty == true
                            ? _profile!.fullName[0].toUpperCase()
                            : _profile?.email[0].toUpperCase() ?? 'U',
                        style: const TextStyle(
                          fontSize: 38,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                          letterSpacing: 1,
                        ),
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          // Nom
          Text(
            _profile?.fullName.isNotEmpty == true 
                ? _profile!.fullName 
                : _profile?.email ?? 'Utilisateur',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: _textPrimary,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 8),
          // Badge rôle
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
            decoration: BoxDecoration(
              color: roleColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: roleColor.withOpacity(0.3), width: 1),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  _profile?.roles.contains(superAdminRole) == true
                      ? Icons.admin_panel_settings_rounded
                      : Icons.person_rounded,
                  size: 14,
                  color: roleColor,
                ),
                const SizedBox(width: 6),
                Text(
                  primaryRole,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                    color: roleColor,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPasswordChangeSection() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      decoration: BoxDecoration(
        color: _white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: _cardShadow.withOpacity(0.05),
            blurRadius: 20,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => setState(() => _showPasswordForm = !_showPasswordForm),
              borderRadius: BorderRadius.circular(24),
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [_lightYellow, _darkYellow],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Icon(
                        _showPasswordForm ? Icons.lock_open_rounded : Icons.lock_rounded,
                        color: Colors.white,
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Sécurité du compte',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: _textPrimary,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Modifier votre mot de passe',
                            style: TextStyle(
                              fontSize: 12,
                              color: _textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    AnimatedRotation(
                      turns: _showPasswordForm ? 0.5 : 0.0,
                      duration: const Duration(milliseconds: 300),
                      child: Icon(
                        Icons.chevron_right_rounded,
                        color: _textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          AnimatedCrossFade(
            duration: const Duration(milliseconds: 300),
            crossFadeState: _showPasswordForm
                ? CrossFadeState.showFirst
                : CrossFadeState.showSecond,
            firstChild: Container(
              padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    const Divider(height: 1, color: _borderLight),
                    const SizedBox(height: 20),
                    // Mot de passe actuel
                    TextFormField(
                      controller: _currentPasswordController,
                      obscureText: !_showCurrentPassword,
                      style: const TextStyle(fontSize: 14),
                      decoration: InputDecoration(
                        labelText: 'Mot de passe actuel',
                        labelStyle: TextStyle(color: _textSecondary),
                        prefixIcon: Icon(Icons.lock_outline_rounded, color: _darkYellow, size: 20),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _showCurrentPassword ? Icons.visibility_off_rounded : Icons.visibility_rounded,
                            size: 20,
                            color: _textSecondary,
                          ),
                          onPressed: () => setState(() => _showCurrentPassword = !_showCurrentPassword),
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: _borderLight),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: _borderLight),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: _darkYellow, width: 2),
                        ),
                        filled: true,
                        fillColor: _backgroundLight,
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Mot de passe actuel requis';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    // Nouveau mot de passe
                    TextFormField(
                      controller: _newPasswordController,
                      obscureText: !_showNewPassword,
                      style: const TextStyle(fontSize: 14),
                      decoration: InputDecoration(
                        labelText: 'Nouveau mot de passe',
                        labelStyle: TextStyle(color: _textSecondary),
                        prefixIcon: Icon(Icons.lock_outline_rounded, color: _darkYellow, size: 20),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _showNewPassword ? Icons.visibility_off_rounded : Icons.visibility_rounded,
                            size: 20,
                            color: _textSecondary,
                          ),
                          onPressed: () => setState(() => _showNewPassword = !_showNewPassword),
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: _borderLight),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: _borderLight),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: _darkYellow, width: 2),
                        ),
                        filled: true,
                        fillColor: _backgroundLight,
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Nouveau mot de passe requis';
                        }
                        if (value.length < 6) {
                          return 'Minimum 6 caractères';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    // Confirmation
                    TextFormField(
                      controller: _confirmPasswordController,
                      obscureText: !_showConfirmPassword,
                      style: const TextStyle(fontSize: 14),
                      decoration: InputDecoration(
                        labelText: 'Confirmer le mot de passe',
                        labelStyle: TextStyle(color: _textSecondary),
                        prefixIcon: Icon(Icons.lock_outline_rounded, color: _darkYellow, size: 20),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _showConfirmPassword ? Icons.visibility_off_rounded : Icons.visibility_rounded,
                            size: 20,
                            color: _textSecondary,
                          ),
                          onPressed: () => setState(() => _showConfirmPassword = !_showConfirmPassword),
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: _borderLight),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: _borderLight),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: _darkYellow, width: 2),
                        ),
                        filled: true,
                        fillColor: _backgroundLight,
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Confirmation requise';
                        }
                        if (value != _newPasswordController.text) {
                          return 'Les mots de passe ne correspondent pas';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isChangingPassword ? null : _changePassword,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _primaryBlue,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                          elevation: 0,
                        ),
                        child: _isChangingPassword
                            ? const SizedBox(
                                width: 22,
                                height: 22,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Text('Changer le mot de passe'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            secondChild: const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        backgroundColor: _backgroundLight,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text(
                'Chargement du profil...',
                style: TextStyle(color: _textSecondary),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: _backgroundLight,
      appBar: AppBar(
        backgroundColor: _white,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_rounded, color: _primaryBlue),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Mon profil',
          style: TextStyle(
            color: _primaryBlue,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
        centerTitle: false,
      ),
      body: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        child: Column(
          children: [
            FadeTransition(
              opacity: _fadeAnimation,
              child: _buildHeader(),
            ),
            
            const SizedBox(height: 20),
            
            // Contenu principal
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  // Informations personnelles
                  FadeTransition(
                    opacity: _fadeAnimation,
                    child: Container(
                      decoration: BoxDecoration(
                        color: _white,
                        borderRadius: BorderRadius.circular(24),
                        boxShadow: [
                          BoxShadow(
                            color: _cardShadow.withOpacity(0.05),
                            blurRadius: 20,
                            offset: const Offset(0, 5),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(18),
                            child: _buildSectionHeader('Informations personnelles', Icons.person_outline_rounded),
                          ),
                          const Divider(height: 1, color: _borderLight),
                          Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              children: [
                                _buildInfoTile('Nom complet', _profile?.fullName, Icons.person_rounded),
                                const SizedBox(height: 8),
                                _buildInfoTile('Téléphone', _profile?.telephone, Icons.phone_rounded),
                                const SizedBox(height: 8),
                                _buildInfoTile('CIN', _profile?.cin, Icons.credit_card_rounded),
                                const SizedBox(height: 8),
                                _buildInfoTile('Email', _profile?.emailPersonne, Icons.email_rounded),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 20),
                  
                  // Informations de connexion
                  FadeTransition(
                    opacity: _fadeAnimation,
                    child: Container(
                      decoration: BoxDecoration(
                        color: _white,
                        borderRadius: BorderRadius.circular(24),
                        boxShadow: [
                          BoxShadow(
                            color: _cardShadow.withOpacity(0.05),
                            blurRadius: 20,
                            offset: const Offset(0, 5),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(18),
                            child: _buildSectionHeader('Informations de connexion', Icons.login_rounded),
                          ),
                          const Divider(height: 1, color: _borderLight),
                          Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              children: [
                                _buildInfoTile('Identifiant', _profile?.email, Icons.alternate_email_rounded),
                                const SizedBox(height: 8),
                                _buildInfoTile('Rôle', primaryRoleLabel(_profile?.roles ?? []), Icons.admin_panel_settings_rounded),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 20),
                  
                  // Changement de mot de passe
                  FadeTransition(
                    opacity: _fadeAnimation,
                    child: _buildPasswordChangeSection(),
                  ),
                  
                  const SizedBox(height: 30),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}