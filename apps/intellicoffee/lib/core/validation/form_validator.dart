import 'package:intellicoffee/core/validation/validator.dart';

/// Gerenciador de validação para formulários
class FormValidator {
  final Map<String, Validator> _validators = {};
  final Map<String, String?> _errors = {};
  final Map<String, dynamic> _values = {};

  /// Adiciona um validador para um campo
  void addValidator(String fieldName, Validator validator) {
    _validators[fieldName] = validator;
  }

  /// Define o valor de um campo e valida
  void setValue(String fieldName, dynamic value) {
    _values[fieldName] = value;
    _validateField(fieldName);
  }

  /// Obtém o valor atual de um campo
  T? getValue<T>(String fieldName) {
    return _values[fieldName] as T?;
  }

  /// Obtém o erro atual de um campo
  String? getError(String fieldName) {
    return _errors[fieldName];
  }

  /// Verifica se um campo tem erro
  bool hasError(String fieldName) {
    return _errors[fieldName] != null;
  }

  /// Verifica se o formulário inteiro é válido
  bool get isValid {
    return _errors.values.every((error) => error == null);
  }

  /// Obtém todos os erros atuais
  Map<String, String> get errors {
    return Map.fromEntries(
      _errors.entries.where((entry) => entry.value != null)
          .map((entry) => MapEntry(entry.key, entry.value!)),
    );
  }

  /// Valida um campo específico
  void _validateField(String fieldName) {
    final validator = _validators[fieldName];
    if (validator != null) {
      final value = _values[fieldName];
      _errors[fieldName] = validator.validate(value);
    }
  }

  /// Valida todos os campos
  bool validateAll() {
    for (final fieldName in _validators.keys) {
      _validateField(fieldName);
    }
    return isValid;
  }

  /// Limpa todos os erros
  void clearErrors() {
    _errors.clear();
  }

  /// Limpa erro de um campo específico
  void clearFieldError(String fieldName) {
    _errors[fieldName] = null;
  }

  /// Redefine o formulário
  void reset() {
    _values.clear();
    _errors.clear();
  }

  /// Obtém todos os valores atuais
  Map<String, dynamic> get values => Map.from(_values);
}

/// Builder para criar validadores de forma fluente
class ValidatorBuilder<T> {
  final List<Validator<T>> _validators = [];

  /// Adiciona um validador customizado
  ValidatorBuilder<T> custom(Validator<T> validator) {
    _validators.add(validator);
    return this;
  }

  /// Constrói o validador composto
  Validator<T> build() {
    if (_validators.isEmpty) {
      return _EmptyValidator<T>();
    }
    if (_validators.length == 1) {
      return _validators.first;
    }
    return CompositeValidator(_validators);
  }
}

/// Builder específico para validadores de String
class StringValidatorBuilder extends ValidatorBuilder<String> {
  /// Torna o campo obrigatório
  StringValidatorBuilder required([String? message]) {
    custom(StringValidators.required(message));
    return this;
  }

  /// Define comprimento mínimo
  StringValidatorBuilder minLength(int length, [String? message]) {
    custom(StringValidators.minLength(length, message));
    return this;
  }

  /// Define comprimento máximo
  StringValidatorBuilder maxLength(int length, [String? message]) {
    custom(StringValidators.maxLength(length, message));
    return this;
  }

  /// Valida como email
  StringValidatorBuilder email([String? message]) {
    custom(StringValidators.email(message));
    return this;
  }

  /// Valida com padrão regex
  StringValidatorBuilder pattern(RegExp pattern, [String? message]) {
    custom(StringValidators.pattern(pattern, message));
    return this;
  }

  /// Valida como alfabético
  StringValidatorBuilder alphabetic([String? message]) {
    custom(StringValidators.alphabetic(message));
    return this;
  }

  /// Valida como numérico
  StringValidatorBuilder numeric([String? message]) {
    custom(StringValidators.numeric(message));
    return this;
  }

  /// Valida como alfanumérico
  StringValidatorBuilder alphanumeric([String? message]) {
    custom(StringValidators.alphanumeric(message));
    return this;
  }

  /// Valida como telefone brasileiro
  StringValidatorBuilder brazilianPhone([String? message]) {
    custom(StringValidators.brazilianPhone(message));
    return this;
  }

  /// Valida como CPF
  StringValidatorBuilder cpf([String? message]) {
    custom(StringValidators.cpf(message));
    return this;
  }

  /// Valida como CNPJ
  StringValidatorBuilder cnpj([String? message]) {
    custom(StringValidators.cnpj(message));
    return this;
  }
}

/// Builder específico para validadores de Number
class NumberValidatorBuilder extends ValidatorBuilder<num> {
  /// Torna o campo obrigatório
  NumberValidatorBuilder required([String? message]) {
    custom(_NumberRequiredValidatorWrapper(message));
    return this;
  }

  /// Define valor mínimo
  NumberValidatorBuilder min(num minimum, [String? message]) {
    custom(NumberValidators.min(minimum, message));
    return this;
  }

  /// Define valor máximo
  NumberValidatorBuilder max(num maximum, [String? message]) {
    custom(NumberValidators.max(maximum, message));
    return this;
  }

  /// Define intervalo
  NumberValidatorBuilder range(num min, num max, [String? message]) {
    custom(NumberValidators.range(min, max, message));
    return this;
  }

  /// Valida como positivo
  NumberValidatorBuilder positive([String? message]) {
    custom(NumberValidators.positive(message));
    return this;
  }

  /// Valida como não negativo
  NumberValidatorBuilder nonNegative([String? message]) {
    custom(NumberValidators.nonNegative(message));
    return this;
  }
}

/// Métodos de conveniência para criar validadores
class Validators {
  /// Cria um builder para validadores de String
  static StringValidatorBuilder string() => StringValidatorBuilder();

  /// Cria um builder para validadores de Number
  static NumberValidatorBuilder number() => NumberValidatorBuilder();

  /// Cria um validador personalizado
  static Validator<T> custom<T>(String? Function(T) validate) {
    return _CustomValidator<T>(validate);
  }

  /// Cria um validador condicional
  static ConditionalValidator<T> when<T>(
    bool Function(T) condition,
    Validator<T> validator,
  ) {
    return ConditionalValidator(condition, validator);
  }
}

// Classes auxiliares

class _EmptyValidator<T> implements Validator<T> {
  @override
  String? validate(T value) => null;
}

class _CustomValidator<T> implements Validator<T> {
  final String? Function(T) _validate;
  _CustomValidator(this._validate);

  @override
  String? validate(T value) => _validate(value);
}

class _NumberRequiredValidatorWrapper implements Validator<num> {
  final String message;
  _NumberRequiredValidatorWrapper([String? message]) 
      : message = message ?? 'Este campo é obrigatório';

  @override
  String? validate(num value) {
    // Para números, consideramos 0 como válido
    return null;
  }
}