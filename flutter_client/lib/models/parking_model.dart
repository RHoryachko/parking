import 'tariff_model.dart';

class ParkingModel {
  final int id;
  final String name;
  final String city;
  final String address;
  final int capacity;
  final String workMode;
  final double latitude;
  final double longitude;
  final List<TariffModel>? tariffs;

  ParkingModel({
    required this.id,
    required this.name,
    required this.city,
    required this.address,
    required this.capacity,
    required this.workMode,
    required this.latitude,
    required this.longitude,
    this.tariffs,
  });

  factory ParkingModel.fromJson(Map<String, dynamic> json) {
    List<TariffModel>? t;
    final raw = json['tariffs'];
    if (raw is List) {
      t = raw.map((e) => TariffModel.fromJson(e as Map<String, dynamic>)).toList();
    }
    return ParkingModel(
      id: json['id'] as int,
      name: json['name'] as String,
      city: json['city'] as String,
      address: json['address'] as String,
      capacity: json['capacity'] as int,
      workMode: json['work_mode'] as String,
      latitude: (json['latitude'] as num?)?.toDouble() ?? 50.4501,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 30.5234,
      tariffs: t,
    );
  }
}
