class TariffModel {
  final int id;
  final String pricePerHour;

  TariffModel({required this.id, required this.pricePerHour});

  factory TariffModel.fromJson(Map<String, dynamic> json) {
    return TariffModel(
      id: json['id'] as int,
      pricePerHour: json['price_per_hour'].toString(),
    );
  }
}
