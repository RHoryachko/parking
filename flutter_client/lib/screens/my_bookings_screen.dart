import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/booking_model.dart';
import '../services/client_service.dart';

class MyBookingsScreen extends StatefulWidget {
  const MyBookingsScreen({super.key});

  @override
  State<MyBookingsScreen> createState() => _MyBookingsScreenState();
}

class _MyBookingsScreenState extends State<MyBookingsScreen> {
  late Future<List<BookingModel>> _future;

  @override
  void initState() {
    super.initState();
    _future = context.read<ClientService>().bookingHistory();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My bookings')),
      body: FutureBuilder<List<BookingModel>>(
        future: _future,
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final items = snapshot.data!;
          if (items.isEmpty) return const Center(child: Text('No bookings yet'));
          return ListView(
            padding: const EdgeInsets.only(top: 6, bottom: 12),
            children: [
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFE0E7FF), Color(0xFFF3E8FF)],
                  ),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  'History: ${items.length} bookings',
                  style: const TextStyle(fontWeight: FontWeight.w700, color: Color(0xFF312E81)),
                ),
              ),
              const SizedBox(height: 8),
              ...items.map((b) {
                final statusColor = b.status == 'paid' ? const Color(0xFF16A34A) : const Color(0xFF6B7280);
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                'Booking #${b.id}',
                                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: statusColor.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Text(b.status, style: TextStyle(color: statusColor, fontWeight: FontWeight.w700)),
                            )
                          ],
                        ),
                        const SizedBox(height: 10),
                        Text('Parking ${b.parkingId} • Spot ${b.spotId} • Vehicle ${b.vehicleId}'),
                        const SizedBox(height: 6),
                        Text('${b.plannedStartTime} -> ${b.plannedEndTime}', style: const TextStyle(color: Color(0xFF6B7280))),
                      ],
                    ),
                  ),
                );
              }),
            ],
          );
        },
      ),
    );
  }
}

