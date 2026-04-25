const String adminRole = 'ROLE_ADMIN';
const String superAdminRole = 'ROLE_SUPER_ADMIN';

const String adminRoleLabel = 'Personnel administrateur';
const String superAdminRoleLabel = 'Administrateur';
const String defaultRoleLabel = 'Utilisateur';

String roleLabel(String role) {
  switch (role) {
    case superAdminRole:
      return superAdminRoleLabel;
    case adminRole:
      return adminRoleLabel;
    default:
      return defaultRoleLabel;
  }
}

String primaryRoleLabel(List<String> roles) {
  if (roles.contains(superAdminRole)) return superAdminRoleLabel;
  if (roles.contains(adminRole)) return adminRoleLabel;
  return defaultRoleLabel;
}
