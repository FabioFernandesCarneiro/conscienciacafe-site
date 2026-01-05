# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IntelliCoffee is an integrated coffee shop and roastery management system built with Flutter + Firebase using Clean Architecture.

**Tech Stack:** Flutter | Firebase (Firestore, Auth, Functions) | Riverpod | GoRouter | ScreenUtil

**Key Dependencies:**
- **State Management:** flutter_riverpod ^2.6.1
- **Routing:** go_router ^16.2.1
- **Firebase:** firebase_core ^4.1.0, cloud_firestore ^6.0.1
- **UI:** flutter_screenutil ^5.9.3, cached_network_image ^3.4.1

### Architecture

**Clean Architecture Pattern:**
```
features/{module}/
  ├── data/            # Providers, services, repositories implementation
  ├── domain/          # Models, repository interfaces, use cases
  └── presentation/    # Controllers, screens, widgets
```

**Core Modules:**
- `auth/` - Firebase Authentication with role-based access
- `products/` - Product categories with custom fields (active development)
- `management/` - User management and admin functions
- `service/` - Customer service operations
- `home/` - Module selector and navigation

### State Management Pattern

Uses Riverpod with clear provider organization:
- **Data Providers:** Stream/Future providers for Firebase data
- **Controller Providers:** StateNotifier for form state and UI logic
- **Repository Providers:** Abstraction layer for data access
- **Use Case Providers:** Business logic encapsulation

Example provider structure in products module:
```dart
final allProductCategoriesProvider = StreamProvider<List<ProductCategory>>;
final productCategoryControllerProvider = Provider<ProductCategoryController>;
final selectedCategoryProvider = StateProvider<ProductCategory?>;
```

## Development Commands

**Setup & Environment:**
```bash
make setup                    # Run flutter pub get + npm ci for functions
flutter doctor                # Check Flutter environment
flutterfire doctor            # Check Firebase setup
```

**Running & Testing:**
```bash
flutter run                   # Development
make run-web                  # Web (chrome)
flutter run --profile         # Performance analysis
make test                     # Run all tests
flutter test test/path/to/specific_test.dart  # Single test
make coverage                 # Test coverage
```

**Code Quality:**
```bash
make analyze                  # Flutter analyze
make format                   # Format Dart code
make functions-lint           # Lint Firebase functions
make functions-format         # Format functions code
```

**Firebase:**
```bash
make emulators               # Start Firebase emulators
firebase deploy --only firestore:rules
firebase deploy --only functions
```

**Build:**
```bash
flutter build apk           # Android
flutter build web           # Web
flutter build ios           # iOS
```

## Key Implementation Details

### Authentication & Routing

**GoRouter with Auth State:**
- Uses `authStateProvider` to watch Firebase Auth state
- Role-based access control via `hasModuleAccessProvider(moduleKey)`
- Protected routes redirect to `/home` if access denied
- Centralized route constants in `AppConstants`

**Route Structure:**
```
/ → SplashScreen
/login → LoginScreen
/home → HomeScreen (module selector)
/admin → ManagementHomeScreen
/admin/users → UserListScreen
/admin/products → ProductsModule (ShellRoute)
```

### Products Module (Active Development)

**Domain Models:**
- `ProductCategory` - Main category with custom fields
- `CustomField` - Dynamic form fields with validation
- `ProductType` enum - coffee, beverage, food, accessory, book, ingredient

**Key Features:**
- Dynamic custom fields per category
- Field types: text, number, boolean, selection, date, decimal
- Firestore integration with real-time updates
- Form validation and state management

**Critical Files:**
- `lib/features/products/domain/models/product_category.dart` - Core models
- `lib/features/products/data/providers/product_category_provider.dart` - Data layer
- `lib/features/products/presentation/screens/product_category_form_screen_improved.dart` - UI

### Firebase Structure

**Collections:**
```
productCategories/{id} - Category definitions
users/{id} - User accounts with role-based access
```

