import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/booking_model.dart';
import '../models/parking_model.dart';
import '../models/spot_model.dart';
import '../models/tariff_model.dart';
import '../models/vehicle_model.dart';
import '../services/api_client.dart';
import '../services/client_service.dart';
import '../widgets/primary_button.dart';

class BookingScreenArgs {
  final int parkingId;
  final List<SpotModel> spots;

  BookingScreenArgs({required this.parkingId, required this.spots});
}

class BookingScreen extends StatefulWidget {
  final BookingScreenArgs args;
  const BookingScreen({super.key, required this.args});

  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  List<VehicleModel> vehicles = [];
  VehicleModel? selectedVehicle;
  SpotModel? selectedSpot;
  TariffModel? selectedTariff;
  ParkingModel? parking;
  bool loading = true;
  String? message;
  BookingModel? created;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final service = context.read<ClientService>();
    vehicles = await service.listVehicles();
    parking = await service.getParking(widget.args.parkingId);
    if (vehicles.isNotEmpty) selectedVehicle = vehicles.first;
    if (widget.args.spots.isNotEmpty) selectedSpot = widget.args.spots.first;
    final tariffs = parking?.tariffs;
    if (tariffs != null && tariffs.isNotEmpty) {
      selectedTariff = tariffs.first;
    }
    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));

    if (parking?.tariffs == null || parking!.tariffs!.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('Create booking')),
        body: const Center(child: Text('No tariffs for this parking. Add a tariff in admin.')),
      );
    }

    final mock = ApiClient.useMock;
    final hint = mock
        ? 'Create a booking, then pay instantly (mock).'
        : 'Create a booking, then pay with the test endpoint or open LiqPay checkout (configure keys on the server).';

    return Scaffold(
      appBar: AppBar(title: const Text('Create booking')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFDBEAFE), Color(0xFFEDE9FE)],
                ),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Text(
                hint,
                style: TextStyle(color: Colors.indigo.shade900, fontWeight: FontWeight.w600),
              ),
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    if (vehicles.isEmpty)
                      const Padding(
                        padding: EdgeInsets.only(bottom: 12),
                        child: Text('No vehicles found. Add one via API /client/vehicles.'),
                      ),
                    if (vehicles.isNotEmpty)
                      DropdownButtonFormField<VehicleModel>(
                        initialValue: selectedVehicle,
                        items: vehicles
                            .map((v) => DropdownMenuItem(value: v, child: Text(v.plateNumber)))
                            .toList(),
                        onChanged: (v) => setState(() => selectedVehicle = v),
                        decoration: const InputDecoration(labelText: 'Vehicle'),
                      ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<SpotModel>(
                      initialValue: selectedSpot,
                      items: widget.args.spots
                          .map((s) => DropdownMenuItem(value: s, child: Text('${s.code} (${s.status})')))
                          .toList(),
                      onChanged: (s) => setState(() => selectedSpot = s),
                      decoration: const InputDecoration(labelText: 'Spot'),
                    ),
                    if (parking?.tariffs != null && parking!.tariffs!.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      DropdownButtonFormField<TariffModel>(
                        initialValue: selectedTariff,
                        items: parking!.tariffs!
                            .map(
                              (t) => DropdownMenuItem(
                                value: t,
                                child: Text('${t.pricePerHour} UAH/h (#${t.id})'),
                              ),
                            )
                            .toList(),
                        onChanged: (t) => setState(() => selectedTariff = t),
                        decoration: const InputDecoration(labelText: 'Tariff'),
                      ),
                    ],
                    const SizedBox(height: 16),
                    PrimaryButton(
                      label: 'Create booking',
                      onPressed: created != null ||
                              selectedVehicle == null ||
                              selectedSpot == null ||
                              selectedTariff == null
                          ? null
                          : () async {
                              final service = context.read<ClientService>();
                              final start = DateTime.now().toUtc().add(const Duration(minutes: 5));
                              final end = start.add(const Duration(hours: 2));
                              try {
                                final booking = await service.createBooking(
                                  parkingId: widget.args.parkingId,
                                  spotId: selectedSpot!.id,
                                  vehicleId: selectedVehicle!.id,
                                  tariffId: selectedTariff!.id,
                                  start: start,
                                  end: end,
                                );
                                setState(() {
                                  created = booking;
                                  message = 'Booking #${booking.id} created. Choose payment.';
                                });
                              } catch (_) {
                                setState(() => message = 'Booking failed');
                              }
                            },
                    ),
                    if (created != null && created!.status == 'created') ...[
                      const SizedBox(height: 16),
                      PrimaryButton(
                        label: mock ? 'Pay (mock)' : 'Instant pay (test API)',
                        onPressed: () async {
                          final service = context.read<ClientService>();
                          try {
                            final paid = await service.payBooking(created!.id);
                            setState(() {
                              created = paid;
                              message = 'Paid: booking #${paid.id}';
                            });
                          } catch (_) {
                            setState(() => message = 'Payment failed');
                          }
                        },
                      ),
                      if (!mock) ...[
                        const SizedBox(height: 10),
                        PrimaryButton(
                          label: 'Pay with LiqPay (browser)',
                          onPressed: () async {
                            final service = context.read<ClientService>();
                            try {
                              final url = await service.liqpayCheckoutUrl(created!.id);
                              final uri = Uri.parse(url);
                              if (await canLaunchUrl(uri)) {
                                await launchUrl(uri, mode: LaunchMode.externalApplication);
                                setState(
                                  () => message =
                                      'Opened LiqPay. After payment completes, refresh “My bookings”.',
                                );
                              } else {
                                setState(() => message = 'Cannot open payment URL on this device.');
                              }
                            } catch (_) {
                              setState(() => message = 'LiqPay checkout failed (configure keys on server).');
                            }
                          },
                        ),
                      ],
                    ],
                  ],
                ),
              ),
            ),
            if (message != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: message!.contains('fail') || message!.contains('failed')
                      ? const Color(0xFFFEE2E2)
                      : const Color(0xFFDCFCE7),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(message!, style: const TextStyle(fontWeight: FontWeight.w700)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
