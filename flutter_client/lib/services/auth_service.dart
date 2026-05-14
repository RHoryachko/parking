import 'package:shared_preferences/shared_preferences.dart';

import '../models/user_model.dart';
import 'api_client.dart';

class AuthService {
  static const _tokenKey = 'parking_token';
  final ApiClient _apiClient;

  AuthService(this._apiClient);

  Future<String> login({
    required String email,
    required String password,
  }) async {
    if (ApiClient.useMock) {
      const token = 'mock-token';
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_tokenKey, token);
      _apiClient.setToken(token);
      return token;
    }
    final response = await _apiClient.dio.post(
      '/auth/login',
      data: {'email': email, 'password': password},
    );
    final token = response.data['access_token'] as String;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    _apiClient.setToken(token);
    return token;
  }

  Future<void> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    if (ApiClient.useMock) {
      await Future<void>.delayed(const Duration(milliseconds: 250));
      return;
    }
    await _apiClient.dio.post(
      '/auth/register',
      data: {
        'full_name': fullName,
        'email': email,
        'password': password,
      },
    );
  }

  Future<UserModel> me() async {
    if (ApiClient.useMock) {
      return UserModel(
        id: 1,
        fullName: 'Mock Client',
        email: 'mock.client@parking.local',
        role: 'client',
        phone: '+380501112233',
        isBlocked: false,
        createdAt: DateTime.utc(2025, 1, 15),
      );
    }
    final response = await _apiClient.dio.get('/auth/me');
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<String?> restoreToken() async {
    if (ApiClient.useMock) {
      _apiClient.setToken('mock-token');
      return 'mock-token';
    }
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    _apiClient.setToken(token);
    return token;
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    _apiClient.setToken(null);
  }
}
