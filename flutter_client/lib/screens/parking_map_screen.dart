import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/parking_model.dart';

/// OSM map of parkings (same tile source as admin Leaflet).
class ParkingMapScreen extends StatelessWidget {
  final List<ParkingModel> parkings;

  const ParkingMapScreen({super.key, required this.parkings});

  LatLng _center() {
    if (parkings.isEmpty) return const LatLng(50.4501, 30.5234);
    final lat = parkings.map((p) => p.latitude).reduce((a, b) => a + b) / parkings.length;
    final lng = parkings.map((p) => p.longitude).reduce((a, b) => a + b) / parkings.length;
    return LatLng(lat, lng);
  }

  @override
  Widget build(BuildContext context) {
    final center = _center();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Карта паркінгів'),
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Text(
              '${parkings.length} майданчиків на карті (OpenStreetMap)',
              style: TextStyle(fontSize: 13, color: Colors.grey.shade700, fontWeight: FontWeight.w600),
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
              child: FlutterMap(
                options: MapOptions(
                  initialCenter: center,
                  initialZoom: parkings.length <= 1 ? 14.0 : 11.0,
                  minZoom: 4,
                  maxZoom: 18,
                  interactionOptions: const InteractionOptions(
                    flags: InteractiveFlag.all,
                  ),
                ),
                children: [
                  TileLayer(
                    urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    userAgentPackageName: 'com.parking.flutter_client',
                  ),
                  MarkerLayer(
                    markers: [
                      for (final p in parkings)
                        Marker(
                          point: LatLng(p.latitude, p.longitude),
                          width: 48,
                          height: 48,
                          alignment: Alignment.bottomCenter,
                          child: IconButton(
                            padding: EdgeInsets.zero,
                            icon: const Icon(Icons.location_on, color: Color(0xFF4338CA), size: 44),
                            onPressed: () => _showParkingSheet(context, p),
                          ),
                        ),
                    ],
                  ),
                  RichAttributionWidget(
                    attributions: [
                      TextSourceAttribution(
                        '© OpenStreetMap',
                        onTap: () async {
                          final u = Uri.parse('https://www.openstreetmap.org/copyright');
                          if (await canLaunchUrl(u)) await launchUrl(u, mode: LaunchMode.externalApplication);
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showParkingSheet(BuildContext context, ParkingModel p) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(p.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            Text('${p.city} · ${p.address}', style: TextStyle(color: Colors.grey.shade700, height: 1.35)),
            const SizedBox(height: 4),
            Text(
              'Режим: ${p.workMode} · Місць: ${p.capacity}',
              style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.pushNamed(context, '/parking-details', arguments: p.id);
                },
                child: const Text('Деталі паркінгу'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
