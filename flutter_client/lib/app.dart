import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'models/user_model.dart';
import 'screens/booking_screen.dart';
import 'screens/login_screen.dart';
import 'screens/my_bookings_screen.dart';
import 'screens/payment_success_screen.dart';
import 'screens/parking_details_screen.dart';
import 'screens/parking_list_screen.dart';
import 'screens/register_screen.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/client_service.dart';

class AuthController extends ChangeNotifier {
  final AuthService authService;
  UserModel? user;
  bool initialized = false;

  AuthController(this.authService);

  Future<void> init() async {
    await authService.restoreToken();
    try {
      user = await authService.me();
    } catch (_) {
      user = null;
    }
    initialized = true;
    notifyListeners();
  }

  Future<void> login(String email, String password) async {
    await authService.login(email: email, password: password);
    user = await authService.me();
    notifyListeners();
  }

  Future<void> register(String fullName, String email, String password) async {
    await authService.register(fullName: fullName, email: email, password: password);
  }

  Future<void> logout() async {
    await authService.logout();
    user = null;
    notifyListeners();
  }
}

class ParkingClientApp extends StatelessWidget {
  final String initialRoute;

  const ParkingClientApp({super.key, this.initialRoute = '/'});

  @override
  Widget build(BuildContext context) {
    final apiClient = ApiClient();
    final authService = AuthService(apiClient);
    final clientService = ClientService(apiClient);

    final theme = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF4F46E5),
        brightness: Brightness.light,
      ),
      scaffoldBackgroundColor: const Color(0xFFF5F7FB),
      textTheme: const TextTheme(
        headlineMedium: TextStyle(fontWeight: FontWeight.w800, letterSpacing: -0.5),
        titleLarge: TextStyle(fontWeight: FontWeight.w700),
        titleMedium: TextStyle(fontWeight: FontWeight.w700),
        bodyMedium: TextStyle(height: 1.35),
      ),
      appBarTheme: const AppBarTheme(
        centerTitle: false,
        backgroundColor: Colors.transparent,
        elevation: 0,
        surfaceTintColor: Colors.transparent,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0xFF4F46E5), width: 1.4),
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: Colors.white,
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: Color(0xFFE5E7EB)),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          textStyle: const TextStyle(fontWeight: FontWeight.w700),
          elevation: 0,
        ),
      ),
    );

    return MultiProvider(
      providers: [
        Provider.value(value: authService),
        Provider.value(value: clientService),
        ChangeNotifierProvider(create: (_) => AuthController(authService)..init()),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'Parking Client',
        theme: theme,
        initialRoute: initialRoute,
        routes: {
          '/': (_) => const AuthGate(),
          '/login': (_) => const LoginScreen(),
          '/register': (_) => const RegisterScreen(),
          '/parkings': (_) => const ParkingListScreen(),
          '/my-bookings': (_) => const MyBookingsScreen(),
          '/payment-success': (_) => const PaymentSuccessScreen(),
        },
        onGenerateRoute: (settings) {
          if (settings.name == '/parking-details') {
            final parkingId = settings.arguments as int;
            return MaterialPageRoute(builder: (_) => ParkingDetailsScreen(parkingId: parkingId));
          }
          if (settings.name == '/booking') {
            final args = settings.arguments as BookingScreenArgs;
            return MaterialPageRoute(builder: (_) => BookingScreen(args: args));
          }
          return null;
        },
      ),
    );
  }
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthController>();
    if (!auth.initialized) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (auth.user == null) {
      return const LoginScreen();
    }
    return const ParkingListScreen();
  }
}

