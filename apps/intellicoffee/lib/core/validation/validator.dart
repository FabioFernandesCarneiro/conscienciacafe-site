/// Interface base para validadores
abstract class Validator<T> {
  String? validate(T value);
}

/// Resultado de validação
class ValidationResult {
  final bool isValid;
  final String? error;

  const ValidationResult.valid() : isValid = true, error = null;
  const ValidationResult.invalid(this.error) : isValid = false;

  @override
  String toString() => isValid ? 'Valid' : 'Invalid: $error';
}

/// Validador composto que permite combinar múltiplos validadores
class CompositeValidator<T> implements Validator<T> {
  final List<Validator<T>> validators;

  CompositeValidator(this.validators);

  @override
  String? validate(T value) {
    for (final validator in validators) {
      final error = validator.validate(value);
      if (error != null) {
        return error;
      }
    }
    return null;
  }

  /// Combina validadores usando operador +
  CompositeValidator<T> operator +(Validator<T> other) {
    return CompositeValidator([...validators, other]);
  }
}

/// Validador condicional
class ConditionalValidator<T> implements Validator<T> {
  final bool Function(T value) condition;
  final Validator<T> validator;

  ConditionalValidator(this.condition, this.validator);

  @override
  String? validate(T value) {
    if (condition(value)) {
      return validator.validate(value);
    }
    return null;
  }
}

/// Validadores básicos para String
class StringValidators {
  /// Verifica se o valor não está vazio
  static Validator<String> required([String? message]) {
    return _RequiredValidator(message ?? 'Este campo é obrigatório');
  }

  /// Verifica comprimento mínimo
  static Validator<String> minLength(int length, [String? message]) {
    return _MinLengthValidator(length, message);
  }

  /// Verifica comprimento máximo
  static Validator<String> maxLength(int length, [String? message]) {
    return _MaxLengthValidator(length, message);
  }

  /// Verifica se é um email válido
  static Validator<String> email([String? message]) {
    return _EmailValidator(message ?? 'Email inválido');
  }

  /// Verifica se atende a um padrão regex
  static Validator<String> pattern(RegExp pattern, [String? message]) {
    return _PatternValidator(pattern, message ?? 'Formato inválido');
  }

  /// Verifica se contém apenas letras
  static Validator<String> alphabetic([String? message]) {
    return pattern(
      RegExp(r'^[a-zA-ZÀ-ÿ\s]+$'),
      message ?? 'Deve conter apenas letras',
    );
  }

  /// Verifica se contém apenas números
  static Validator<String> numeric([String? message]) {
    return pattern(
      RegExp(r'^[0-9]+$'),
      message ?? 'Deve conter apenas números',
    );
  }

  /// Verifica se contém apenas letras e números
  static Validator<String> alphanumeric([String? message]) {
    return pattern(
      RegExp(r'^[a-zA-Z0-9À-ÿ\s]+$'),
      message ?? 'Deve conter apenas letras e números',
    );
  }

  /// Verifica se é um telefone brasileiro válido
  static Validator<String> brazilianPhone([String? message]) {
    return pattern(
      RegExp(r'^\(\d{2}\)\s\d{4,5}-\d{4}$'),
      message ?? 'Telefone inválido. Use o formato (XX) XXXXX-XXXX',
    );
  }

  /// Verifica se é um CPF válido
  static Validator<String> cpf([String? message]) {
    return _CPFValidator(message ?? 'CPF inválido');
  }

  /// Verifica se é um CNPJ válido
  static Validator<String> cnpj([String? message]) {
    return _CNPJValidator(message ?? 'CNPJ inválido');
  }
}

/// Validadores para números
class NumberValidators {
  /// Verifica se é obrigatório
  static Validator<num?> required([String? message]) {
    return _NumberRequiredValidator(message ?? 'Este campo é obrigatório');
  }

  /// Verifica valor mínimo
  static Validator<num> min(num minimum, [String? message]) {
    return _MinNumberValidator(minimum, message);
  }

  /// Verifica valor máximo
  static Validator<num> max(num maximum, [String? message]) {
    return _MaxNumberValidator(maximum, message);
  }

  /// Verifica se está dentro de um intervalo
  static Validator<num> range(num min, num max, [String? message]) {
    return CompositeValidator([
      NumberValidators.min(min),
      NumberValidators.max(max),
    ]);
  }

  /// Verifica se é positivo
  static Validator<num> positive([String? message]) {
    return _MinNumberValidator(0.01, message ?? 'Deve ser maior que zero');
  }

  /// Verifica se é não negativo
  static Validator<num> nonNegative([String? message]) {
    return _MinNumberValidator(0, message ?? 'Não pode ser negativo');
  }
}

