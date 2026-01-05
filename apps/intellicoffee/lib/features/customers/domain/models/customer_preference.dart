import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:equatable/equatable.dart';

class CustomerPreference extends Equatable {
  final String id;
  final String category; // coffee, food, service
  final String item;
  final int rating; // 1-5
  final String? notes;
  final DateTime updatedAt;

  const CustomerPreference({
    required this.id,
    required this.category,
    required this.item,
    required this.rating,
    this.notes,
    required this.updatedAt,
  });

  // Factory para criar uma nova preferência
  factory CustomerPreference.create({
    required String category,
    required String item,
    required int rating,
    String? notes,
  }) {
    return CustomerPreference(
      id: '', // Será gerado pelo Firestore
      category: category,
      item: item,
      rating: rating,
      notes: notes,
      updatedAt: DateTime.now(),
    );
  }

  // Factory para criar a partir do Firestore
  factory CustomerPreference.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return CustomerPreference(
      id: doc.id,
      category: data['category'] ?? '',
      item: data['item'] ?? '',
      rating: data['rating'] ?? 3,
      notes: data['notes'],
      updatedAt: (data['updatedAt'] as Timestamp).toDate(),
    );
  }

  // Converter para Map para salvar no Firestore
  Map<String, dynamic> toFirestore() {
    return {
      'category': category,
      'item': item,
      'rating': rating,
      'notes': notes,
      'updatedAt': Timestamp.fromDate(updatedAt),
    };
  }

  // Copiar com novos valores
  CustomerPreference copyWith({
    String? id,
    String? category,
    String? item,
    int? rating,
    String? notes,
    DateTime? updatedAt,
  }) {
    return CustomerPreference(
      id: id ?? this.id,
      category: category ?? this.category,
      item: item ?? this.item,
      rating: rating ?? this.rating,
      notes: notes ?? this.notes,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  List<Object?> get props => [
        id,
        category,
        item,
        rating,
        notes,
        updatedAt,
      ];
}