import '../models/user_model.dart';
import '../models/booking_model.dart';
import '../models/parking_model.dart';
import '../models/spot_model.dart';
import '../models/tariff_model.dart';
import '../models/vehicle_model.dart';
import 'api_client.dart';

class ClientService {
  final ApiClient _apiClient;
  static final List<BookingModel> _mockBookings = [];
  static final List<VehicleModel> _mockVehicles = [
    VehicleModel(id: 1, plateNumber: 'AA1234BC', brand: 'Tesla', model: 'Model 3', color: 'White'),
    VehicleModel(id: 2, plateNumber: 'KA7777KK', brand: 'BMW', model: 'X5', color: 'Black'),
  ];
  static final List<ParkingModel> _mockParkings = [
    ParkingModel(
      id: 1,
      name: 'Skyline Center',
      city: 'Kyiv',
      address: 'Khreshchatyk 10',
      capacity: 120,
      workMode: 'ai',
      latitude: 50.4474,
      longitude: 30.5226,
      tariffs: [TariffModel(id: 1, pricePerHour: '50.00')],
    ),
    ParkingModel(
      id: 2,
      name: 'River Mall',
      city: 'Kyiv',
      address: 'Dnipro Embankment 1',
      capacity: 90,
      workMode: 'manual',
      latitude: 50.4280,
      longitude: 30.5670,
      tariffs: [TariffModel(id: 2, pricePerHour: '45.00')],
    ),
    ParkingModel(
      id: 3,
      name: 'Lviv Plaza',
      city: 'Lviv',
      address: 'Svobody Ave 18',
      capacity: 80,
      workMode: 'manual',
      latitude: 49.8420,
      longitude: 24.0316,
      tariffs: [TariffModel(id: 3, pricePerHour: '40.00')],
    ),
  ];

  ClientService(this._apiClient);