// Implementações privadas dos validadores

class _RequiredValidator implements Validator<String> {
  final String message;
  _RequiredValidator(this.message);

  @override
  String? validate(String value) {
    if (value.trim().isEmpty) return message;
    return null;
  }
}

class _MinLengthValidator implements Validator<String> {
  final int length;
  final String? message;
  _MinLengthValidator(this.length, this.message);

  @override
  String? validate(String value) {
    if (value.length < length) {
      return message ?? 'Deve ter pelo menos $length caracteres';
    }
    return null;
  }
}

class _MaxLengthValidator implements Validator<String> {
  final int length;
  final String? message;
  _MaxLengthValidator(this.length, this.message);

  @override
  String? validate(String value) {
    if (value.length > length) {
      return message ?? 'Deve ter no máximo $length caracteres';
    }
    return null;
  }
}

class _EmailValidator implements Validator<String> {
  final String message;
  _EmailValidator(this.message);

  @override
  String? validate(String value) {
    if (value.isEmpty) return null; // Deixa a validação de obrigatório para outro validador
    
    final emailRegex = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
    if (!emailRegex.hasMatch(value)) return message;
    return null;
  }
}

class _PatternValidator implements Validator<String> {
  final RegExp pattern;
  final String message;
  _PatternValidator(this.pattern, this.message);

  @override
  String? validate(String value) {
    if (value.isEmpty) return null;
    if (!pattern.hasMatch(value)) return message;
    return null;
  }
}

class _CPFValidator implements Validator<String> {
  final String message;
  _CPFValidator(this.message);

  @override
  String? validate(String value) {
    if (value.isEmpty) return null;
    
    // Remove formatação
    final cpf = value.replaceAll(RegExp(r'[^0-9]'), '');
    
    if (cpf.length != 11) return message;
    if (RegExp(r'^(\d)\1*$').hasMatch(cpf)) return message; // Todos os dígitos iguais
    
    // Validação dos dígitos verificadores
    int sum = 0;
    for (int i = 0; i < 9; i++) {
      sum += int.parse(cpf[i]) * (10 - i);
    }
    int firstDigit = (sum * 10) % 11;
    if (firstDigit == 10) firstDigit = 0;
    if (firstDigit != int.parse(cpf[9])) return message;
    
    sum = 0;
    for (int i = 0; i < 10; i++) {
      sum += int.parse(cpf[i]) * (11 - i);
    }
    int secondDigit = (sum * 10) % 11;
    if (secondDigit == 10) secondDigit = 0;
    if (secondDigit != int.parse(cpf[10])) return message;
    
    return null;
  }
}

class _CNPJValidator implements Validator<String> {
  final String message;
  _CNPJValidator(this.message);

  @override
  String? validate(String value) {
    if (value.isEmpty) return null;
    
    // Remove formatação
    final cnpj = value.replaceAll(RegExp(r'[^0-9]'), '');
    
    if (cnpj.length != 14) return message;
    if (RegExp(r'^(\d)\1*$').hasMatch(cnpj)) return message;
    
    // Validação do primeiro dígito
    const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    int sum1 = 0;
    for (int i = 0; i < 12; i++) {
      sum1 += int.parse(cnpj[i]) * weights1[i];
    }
    int digit1 = sum1 % 11;
    digit1 = digit1 < 2 ? 0 : 11 - digit1;
    if (digit1 != int.parse(cnpj[12])) return message;
    
    // Validação do segundo dígito
    const weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    int sum2 = 0;
    for (int i = 0; i < 13; i++) {
      sum2 += int.parse(cnpj[i]) * weights2[i];
    }
    int digit2 = sum2 % 11;
    digit2 = digit2 < 2 ? 0 : 11 - digit2;
    if (digit2 != int.parse(cnpj[13])) return message;
    
    return null;
  }
}

class _NumberRequiredValidator implements Validator<num?> {
  final String message;
  _NumberRequiredValidator(this.message);

  @override
  String? validate(num? value) {
    if (value == null) return message;
    return null;
  }
}

class _MinNumberValidator implements Validator<num> {
  final num minimum;
  final String? message;
  _MinNumberValidator(this.minimum, this.message);

  @override
  String? validate(num value) {
    if (value < minimum) {
      return message ?? 'Deve ser pelo menos $minimum';
    }
    return null;
  }
}

class _MaxNumberValidator implements Validator<num> {
  final num maximum;
  final String? message;
  _MaxNumberValidator(this.maximum, this.message);

  @override
  String? validate(num value) {
    if (value > maximum) {
      return message ?? 'Deve ser no máximo $maximum';
    }
    return null;
  }
}