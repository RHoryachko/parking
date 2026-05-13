class VehicleModel {
  final int id;
  final String plateNumber;
  final String? brand;
  final String? model;
  final String? color;

  VehicleModel({
    required this.id,
    required this.plateNumber,
    this.brand,
    this.model,
    this.color,
  });

  factory VehicleModel.fromJson(Map<String, dynamic> json) {
    return VehicleModel(
      id: json['id'] as int,
      plateNumber: json['plate_number'] as String,
      brand: json['brand'] as String?,
      model: json['model'] as String?,
      color: json['color'] as String?,
    );
  }
}
