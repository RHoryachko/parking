class SpotModel {
  final int id;
  final int parkingId;
  final String code;
  final String status;

  SpotModel({
    required this.id,
    required this.parkingId,
    required this.code,
    required this.status,
  });

  factory SpotModel.fromJson(Map<String, dynamic> json) {
    return SpotModel(
      id: json['id'] as int,
      parkingId: json['parking_id'] as int,
      code: json['code'] as String,
      status: json['status'] as String,
    );
  }
}
