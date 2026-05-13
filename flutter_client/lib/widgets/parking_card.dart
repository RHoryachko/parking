import 'package:flutter/material.dart';

import '../models/parking_model.dart';

class ParkingCard extends StatelessWidget {
  final ParkingModel parking;
  final VoidCallback onTap;

  const ParkingCard({super.key, required this.parking, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final modeColor = parking.workMode == 'ai' ? const Color(0xFF4F46E5) : const Color(0xFF0EA5E9);
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [modeColor.withValues(alpha: 0.18), modeColor.withValues(alpha: 0.08)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.local_parking_rounded, color: modeColor),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(parking.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 4),
                    Text('${parking.city}, ${parking.address}', style: const TextStyle(color: Color(0xFF6B7280))),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        _chip('Capacity ${parking.capacity}', const Color(0xFFF3F4F6), const Color(0xFF374151)),
                        _chip(parking.workMode.toUpperCase(), modeColor.withValues(alpha: 0.12), modeColor),
                      ],
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
      ),
    );
  }

  Widget _chip(String text, Color bg, Color fg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Text(text, style: TextStyle(color: fg, fontWeight: FontWeight.w700, fontSize: 12)),
    );
  }
}

