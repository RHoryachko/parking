import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app.dart';
import '../widgets/primary_button.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController(text: 'client@parking.local');
  final _password = TextEditingController(text: 'client123');
  bool _loading = false;
  String? _error;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFEFF6FF), Color(0xFFF8FAFC)],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            width: 52,
                            height: 52,
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFF4338CA), Color(0xFF7C3AED)],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: const Icon(Icons.local_parking_rounded, color: Colors.white),
                          ),
                          const SizedBox(height: 14),
                          const Text('Welcome back', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800)),
                          const SizedBox(height: 4),
                          const Text('Sign in to your parking client account', style: TextStyle(color: Color(0xFF6B7280))),
                          const SizedBox(height: 20),
                          TextFormField(
                            controller: _email,
                            decoration: const InputDecoration(labelText: 'Email'),
                            validator: (v) => (v == null || !v.contains('@')) ? 'Enter valid email' : null,
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: _password,
                            decoration: const InputDecoration(labelText: 'Password'),
                            obscureText: true,
                            validator: (v) => (v == null || v.length < 6) ? 'Min 6 symbols' : null,
                          ),
                          const SizedBox(height: 16),
                          PrimaryButton(
                            label: _loading ? 'Signing in...' : 'Sign in',
                            onPressed: _loading
                                ? null
                                : () async {
                                    if (!_formKey.currentState!.validate()) return;
                                    setState(() {
                                      _loading = true;
                                      _error = null;
                                    });
                                    try {
                                      await context.read<AuthController>().login(_email.text.trim(), _password.text);
                                      if (!context.mounted) return;
                                      Navigator.pushReplacementNamed(context, '/parkings');
                                    } catch (_) {
                                      setState(() => _error = 'Login failed. Check credentials.');
                                    } finally {
                                      if (mounted) setState(() => _loading = false);
                                    }
                                  },
                          ),
                          TextButton(
                            onPressed: () => Navigator.pushNamed(context, '/register'),
                            child: const Text('Create account'),
                          ),
                          if (_error != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Text(_error!, style: const TextStyle(color: Colors.red)),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

