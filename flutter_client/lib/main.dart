import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_web_plugins/url_strategy.dart';

import 'app.dart';

String _initialLocation() {
  if (!kIsWeb) return '/';
  final path = Uri.base.path;
  if (path == '/payment-success' || path.endsWith('/payment-success')) {
    return '/payment-success';
  }
  return '/';
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  if (kIsWeb) {
    usePathUrlStrategy();
  }
  runApp(ParkingClientApp(initialRoute: _initialLocation()));
}
