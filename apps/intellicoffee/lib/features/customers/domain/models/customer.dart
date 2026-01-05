import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:equatable/equatable.dart';

class Customer extends Equatable {
  final String id;
  final String name;
  final String phone;
  final String? email;
  final DateTime? birthDate;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? lastVisit;
  final int visitCount;
  final double totalSpent;
  final double averageTicket;
  final int loyaltyPoints;
  final String tier; // regular, bronze, silver, gold
  final String? notes;
  final List<String> tags;
  final bool allowsMarketing;
  final String? source;
  final String status; // active, inactive

  const Customer({
    required this.id,
    required this.name,
    required this.phone,
    this.email,
    this.birthDate,
    required this.createdAt,
    required this.updatedAt,
    this.lastVisit,
    required this.visitCount,
    required this.totalSpent,
    required this.averageTicket,
    required this.loyaltyPoints,
    required this.tier,
    this.notes,
    required this.tags,
    required this.allowsMarketing,
    this.source,
    required this.status,
  });

  // Factory para criar um novo cliente com valores padrão
  factory Customer.create({
    required String name,
    required String phone,
    String? email,
    DateTime? birthDate,
    String? notes,
    List<String>? tags,
    bool? allowsMarketing,
    String? source,
  }) {
    final now = DateTime.now();
    return Customer(
      id: '', // Será gerado pelo Firestore
      name: name,
      phone: phone,
      email: email,
      birthDate: birthDate,
      createdAt: now,
      updatedAt: now,
      lastVisit: now,
      visitCount: 1,
      totalSpent: 0,
      averageTicket: 0,
      loyaltyPoints: 0,
      tier: 'regular',
      notes: notes,
      tags: tags ?? [],
      allowsMarketing: allowsMarketing ?? true,
      source: source,
      status: 'active',
    );
  }

  // Factory para criar a partir do Firestore
  factory Customer.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return Customer(
      id: doc.id,
      name: data['name'] ?? '',
      phone: data['phone'] ?? '',
      email: data['email'],
      birthDate: data['birthDate'] != null 
          ? (data['birthDate'] as Timestamp).toDate()
          : null,
      createdAt: (data['createdAt'] as Timestamp).toDate(),
      updatedAt: (data['updatedAt'] as Timestamp).toDate(),
      lastVisit: data['lastVisit'] != null 
          ? (data['lastVisit'] as Timestamp).toDate()
          : null,
      visitCount: data['visitCount'] ?? 0,
      totalSpent: (data['totalSpent'] ?? 0).toDouble(),
      averageTicket: (data['averageTicket'] ?? 0).toDouble(),
      loyaltyPoints: data['loyaltyPoints'] ?? 0,
      tier: data['tier'] ?? 'regular',
      notes: data['notes'],
      tags: List<String>.from(data['tags'] ?? []),
      allowsMarketing: data['allowsMarketing'] ?? false,
      source: data['source'],
      status: data['status'] ?? 'active',
    );
  }

  // Converter para Map para salvar no Firestore
  Map<String, dynamic> toFirestore() {
    return {
      'name': name,
      'phone': phone,
      'email': email,
      'birthDate': birthDate != null ? Timestamp.fromDate(birthDate!) : null,
      'createdAt': Timestamp.fromDate(createdAt),
      'updatedAt': Timestamp.fromDate(updatedAt),
      'lastVisit': lastVisit != null ? Timestamp.fromDate(lastVisit!) : null,
      'visitCount': visitCount,
      'totalSpent': totalSpent,
      'averageTicket': averageTicket,
      'loyaltyPoints': loyaltyPoints,
      'tier': tier,
      'notes': notes,
      'tags': tags,
      'allowsMarketing': allowsMarketing,
      'source': source,
      'status': status,
    };
  }

  // Copiar com novos valores
  Customer copyWith({
    String? id,
    String? name,
    String? phone,
    String? email,
    DateTime? birthDate,
    DateTime? createdAt,
    DateTime? updatedAt,
    DateTime? lastVisit,
    int? visitCount,
    double? totalSpent,
    double? averageTicket,
    int? loyaltyPoints,
    String? tier,
    String? notes,
    List<String>? tags,
    bool? allowsMarketing,
    String? source,
    String? status,
  }) {
    return Customer(
      id: id ?? this.id,
      name: name ?? this.name,
      phone: phone ?? this.phone,
      email: email ?? this.email,
      birthDate: birthDate ?? this.birthDate,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      lastVisit: lastVisit ?? this.lastVisit,
      visitCount: visitCount ?? this.visitCount,
      totalSpent: totalSpent ?? this.totalSpent,
      averageTicket: averageTicket ?? this.averageTicket,
      loyaltyPoints: loyaltyPoints ?? this.loyaltyPoints,
      tier: tier ?? this.tier,
      notes: notes ?? this.notes,
      tags: tags ?? this.tags,
      allowsMarketing: allowsMarketing ?? this.allowsMarketing,
      source: source ?? this.source,
      status: status ?? this.status,
    );
  }

  @override
  List<Object?> get props => [
        id,
        name,
        phone,
        email,
        birthDate,
        createdAt,
        updatedAt,
        lastVisit,
        visitCount,
        totalSpent,
        averageTicket,
        loyaltyPoints,
        tier,
        notes,
        tags,
        allowsMarketing,
        source,
        status,
      ];
}