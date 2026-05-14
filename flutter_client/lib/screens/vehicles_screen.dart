import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/vehicle_model.dart';
import '../services/client_service.dart';

class VehiclesScreen extends StatefulWidget {
  const VehiclesScreen({super.key});

  @override
  State<VehiclesScreen> createState() => _VehiclesScreenState();
}

class _VehiclesScreenState extends State<VehiclesScreen> {
  late Future<List<VehicleModel>> _future;

  @override
  void initState() {
    super.initState();
    _future = context.read<ClientService>().listVehicles();
  }

  Future<void> _reload() async {
    setState(() {
      _future = context.read<ClientService>().listVehicles();
    });
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Мої авто'),
        actions: [
          IconButton(onPressed: _reload, icon: const Icon(Icons.refresh_rounded)),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await Navigator.pushNamed(context, '/vehicle-form');
          if (mounted) await _reload();
        },
        icon: const Icon(Icons.add_rounded),
        label: const Text('Додати'),
      ),
      body: FutureBuilder<List<VehicleModel>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Помилка: ${snapshot.error}'));
          }
          final list = snapshot.data ?? [];
          if (list.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.directions_car_outlined, size: 56, color: Colors.grey.shade400),
                    const SizedBox(height: 12),
                    const Text('Ще немає транспортних засобів', textAlign: TextAlign.center),
                    const SizedBox(height: 8),
                    TextButton(
                      onPressed: () async {
                        await Navigator.pushNamed(context, '/vehicle-form');
                        if (mounted) await _reload();
                      },
                      child: const Text('Додати перше авто'),
                    ),
                  ],
                ),
              ),
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 88),
            itemCount: list.length,
            separatorBuilder: (context, index) {
              return const SizedBox(height: 8);
            },
            itemBuilder: (context, i) {
              final v = list[i];
              final subtitle = [
                if ((v.brand ?? '').isNotEmpty || (v.model ?? '').isNotEmpty)
                  '${v.brand ?? ''} ${v.model ?? ''}'.trim(),
                if ((v.color ?? '').isNotEmpty) v.color!,
              ].where((e) => e.isNotEmpty).join(' · ');
              return Card(
                child: ListTile(
                  title: Text(
                    v.plateNumber,
                    style: const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 0.5),
                  ),
                  subtitle: subtitle.isEmpty ? null : Text(subtitle),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () async {
                    await Navigator.pushNamed(context, '/vehicle-form', arguments: v);
                    if (mounted) await _reload();
                  },
                ),
              );
            },
          );
        },
      ),
    );
  }
}
