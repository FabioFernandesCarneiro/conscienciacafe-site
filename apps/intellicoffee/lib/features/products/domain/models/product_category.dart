import 'package:cloud_firestore/cloud_firestore.dart';

/// Enumeração para tipos de produtos
enum ProductType {
  coffee,     // Grãos de café torrados
  beverage,   // Cafés preparados e bebidas
  food,       // Itens alimentícios
  accessory,  // Equipamentos e produtos para preparo
  book,       // Livros
  ingredient  // Ingredientes para personalização
}

/// Enumeração para tipos de campos customizados
enum FieldType {
  text,      // Campo de texto
  boolean,   // Campo booleano (verdadeiro/falso)
  number,    // Campo numérico
  decimal,   // Campo decimal/financeiro
  selection, // Seleção de opções predefinidas
  date       // Campo de data
}

/// Extensão para converter ProductType para String
extension ProductTypeExtension on ProductType {
  String get displayName {
    switch (this) {
      case ProductType.coffee:
        return 'Café';
      case ProductType.beverage:
        return 'Bebida';
      case ProductType.food:
        return 'Comida';
      case ProductType.accessory:
        return 'Acessório';
      case ProductType.book:
        return 'Livro';
      case ProductType.ingredient:
        return 'Ingrediente';
    }
  }
  
  /// Método para obter a cor associada ao tipo
  int get color {
    switch (this) {
      case ProductType.coffee:
        return 0xFFF57C00; // Âmbar
      case ProductType.beverage:
        return 0xFF2196F3; // Azul
      case ProductType.food:
        return 0xFF9C27B0; // Roxo
      case ProductType.accessory:
        return 0xFF607D8B; // Cinza azulado
      case ProductType.book:
        return 0xFF795548; // Marrom
      case ProductType.ingredient:
        return 0xFF4CAF50; // Verde
    }
  }
}

/// Extensão para converter FieldType para String
extension FieldTypeExtension on FieldType {
  String get displayName {
    switch (this) {
      case FieldType.text:
        return 'Texto';
      case FieldType.boolean:
        return 'Sim/Não';
      case FieldType.number:
        return 'Número';
      case FieldType.decimal:
        return 'Decimal';
      case FieldType.selection:
        return 'Seleção';
      case FieldType.date:
        return 'Data';
    }
  }
}

/// Modelo para campo personalizado
class CustomField {
  final String id;
  final String name;
  final String description;
  final bool isRequired;
  final FieldType fieldType;
  final List<String> options;
  final dynamic defaultValue;
  final String? validation;
  final int order;
  final bool isSearchable;
  final bool isDisplayedInList;

  CustomField({
    required this.id,
    required this.name,
    required this.description,
    required this.isRequired,
    required this.fieldType,
    required this.options,
    this.defaultValue,
    this.validation,
    required this.order,
    required this.isSearchable,
    required this.isDisplayedInList,
  });

  /// Cria uma cópia do objeto com os campos atualizados
  CustomField copyWith({
    String? id,
    String? name,
    String? description,
    bool? isRequired,
    FieldType? fieldType,
    List<String>? options,
    dynamic defaultValue,
    String? validation,
    int? order,
    bool? isSearchable,
    bool? isDisplayedInList,
  }) {
    return CustomField(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      isRequired: isRequired ?? this.isRequired,
      fieldType: fieldType ?? this.fieldType,
      options: options ?? this.options,
      defaultValue: defaultValue ?? this.defaultValue,
      validation: validation ?? this.validation,
      order: order ?? this.order,
      isSearchable: isSearchable ?? this.isSearchable,
      isDisplayedInList: isDisplayedInList ?? this.isDisplayedInList,
    );
  }

