## Common developer commands

.PHONY: setup analyze format test coverage run-web emulators functions-lint functions-format functions-format-check outdated

setup:
	flutter pub get
	cd functions && npm ci

analyze:
	flutter analyze

format:
	dart format .

test:
	flutter test

coverage:
	flutter test --coverage

run-web:
	flutter run -d chrome

emulators:
	firebase emulators:start

functions-lint:
	cd functions && npm run lint

functions-format:
	cd functions && npm run format

functions-format-check:
	cd functions && npm run format:check

outdated:
	flutter pub outdated || true
	cd functions && npm outdated || true
