import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';

/// Thanks page after LiqPay (`/payment-success?booking_id=…`). Default `result_url` from the API uses this route.
class PaymentSuccessScreen extends StatelessWidget {
  const PaymentSuccessScreen({super.key});

  int? _bookingId() {
    if (!kIsWeb) return null;
    final raw = Uri.base.queryParameters['booking_id'];
    if (raw == null || raw.isEmpty) return null;
    return int.tryParse(raw);
  }

  @override
  Widget build(BuildContext context) {
    final id = _bookingId();

    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFFEEF2FF),
              Color(0xFFF8FAFC),
              Color(0xFFECFDF5),
            ],
            stops: [0.0, 0.45, 1.0],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Card(
                margin: const EdgeInsets.symmetric(horizontal: 20),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(18),
                  side: const BorderSide(color: Color(0xFFE2E8F0)),
                ),
                elevation: 0,
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(28, 28, 28, 24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.check_circle, color: Colors.green.shade800, size: 22),
                          const SizedBox(width: 8),
                          Text(
                            'Оплату прийнято',
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              color: Colors.green.shade800,
                              fontSize: 15,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Text(
                        'Замовлення оплачене',
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.w800,
                              letterSpacing: -0.5,
                              color: const Color(0xFF0F172A),
                            ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Дякуємо! Платіж у LiqPay оброблено. Бронювання зʼявиться як оплачене у вашому застосунку.',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: const Color(0xFF334155),
                              height: 1.5,
                            ),
                      ),
                      if (id != null) ...[
                        const SizedBox(height: 12),
                        Text.rich(
                          TextSpan(
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: const Color(0xFF64748B),
                                ),
                            children: [
                              const TextSpan(text: 'Номер бронювання: '),
                              TextSpan(
                                text: '#$id',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w800,
                                  color: Color(0xFF0F172A),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(height: 16),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF1F5F9),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          'Якщо статус ще не оновився — зачекайте кілька секунд (сервер отримує підтвердження окремо), потім відкрийте «Мої бронювання» у застосунку або оновіть список.',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: const Color(0xFF475569),
                                height: 1.45,
                              ),
                        ),
                      ),
                      const SizedBox(height: 18),
                      Text(
                        'Можете закрити цю вкладку або перейти до списку бронювань.',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: const Color(0xFF64748B),
                            ),
                      ),
                      const SizedBox(height: 20),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () {
                                Navigator.of(context).pushNamedAndRemoveUntil('/', (r) => false);
                              },
                              child: const Text('На головну'),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: FilledButton(
                              onPressed: () {
                                Navigator.of(context).pushNamedAndRemoveUntil(
                                  '/my-bookings',
                                  (r) => false,
                                );
                              },
                              child: const Text('Мої бронювання'),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
