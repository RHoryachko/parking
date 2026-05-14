import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app.dart';
import '../services/client_service.dart';
import '../widgets/primary_button.dart';

(String first, String last) _splitFullName(String full) {
  final t = full.trim();
  if (t.isEmpty) return ('', '');
  final i = t.indexOf(' ');
  if (i <= 0) return (t, '');
  return (t.substring(0, i).trim(), t.substring(i + 1).trim());
}

String _joinFullName(String first, String last) {
  final f = first.trim();
  final l = last.trim();
  if (f.isEmpty && l.isEmpty) return '';
  if (l.isEmpty) return f;
  if (f.isEmpty) return l;
  return '$f $l';
}

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _first = TextEditingController();
  final _last = TextEditingController();
  final _phone = TextEditingController();
  bool _loading = true;
  bool _saving = false;
  String? _message;

  @override
  void dispose() {
    _first.dispose();
    _last.dispose();
    _phone.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      final auth = context.read<AuthController>();
      await auth.refreshUser();
      if (!mounted) return;
      final u = auth.user;
      if (u == null) return;
      final parts = _splitFullName(u.fullName);
      _first.text = parts.$1;
      _last.text = parts.$2;
      _phone.text = u.phone ?? '';
    } catch (e) {
      if (mounted) setState(() => _message = 'Не вдалося завантажити профіль');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _load());
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthController>();
    final user = auth.user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Профіль'),
        actions: [
          IconButton(onPressed: _loading ? null : _load, icon: const Icon(Icons.refresh_rounded)),
        ],
      ),
      body: _loading || user == null
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            user.email,
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                          ),
                          const SizedBox(height: 8),
                          _infoRow('Роль', user.role),
                          if (user.createdAt != null)
                            _infoRow(
                              'Зареєстровано',
                              '${user.createdAt!.toLocal().day.toString().padLeft(2, '0')}.'
                              '${user.createdAt!.toLocal().month.toString().padLeft(2, '0')}.'
                              '${user.createdAt!.toLocal().year}',
                            ),
                          if (user.isBlocked)
                            const Padding(
                              padding: EdgeInsets.only(top: 8),
                              child: Text(
                                'Обліковий запис заблоковано',
                                style: TextStyle(color: Color(0xFFB91C1C), fontWeight: FontWeight.w600),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Редагування',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Color(0xFF374151)),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _first,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(labelText: "Ім'я"),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: _last,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(labelText: 'Прізвище'),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: _phone,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(labelText: 'Телефон'),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'На сервері зберігається одне поле «повне ім’я» (ім’я та прізвище разом).',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600, height: 1.35),
                  ),
                  const SizedBox(height: 16),
                  PrimaryButton(
                    label: _saving ? 'Збереження…' : 'Зберегти зміни',
                    onPressed: _saving
                        ? null
                        : () async {
                            final full = _joinFullName(_first.text, _last.text);
                            if (full.isEmpty) {
                              setState(() => _message = "Вкажіть ім'я або прізвище");
                              return;
                            }
                            setState(() {
                              _saving = true;
                              _message = null;
                            });
                            try {
                              final client = context.read<ClientService>();
                              final updated = await client.updateProfile(
                                current: user,
                                fullName: full,
                                phoneRaw: _phone.text,
                              );
                              if (!context.mounted) return;
                              context.read<AuthController>().replaceUser(updated);
                              setState(() => _message = 'Збережено');
                            } catch (_) {
                              if (mounted) setState(() => _message = 'Помилка збереження');
                            } finally {
                              if (mounted) setState(() => _saving = false);
                            }
                          },
                  ),
                  if (_message != null) ...[
                    const SizedBox(height: 12),
                    Text(_message!, style: const TextStyle(color: Color(0xFF374151))),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label, style: TextStyle(color: Colors.grey.shade600, fontWeight: FontWeight.w600)),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