**Security Rules:** RBAC implemented in `firestore.rules`

### Data Models

**Core Collections:**
- `users` - User accounts with role-based permissions
- `productCategories` - Product category definitions with custom fields
- `customers` - Customer profiles and preferences
- `orders` - Order management and tracking
- `products` - Product catalog with pricing

## Navigation & UI Patterns

**Navigation Flow:** Splash → Login → Home (module selector) → Module-specific screens

**UI Framework:**
- **Responsive Design:** ScreenUtil for consistent sizing across devices
- **Theme System:** Centralized in `core/theme/app_theme.dart`
- **Module Colors:** Each module has distinct color (defined in `AppConstants`)

**Standard Components:**
- Forms use `shared/widgets/form_field.dart` components
- Consistent navigation patterns across modules
- Error handling via `core/errors/` classes

## Code Standards & Best Practices

### Naming Conventions
- **Files:** `snake_case.dart`
- **Classes:** `PascalCase`
- **Variables/Methods:** `camelCase`
- **Constants:** `SNAKE_CASE` or `kCamelCase`

### Code Quality (analysis_options.yaml)
- **Strict Analysis:** Enabled strict-casts, strict-inference, strict-raw-types
- **Linting:** Comprehensive rules for performance, readability, Flutter best practices
- **Formatting:** `prefer_single_quotes`, `prefer_const_constructors`

### Widget Architecture
- **Prefer StatelessWidget** with Riverpod for state management
- **Extract reusable widgets** to `shared/widgets/`
- **Use `const` constructors** where possible
- **Document complex widgets** with `///` comments

### Form Implementation Pattern
```dart
// Controller with validation
class FormController extends StateNotifier<FormState> {
  void updateField(String value) {
    state = state.copyWith(field: value, fieldError: validate(value));
  }

  bool get isValid => /* validation logic */;
}

// UI using standard components
AppFormField(
  label: 'Field Name',
  errorText: state.fieldError,
  onChanged: controller.updateField,
)
```

### Testing
- Unit tests in `test/core/` for business logic
- Widget tests in `test/widgets/` for UI components
- Use descriptive test names and arrange-act-assert pattern

## Design System & UI Guidelines

**Theme Location:** `core/theme/app_theme.dart`

**Critical Rules:**
- ✅ **Always use theme:** `Theme.of(context).colorScheme.primary`
- ✅ **Always use ScreenUtil:** `.w`, `.h`, `.r`, `.sp` for responsive sizing
- ❌ **Never hardcode colors:** Use theme references instead of `Colors.green`

**Standard Form Components:**
- Location: `shared/widgets/form_field.dart`, `form_section.dart`, `form_button.dart`
- Available: `AppFormField`, `AppEmailField`, `AppPasswordField`, etc.
- Organization: Use `FormSection` to group related fields

## Firebase Integration

**Firestore Collections:**
```
productCategories/{id} - Product category definitions with custom fields
users/{id} - User accounts with role-based permissions
```

**Security:** RBAC implemented in `firestore.rules`

## Common Issues & Solutions

### Firebase
- **Auth Issues:** Check user exists, validate credentials, verify RBAC claims
- **Firestore:** Verify collection paths, security rules, use `snapshots()` for real-time data

### State Management (Riverpod)
- **Providers:** Use `.notifier` for updates, `.select()` for specific parts
- **Performance:** Minimize provider scope, avoid circular dependencies

### UI/Performance
- **Layout Issues:** Use `debugPaintSizeEnabled = true`, systematic ScreenUtil usage
- **Performance:** Prefer `ListView.builder`, extract widgets, use `const` constructors

### Debugging
```bash
flutter run --profile --devtools  # Performance analysis
flutter test test/path/specific_test.dart  # Single test
```

### Development Workflow
1. **Design:** Define requirements and data models
2. **Implementation:** Models → repositories → providers → UI → routes
3. **Testing:** Unit tests for logic, widget tests for UI
4. **Firebase:** Update security rules, test with emulators