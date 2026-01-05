import 'package:flutter_test/flutter_test.dart';
import 'package:intellicoffee/core/validation/validator.dart';

void main() {
  group('Validator basics', () {
    test('email validator allows empty and validates pattern', () {
      final email = StringValidators.email('inv');
      expect(email.validate(''), isNull); // empty is ok (use required separately)
      expect(email.validate('x@y'), isNotNull);
      expect(email.validate('x@y.z'), isNull);
    });

    test('cpf/cnpj validators basic length guards', () {
      final cpf = StringValidators.cpf();
      final cnpj = StringValidators.cnpj();
      expect(cpf.validate('123'), isNotNull);
      expect(cnpj.validate('123'), isNotNull);
    });
  });
}

