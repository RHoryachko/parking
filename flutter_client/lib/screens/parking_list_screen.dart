import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../app.dart';
import '../models/parking_model.dart';
import '../services/api_client.dart';
import '../services/client_service.dart';
import '../widgets/parking_card.dart';
import 'parking_map_screen.dart';

class ParkingListScreen extends StatefulWidget {
  const ParkingListScreen({super.key});

  @override
  State<ParkingListScreen> createState() => _ParkingListScreenState();
}

class _ParkingListScreenState extends State<ParkingListScreen> {
  late Future<List<ParkingModel>> _future;
  String _city = 'All';

  @override
  void initState() {
    super.initState();
    _future = context.read<ClientService>().listParkings();
    if (kIsWeb) {
      final bid = Uri.base.queryParameters['booking_id'];
      if (bid != null && bid.isNotEmpty) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Оплату прийнято. Бронювання #$bid'),
              behavior: SnackBarBehavior.floating,
              duration: const Duration(seconds: 6),
            ),
          );
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(ApiClient.useMock ? 'Available Parkings (Mock)' : 'Available Parkings'),
        actions: [
          IconButton(
            onPressed: () => Navigator.pushNamed(context, '/profile'),
            icon: const Icon(Icons.person_outline_rounded),
            tooltip: 'Профіль',
          ),
          IconButton(
            onPressed: () => Navigator.pushNamed(context, '/vehicles'),
            icon: const Icon(Icons.directions_car_outlined),
            tooltip: 'Мої авто',
          ),
          IconButton(
            onPressed: () => Navigator.pushNamed(context, '/my-bookings'),
            icon: const Icon(Icons.receipt_long_outlined),
            tooltip: 'My bookings',
          ),
          IconButton(
            onPressed: () async {
              await context.read<AuthController>().logout();
              if (!context.mounted) return;
              Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
            },
            icon: const Icon(Icons.logout_rounded),
            tooltip: 'Logout',
          ),
        ],
      ),
      body: FutureBuilder<List<ParkingModel>>(
        future: _future,
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final parkings = snapshot.data!;
          if (parkings.isEmpty) return const Center(child: Text('No parkings found'));
          final cities = {'All', ...parkings.map((e) => e.city)}.toList();
          final filtered = _city == 'All'
              ? parkings
              : parkings.where((p) => p.city.toLowerCase() == _city.toLowerCase()).toList();
          final freeModeCount = parkings.where((p) => p.workMode == 'manual').length;
          final aiModeCount = parkings.where((p) => p.workMode == 'ai').length;
          return ListView(
            padding: const EdgeInsets.only(top: 8, bottom: 12),
            children: [
              GestureDetector(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => ParkingMapScreen(parkings: parkings),
                    ),
                  );
                },
                child: Tooltip(
                  message: 'Відкрити карту',
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 16),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF4338CA), Color(0xFF6366F1)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF4338CA).withValues(alpha: 0.35),
                          blurRadius: 12,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'City parking map',
                                style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w800),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '${parkings.length} lots • Manual $freeModeCount • AI $aiModeCount',
                                style: const TextStyle(color: Colors.white70),
                              ),
                            ],
                          ),
                        ),
                        const Icon(Icons.map_outlined, color: Colors.white70, size: 32),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              SizedBox(
                height: 44,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  children: cities.map((city) {
                    final selected = city == _city;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(city),
                        selected: selected,
                        onSelected: (_) => setState(() => _city = city),
                        selectedColor: const Color(0xFF4F46E5).withValues(alpha: 0.18),
                        side: BorderSide(
                          color: selected ? const Color(0xFF4F46E5) : const Color(0xFFE5E7EB),
                        ),
                        labelStyle: TextStyle(
                          color: selected ? const Color(0xFF312E81) : const Color(0xFF374151),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
              const SizedBox(height: 4),
              ...filtered.map(
                (parking) => ParkingCard(
                  parking: parking,
                  onTap: () => Navigator.pushNamed(context, '/parking-details', arguments: parking.id),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

