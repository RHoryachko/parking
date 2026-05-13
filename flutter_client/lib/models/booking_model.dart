class BookingModel {
  final int id;
  final int parkingId;
  final int spotId;
  final int vehicleId;
  final int tariffId;
  final String plannedStartTime;
  final String plannedEndTime;
  final String status;

  BookingModel({
    required this.id,
    required this.parkingId,
    required this.spotId,
    required this.vehicleId,
    required this.tariffId,
    required this.plannedStartTime,
    required this.plannedEndTime,
    required this.status,
  });

  factory BookingModel.fromJson(Map<String, dynamic> json) {
    return BookingModel(
      id: json['id'] as int,
      parkingId: json['parking_id'] as int,
      spotId: json['spot_id'] as int,
      vehicleId: json['vehicle_id'] as int,
      tariffId: json['tariff_id'] as int,
      plannedStartTime: json['planned_start_time'] as String,
      plannedEndTime: json['planned_end_time'] as String,
      status: json['status'] as String,
    );
  }
}
