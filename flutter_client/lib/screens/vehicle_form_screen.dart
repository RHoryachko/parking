import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/vehicle_model.dart';
import '../services/client_service.dart';
import '../widgets/primary_button.dart';

class VehicleFormScreen extends StatefulWidget {
  final VehicleModel? vehicle;

  const VehicleFormScreen({super.key, this.vehicle});

  @override
  State<VehicleFormScreen> createState() => _VehicleFormScreenState();
}

class _VehicleFormScreenState extends State<VehicleFormScreen> {
  late final TextEditingController _plate;
  late final TextEditingController _brand;
  late final TextEditingController _model;
  late final TextEditingController _color;
  bool _saving = false;
  bool _deleting = false;
  String? _message;

  bool get _isEdit => widget.vehicle != null;

  @override
  void initState() {
    super.initState();
    final v = widget.vehicle;
    _plate = TextEditingController(text: v?.plateNumber ?? '');
    _brand = TextEditingController(text: v?.brand ?? '');
    _model = TextEditingController(text: v?.model ?? '');
    _color = TextEditingController(text: v?.color ?? '');
  }

  @override
  void dispose() {
    _plate.dispose();
    _brand.dispose();
    _model.dispose();
    _color.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final plate = _plate.text.trim();
    if (plate.isEmpty) {
      setState(() => _message = 'Вкажіть номерний знак');
      return;
    }
    setState(() {
      _saving = true;
      _message = null;
    });
    try {
      final svc = context.read<ClientService>();
      final brand = _brand.text.trim().isEmpty ? null : _brand.text.trim();
      final model = _model.text.trim().isEmpty ? null : _model.text.trim();
      final color = _color.text.trim().isEmpty ? null : _color.text.trim();
      if (_isEdit) {
        await svc.updateVehicle(
          widget.vehicle!.id,
          plateNumber: plate,
          brand: brand,
          model: model,
          color: color,
        );
      } else {
        await svc.createVehicle(
          plateNumber: plate,
          brand: brand,
          model: model,
          color: color,
        );
      }
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) {
        setState(() => _message = e.toString().contains('409') ? 'Такий номер уже зареєстровано' : 'Не вдалося зберегти');
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _delete() async {
    if (!_isEdit) return;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Видалити авто?'),
        content: const Text('Бронювання, пов’язані з цим ТЗ, можуть стати недійсними.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Скасувати')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Видалити', style: TextStyle(color: Color(0xFFB91C1C))),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() {
      _deleting = true;
      _message = null;
    });
    try {
      await context.read<ClientService>().deleteVehicle(widget.vehicle!.id);
      if (mounted) Navigator.pop(context);
    } catch (_) {
      if (mounted) setState(() => _message = 'Не вдалося видалити');
    } finally {
      if (mounted) setState(() => _deleting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_isEdit ? 'Редагування ТЗ' : 'Нове авто')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _plate,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(labelText: 'Номерний знак'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _brand,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(labelText: 'Марка (необов’язково)'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _model,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(labelText: 'Модель (необов’язково)'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _color,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(labelText: 'Колір (необов’язково)'),
            ),
            const SizedBox(height: 20),
            PrimaryButton(
              label: _saving ? 'Збереження…' : (_isEdit ? 'Зберегти' : 'Створити'),
              onPressed: (_saving || _deleting) ? null : _save,
            ),
            if (_isEdit) ...[
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: (_saving || _deleting) ? null : _delete,
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(48),
                  foregroundColor: const Color(0xFFB91C1C),
                  side: const BorderSide(color: Color(0xFFFCA5A5)),
                ),
                child: Text(_deleting ? 'Видалення…' : 'Видалити авто'),
              ),
            ],
            if (_message != null) ...[
              const SizedBox(height: 12),
              Text(_message!, style: const TextStyle(color: Color(0xFF374151))),
            ],
          ],
        ),
      ),
    );
  }
}
