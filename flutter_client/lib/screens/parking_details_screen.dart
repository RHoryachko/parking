import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/parking_model.dart';
import '../models/spot_model.dart';
import '../services/client_service.dart';
import 'booking_screen.dart';

class ParkingDetailsScreen extends StatefulWidget {
  final int parkingId;
  const ParkingDetailsScreen({super.key, required this.parkingId});

  @override
  State<ParkingDetailsScreen> createState() => _ParkingDetailsScreenState();
}

class _ParkingDetailsScreenState extends State<ParkingDetailsScreen> {
  ParkingModel? parking;
  List<SpotModel> spots = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final service = context.read<ClientService>();
    final p = await service.getParking(widget.parkingId);
    final s = await service.listSpots(widget.parkingId);
    setState(() {
      parking = p;
      spots = s;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final freeCount = spots.where((e) => e.status == 'free').length;
    return Scaffold(
      appBar: AppBar(title: Text(parking!.name)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${parking!.city}, ${parking!.address}',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        _chip('Mode: ${parking!.workMode}', const Color(0xFFE0E7FF), const Color(0xFF4338CA)),
                        _chip('Free: $freeCount/${spots.length}', const Color(0xFFDCFCE7), const Color(0xFF15803D)),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 8),
            const Text('Spots', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 8),
            Expanded(
              child: ListView.builder(
                itemCount: spots.length,
                itemBuilder: (context, index) {
                  final s = spots[index];
                  final color = s.status == 'free' ? const Color(0xFF16A34A) : const Color(0xFFF59E0B);
                  return Card(
                    child: ListTile(
                      title: Text(s.code),
                      subtitle: Text('Status: ${s.status}'),
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.14),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          s.status,
                          style: TextStyle(color: color, fontWeight: FontWeight.w700),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pushNamed(
                    context,
                    '/booking',
                    arguments: BookingScreenArgs(
                      parkingId: widget.parkingId,
                      spots: spots.where((e) => e.status == 'free').toList(),
                    ),
                  );
                },
                icon: const Icon(Icons.book_online_outlined),
                label: const Text('Book this parking'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _chip(String text, Color bg, Color fg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Text(text, style: TextStyle(color: fg, fontWeight: FontWeight.w700)),
    );
  }
}

