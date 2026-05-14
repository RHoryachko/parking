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

  late DateTime plannedStart;
  late DateTime plannedEnd;

  @override
  void initState() {
    super.initState();
    _init();
  }

  DateTime _defaultStartLocal() {
    final n = DateTime.now();
    var s = DateTime(n.year, n.month, n.day, n.hour + 1, 0);
    if (!s.isAfter(n.add(const Duration(minutes: 10)))) {
      s = s.add(const Duration(hours: 1));
    }
    return s;
  }

  String _formatLocal(DateTime dt) {
    final d = dt;
    return '${d.day.toString().padLeft(2, '0')}.${d.month.toString().padLeft(2, '0')}.${d.year} '
        '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
  }

  String? _timeRangeError() {
    if (!plannedEnd.isAfter(plannedStart)) {
      return 'Кінець має бути пізніше за початок';
    }
    if (plannedStart.isBefore(DateTime.now().subtract(const Duration(minutes: 1)))) {
      return 'Початок не може бути в минулому';
    }
    return null;
  }

  Future<DateTime?> _pickDateTime(BuildContext context, DateTime initial) async {
    final d = await showDatePicker(
      context: context,
      initialDate: DateTime(initial.year, initial.month, initial.day),
      firstDate: DateTime.now().subtract(const Duration(days: 1)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (d == null || !context.mounted) return null;
    final t = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(hour: initial.hour, minute: initial.minute),
    );
    if (t == null || !context.mounted) return null;
    return DateTime(d.year, d.month, d.day, t.hour, t.minute);
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
    plannedStart = _defaultStartLocal();
    plannedEnd = plannedStart.add(const Duration(hours: 2));
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

    return Scaffold(
      appBar: AppBar(title: const Text('Create booking')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
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
                    if (selectedTariff != null) ...[
                      const SizedBox(height: 12),
                      InputDecorator(
                        decoration: const InputDecoration(
                          labelText: 'Tariff',
                          filled: true,
                          fillColor: Color(0xFFF1F5F9),
                        ),
                        child: Text(
                          '${selectedTariff!.pricePerHour} UAH/h (#${selectedTariff!.id})',
                          style: const TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF0F172A)),
                        ),
                      ),
                    ],
                    const SizedBox(height: 8),
                    const Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        'Час броню',
                        style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: Color(0xFF475569)),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(14),
                        onTap: created != null
                            ? null
                            : () async {
                                final v = await _pickDateTime(context, plannedStart);
                                if (v != null) setState(() => plannedStart = v);
                              },
                        child: InputDecorator(
                          decoration: const InputDecoration(
                            labelText: 'Початок',
                            suffixIcon: Icon(Icons.calendar_today_outlined, size: 20),
                          ),
                          child: Text(_formatLocal(plannedStart), style: const TextStyle(fontWeight: FontWeight.w600)),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(14),
                        onTap: created != null
                            ? null
                            : () async {
                                final v = await _pickDateTime(context, plannedEnd);
                                if (v != null) setState(() => plannedEnd = v);
                              },
                        child: InputDecorator(
                          decoration: const InputDecoration(
                            labelText: 'Кінець',
                            suffixIcon: Icon(Icons.schedule_outlined, size: 20),
                          ),
                          child: Text(_formatLocal(plannedEnd), style: const TextStyle(fontWeight: FontWeight.w600)),
                        ),
                      ),
                    ),
                    if (_timeRangeError() != null && created == null) ...[
                      const SizedBox(height: 8),
                      Text(
                        _timeRangeError()!,
                        style: const TextStyle(color: Color(0xFFB91C1C), fontSize: 13, fontWeight: FontWeight.w600),
                      ),
                    ],
                    const SizedBox(height: 16),
                    PrimaryButton(
                      label: 'Create booking',
                      onPressed: created != null ||
                              selectedVehicle == null ||
                              selectedSpot == null ||
                              selectedTariff == null ||
                              _timeRangeError() != null
                          ? null
                          : () async {
                              final service = context.read<ClientService>();
                              final start = plannedStart;
                              final end = plannedEnd;
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
                      if (ApiClient.useMock)
                        PrimaryButton(
                          label: 'Pay (mock)',
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
                        )
                      else ...[
                        PrimaryButton(
                          label: 'Оплатити через LiqPay (браузер)',
                          onPressed: () async {
                            final service = context.read<ClientService>();
                            try {
                              final url = await service.liqpayCheckoutUrl(created!.id);
                              final uri = Uri.parse(url);
                              if (await canLaunchUrl(uri)) {
                                await launchUrl(uri, mode: LaunchMode.externalApplication);
                                setState(
                                  () => message =
                                      'Відкрито LiqPay. Після оплати карткою оновіть «Мої бронювання» — статус зміниться, коли банк підтвердить платіж.',
                                );
                              } else {
                                setState(() => message = 'Не вдалося відкрити посилання LiqPay.');
                              }
                            } catch (_) {
                              setState(
                                () => message =
                                    'LiqPay недоступний (ключі на сервері). Спробуйте «Миттєва оплата» або оплату на місці.',
                              );
                            }
                          },
                        ),
                        const SizedBox(height: 10),
                        TextButton(
                          onPressed: () async {
                            final service = context.read<ClientService>();
                            try {
                              final paid = await service.payBooking(created!.id);
                              setState(() {
                                created = paid;
                                message = 'Оплачено в застосунку. Бронювання #${paid.id}.';
                              });
                            } catch (_) {
                              setState(() => message = 'Миттєва оплата не вдалася.');
                            }
                          },
                          child: const Text('Миттєва оплата (без картки в LiqPay)'),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Якщо на LiqPay зʼявляється «помилка транзакції», часто причина в тому, що сервер API недоступний з інтернету для callback (localhost). Тоді використайте ngrok для APP_PUBLIC_API_URL або миттєву оплату.',
                          style: TextStyle(
                            fontSize: 11,
                            height: 1.35,
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
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