  /// Factory para criar um CustomField a partir de um mapa (Firestore)
  factory CustomField.fromMap(Map<String, dynamic> map, {String? id}) {
    return CustomField(
      id: id ?? map['id'] ?? '',
      name: map['name'] ?? '',
      description: map['description'] ?? '',
      isRequired: map['isRequired'] ?? false,
      fieldType: _parseFieldType(map['fieldType']),
      options: List<String>.from(map['options'] ?? []),
      defaultValue: map['defaultValue'],
      validation: map['validation'],
      order: map['order'] ?? 0,
      isSearchable: map['isSearchable'] ?? false,
      isDisplayedInList: map['isDisplayedInList'] ?? false,
    );
  }

  /// Converte o objeto para um Map
  Map<String, dynamic> toMap() {
    return {
      'name': name,
      'description': description,
      'isRequired': isRequired,
      'fieldType': fieldType.name,
      'options': options,
      'defaultValue': defaultValue,
      'validation': validation,
      'order': order,
      'isSearchable': isSearchable,
      'isDisplayedInList': isDisplayedInList,
    };
  }

  /// Helper para converter string em FieldType
  static FieldType _parseFieldType(String? typeName) {
    if (typeName == null) return FieldType.text;
    
    try {
      return FieldType.values.firstWhere(
        (type) => type.name.toLowerCase() == typeName.toLowerCase(),
        orElse: () => FieldType.text,
      );
    } catch (_) {
      return FieldType.text;
    }
  }
}

/// Modelo para categoria de produto
class ProductCategory {
  final String id;
  final String name;
  final ProductType productType;
  final String description;
  final bool isActive;
  final int order;
  final List<CustomField> customFields;
  final DateTime createdAt;
  final DateTime updatedAt;

  ProductCategory({
    required this.id,
    required this.name,
    required this.productType,
    required this.description,
    this.isActive = true,
    required this.order,
    required this.customFields,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Cria uma cópia do objeto com os campos atualizados
  ProductCategory copyWith({
    String? id,
    String? name,
    ProductType? productType,
    String? description,
    bool? isActive,
    int? order,
    List<CustomField>? customFields,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return ProductCategory(
      id: id ?? this.id,
      name: name ?? this.name,
      productType: productType ?? this.productType,
      description: description ?? this.description,
      isActive: isActive ?? this.isActive,
      order: order ?? this.order,
      customFields: customFields ?? this.customFields,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  /// Factory para criar um ProductCategory a partir de um documento do Firestore
  factory ProductCategory.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    
    // Converte a lista de campos customizados
    final List<dynamic> customFieldsData = data['customFields'] ?? [];
    final List<CustomField> customFields = customFieldsData
        .map((fieldData) => CustomField.fromMap(fieldData, id: fieldData['id']))
        .toList();
    
    return ProductCategory(
      id: doc.id,
      name: data['name'] ?? '',
      productType: _parseProductType(data['productType']),
      description: data['description'] ?? '',
      isActive: data['isActive'] ?? true,
      order: data['order'] ?? 0,
      customFields: customFields,
      createdAt: (data['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
      updatedAt: (data['updatedAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
    );
  }

  /// Converte o objeto para um Map para salvar no Firestore
  Map<String, dynamic> toFirestore() {
    return {
      'name': name,
      'productType': productType.name,
      'description': description,
      'isActive': isActive,
      'order': order,
      'customFields': customFields.map((field) => field.toMap()).toList(),
      'createdAt': Timestamp.fromDate(createdAt),
      'updatedAt': Timestamp.fromDate(DateTime.now()),
    };
  }
  
  /// Helper para converter string em ProductType
  static ProductType _parseProductType(String? typeName) {
    if (typeName == null) return ProductType.coffee;
    
    try {
      return ProductType.values.firstWhere(
        (type) => type.name.toLowerCase() == typeName.toLowerCase(),
        orElse: () => ProductType.coffee,
      );
    } catch (_) {
      return ProductType.coffee;
    }
  }
  
  /// Factory para criar uma nova categoria vazia (para formulários)
  factory ProductCategory.empty() {
    return ProductCategory(
      id: '',
      name: '',
      productType: ProductType.coffee,
      description: '',
      order: 0,
      customFields: [],
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }
} 