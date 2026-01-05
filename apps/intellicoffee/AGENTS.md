# Repository Guidelines

## Project Structure & Module Organization
- `lib/` — Flutter app code. Key areas: `core/` (errors, validation, theme), `config/` (routing), `features/` (domain-driven modules), `shared/` (reusable widgets), `main.dart`, `firebase_options.dart`.
- `test/` — unit/widget tests; mirror `lib/` structure (e.g., `test/features/...`).
- `functions/` — Firebase Cloud Functions (Node.js). Uses ESLint and Firebase CLI.
- Platform targets: `android/`, `ios/`, `web/`. Non-functional unless you are working on platform integration.
- Supporting: `docs/`, `prototypes/`, `public/`.

## Build, Test, and Development Commands
- Install deps: `flutter pub get`
- Analyze lints: `flutter analyze` (rules in `analysis_options.yaml`)
- Format code: `dart format .` (run before committing)
- Run app: `flutter run -d chrome` (web) or `flutter run` (auto-detect)
- Tests: `flutter test` (unit + widget)
- Build artifacts: `flutter build apk` | `flutter build ios --no-codesign` | `flutter build web`
- Functions (from `functions/`): `npm i`, `npm run lint`, `npm run serve` (emulator), `npm run deploy` (authorized only)
- Firebase emulators (root): `firebase emulators:start` (uses `firebase.json`)

## Coding Style & Naming Conventions
- Dart style: 2-space indent; files `snake_case.dart`; classes/types `UpperCamelCase`; methods/fields `lowerCamelCase`.
- Screens: file ends with `_screen.dart`, class ends with `Screen`.
- Riverpod: providers in files ending `_provider.dart`, state classes `...State`, notifiers `...Notifier`, controllers `...Controller`.
- Keep features modular under `lib/features/<domain>/...`; place shared UI in `lib/shared/widgets/`.

## Testing Guidelines
- Framework: `flutter_test` (see `test/widget_test.dart`).
- Name tests `*_test.dart` and mirror `lib/` paths.
- Prefer widget tests for UI and pure unit tests for validators, use cases, and repositories.
- Avoid network calls; use Firebase emulators or fakes/mocks.
- Run locally with `flutter test` and ensure deterministic results.

## Commit & Pull Request Guidelines
- Commit messages: prefer Conventional Commits (e.g., `feat(products): add category filter`, `fix(auth): handle session loss`).
- PRs: focused scope, clear description, linked issues, screenshots for UI changes, and test notes.
- Passing `flutter analyze` + formatting required; include tests for new logic.

## Security & Configuration Tips
- Do not commit secrets or service keys. Use `firebase_options.dart` (generated) and local emulators.
- Avoid modifying `android/`, `ios/`, `web/` unless necessary; most work belongs in `lib/` and `functions/`.

## Agent-Specific Instructions
- Follow directory and naming patterns above. Prefer minimal, targeted diffs.
- Update related docs/tests when changing public APIs or routes in `config/app_router.dart`.
