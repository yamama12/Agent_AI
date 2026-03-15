class LoginRequest {
    final String email;
    final String password;
    
    LoginRequest({required this.email, required this.password});
    
      Map<String, dynamic> toJson() => {
        'email': email,
        'password': password,
      };
}

class LoginResponse {
    final String accessToken;
    final String role;
    final bool changePassword;

    LoginResponse({required this.accessToken, required this.role, required this.changePassword});
    factory LoginResponse.fromJson(Map<String, dynamic> json) {
        return LoginResponse(
            accessToken: json['access_token'],
            role: json['role'],
            changePassword: json['change_password'] ?? false,
        );
    }
}