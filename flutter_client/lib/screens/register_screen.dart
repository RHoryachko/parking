import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app.dart';
import '../widgets/primary_button.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _fullName = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _loading = false;
  String? _message;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create account')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('New client profile', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 16),
                    TextField(controller: _fullName, decoration: const InputDecoration(labelText: 'Full name')),
                    const SizedBox(height: 10),
                    TextField(controller: _email, decoration: const InputDecoration(labelText: 'Email')),
                    const SizedBox(height: 10),
                    TextField(
                      controller: _password,
                      decoration: const InputDecoration(labelText: 'Password'),
                      obscureText: true,
                    ),
                    const SizedBox(height: 16),
                    PrimaryButton(
                      label: _loading ? 'Registering...' : 'Create account',
                      onPressed: _loading
                          ? null
                          : () async {
                              setState(() {
                                _loading = true;
                                _message = null;
                              });
                              try {
                                await context.read<AuthController>().register(
                                      _fullName.text.trim(),
                                      _email.text.trim(),
                                      _password.text,
                                    );
                                setState(() => _message = 'Registered successfully. Please sign in.');
                              } catch (_) {
                                setState(() => _message = 'Registration failed.');
                              } finally {
                                if (mounted) setState(() => _loading = false);
                              }
                            },
                    ),
                    const SizedBox(height: 8),
                    TextButton(onPressed: () => Navigator.pop(context), child: const Text('Back to login')),
                    if (_message != null) Text(_message!, style: const TextStyle(color: Color(0xFF374151))),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