  Future<List<ParkingModel>> listParkings({String? city}) async {
    if (ApiClient.useMock) {
      await Future<void>.delayed(const Duration(milliseconds: 220));
      if (city == null || city.isEmpty) return _mockParkings;
      return _mockParkings.where((p) => p.city.toLowerCase() == city.toLowerCase()).toList();
    }
    final response = await _apiClient.dio.get(
      '/client/parkings',
      queryParameters: city == null ? null : {'city': city},
    );
    return (response.data as List)
        .map((e) => ParkingModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ParkingModel> getParking(int parkingId) async {
    if (ApiClient.useMock) {
      await Future<void>.delayed(const Duration(milliseconds: 150));
      return _mockParkings.firstWhere((p) => p.id == parkingId);
    }
    final response = await _apiClient.dio.get('/client/parkings/$parkingId');
    return ParkingModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<SpotModel>> listSpots(int parkingId) async {
    if (ApiClient.useMock) {
      await Future<void>.delayed(const Duration(milliseconds: 180));
      return List.generate(24, (index) {
        final n = index + 1;
        final status = n % 7 == 0
            ? 'occupied'
            : (n % 5 == 0 ? 'reserved' : (n % 11 == 0 ? 'inactive' : 'free'));
        return SpotModel(
          id: parkingId * 100 + n,
          parkingId: parkingId,
          code: 'A$n',
          status: status,
        );
      });
    }
    final response = await _apiClient.dio.get('/client/parkings/$parkingId/spots');
    return (response.data as List)
        .map((e) => SpotModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<UserModel> updateProfile({
    required UserModel current,
    required String fullName,
    required String phoneRaw,
  }) async {
    if (ApiClient.useMock) {
      await Future<void>.delayed(const Duration(milliseconds: 120));
      final t = phoneRaw.trim();
      return UserModel(
        id: current.id,
        fullName: fullName.trim(),
        email: current.email,
        role: current.role,
        phone: t.isEmpty ? null : t,
        isBlocked: current.isBlocked,
        createdAt: current.createdAt,
      );
    }
    final t = phoneRaw.trim();
    final response = await _apiClient.dio.patch(
      '/client/me',
      data: {
        'full_name': fullName.trim(),
        'phone': t.isEmpty ? '' : t,
      },
    );
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<VehicleModel>> listVehicles() async {
    if (ApiClient.useMock) {
      await Future<void>.delayed(const Duration(milliseconds: 120));
      return _mockVehicles;
    }
    final response = await _apiClient.dio.get('/client/vehicles');
    return (response.data as List)
        .map((e) => VehicleModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<VehicleModel> createVehicle({
    required String plateNumber,
    String? brand,
    String? model,
    String? color,
  }) async {
    if (ApiClient.useMock) {
      final vehicle = VehicleModel(
        id: _mockVehicles.length + 1,
        plateNumber: plateNumber.toUpperCase(),
        brand: brand,
        model: model,
        color: color,
      );
      _mockVehicles.add(vehicle);
      return vehicle;
    }
    final response = await _apiClient.dio.post(
      '/client/vehicles',
      data: {
        'plate_number': plateNumber,
        'brand': brand,
        'model': model,
        'color': color,
      },
    );
    return VehicleModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<VehicleModel> updateVehicle(
    int vehicleId, {
    required String plateNumber,
    String? brand,
    String? model,
    String? color,
  }) async {
    if (ApiClient.useMock) {
      await Future<void>.delayed(const Duration(milliseconds: 100));
      final idx = _mockVehicles.indexWhere((v) => v.id == vehicleId);
      if (idx == -1) throw Exception('Vehicle not found');
      final updated = VehicleModel(
        id: vehicleId,
        plateNumber: plateNumber.toUpperCase(),
        brand: brand,
        model: model,
        color: color,
      );
      _mockVehicles[idx] = updated;
      return updated;
    }
    final response = await _apiClient.dio.patch(
      '/client/vehicles/$vehicleId',
      data: {
        'plate_number': plateNumber,
        'brand': brand,
        'model': model,
        'color': color,
      },
    );
    return VehicleModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteVehicle(int vehicleId) async {
    if (ApiClient.useMock) {
      _mockVehicles.removeWhere((v) => v.id == vehicleId);
      await Future<void>.delayed(const Duration(milliseconds: 80));
      return;
    }
    await _apiClient.dio.delete('/client/vehicles/$vehicleId');
  }

  Future<BookingModel> createBooking({
    required int parkingId,
    required int spotId,
    required int vehicleId,
    required int tariffId,
    required DateTime start,
    required DateTime end,
  }) async {
    if (ApiClient.useMock) {
      final booking = BookingModel(
        id: _mockBookings.length + 1,
        parkingId: parkingId,
        spotId: spotId,
        vehicleId: vehicleId,
        tariffId: tariffId,
        plannedStartTime: start.toUtc().toIso8601String(),
        plannedEndTime: end.toUtc().toIso8601String(),
        status: 'created',
      );
      _mockBookings.insert(0, booking);
      return booking;
    }
    final response = await _apiClient.dio.post(
      '/client/bookings',
      data: {
        'parking_id': parkingId,
        'spot_id': spotId,
        'vehicle_id': vehicleId,
        'tariff_id': tariffId,
        'planned_start_time': start.toUtc().toIso8601String(),
        'planned_end_time': end.toUtc().toIso8601String(),
      },
    );
    return BookingModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<BookingModel> payBooking(int bookingId) async {
    if (ApiClient.useMock) {
      final idx = _mockBookings.indexWhere((b) => b.id == bookingId);
      if (idx == -1) {
        throw Exception('Mock booking not found');
      }
      final b = _mockBookings[idx];
      final paid = BookingModel(
        id: b.id,
        parkingId: b.parkingId,
        spotId: b.spotId,
        vehicleId: b.vehicleId,
        tariffId: b.tariffId,
        plannedStartTime: b.plannedStartTime,
        plannedEndTime: b.plannedEndTime,
        status: 'paid',
      );
      _mockBookings[idx] = paid;
      return paid;
    }
    final response = await _apiClient.dio.post('/client/bookings/$bookingId/pay');
    return BookingModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<String> liqpayCheckoutUrl(int bookingId) async {
    if (ApiClient.useMock) {
      throw StateError('LiqPay is not used when USE_MOCK=true');
    }
    final response = await _apiClient.dio.post('/client/bookings/$bookingId/liqpay-checkout');
    final data = response.data;
    if (data == null || data['checkout_url'] == null) {
      throw StateError('Invalid LiqPay checkout response');
    }
    return data['checkout_url'] as String;
  }

  Future<BookingModel> cancelBooking(int bookingId) async {
    if (ApiClient.useMock) {
      await Future<void>.delayed(const Duration(milliseconds: 80));
      final idx = _mockBookings.indexWhere((b) => b.id == bookingId);
      if (idx == -1) throw Exception('Booking not found');
      final b = _mockBookings[idx];
      final updated = BookingModel(
        id: b.id,
        parkingId: b.parkingId,
        spotId: b.spotId,
        vehicleId: b.vehicleId,
        tariffId: b.tariffId,
        plannedStartTime: b.plannedStartTime,
        plannedEndTime: b.plannedEndTime,
        status: 'canceled',
      );
      _mockBookings[idx] = updated;
      return updated;
    }
    final response = await _apiClient.dio.post('/client/bookings/$bookingId/cancel');
    return BookingModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<BookingModel>> bookingHistory() async {
    if (ApiClient.useMock) {
      await Future<void>.delayed(const Duration(milliseconds: 120));
      if (_mockBookings.isEmpty) {
        _mockBookings.addAll([
          BookingModel(
            id: 9001,
            parkingId: 1,
            spotId: 101,
            vehicleId: 1,
            tariffId: 1,
            plannedStartTime: DateTime.now().subtract(const Duration(days: 1)).toUtc().toIso8601String(),
            plannedEndTime: DateTime.now().subtract(const Duration(days: 1, hours: -2)).toUtc().toIso8601String(),
            status: 'paid',
          ),
        ]);
      }
      return _mockBookings;
    }
    final response = await _apiClient.dio.get('/client/bookings');
    return (response.data as List)
        .map((e) => BookingModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
