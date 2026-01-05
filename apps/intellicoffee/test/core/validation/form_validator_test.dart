import 'package:flutter_test/flutter_test.dart';
import 'package:intellicoffee/core/validation/form_validator.dart';
import 'package:intellicoffee/core/validation/validator.dart';

void main() {
  group('FormValidator', () {
    test('validates required and email rules', () {
      final form = FormValidator();
      form.addValidator(
        'email',
        Validators.string().required('Obrigatório').email('Email inválido').build(),
      );

      // Empty -> required error
      form.setValue('email', '');
      expect(form.getError('email'), 'Obrigatório');
      expect(form.isValid, isFalse);

      // Bad email -> email error
      form.setValue('email', 'user@invalid');
      expect(form.getError('email'), 'Email inválido');
      expect(form.isValid, isFalse);

      // Good email -> no error
      form.setValue('email', 'user@example.com');
      expect(form.getError('email'), isNull);
      expect(form.isValid, isTrue);
    });

    test('composite validators stop on first error', () {
      final validator = Validators.string()
          .minLength(5, 'min5')
          .pattern(RegExp(r'^abc'), 'must start with abc')
          .build();

      expect(validator.validate('a'), 'min5');
      expect(validator.validate('xbcdx'), 'must start with abc');
      expect(validator.validate('abcde'), isNull);
    });

    test('number validators work as expected', () {
      final v = Validators.number().min(2).max(5).build();
      expect(v.validate(1), isNotNull);
      expect(v.validate(3), isNull);
      expect(v.validate(6), isNotNull);
    });
  });
}
