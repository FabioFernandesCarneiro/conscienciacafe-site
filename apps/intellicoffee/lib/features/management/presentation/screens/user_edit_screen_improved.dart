import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/core/validation/form_validator.dart';
import 'package:intellicoffee/core/validation/validation_mixin.dart';
import 'package:intellicoffee/features/management/data/providers/system_user_provider.dart';
import 'package:intellicoffee/features/management/data/providers/user_photo_provider.dart';
import 'package:intellicoffee/features/management/domain/models/system_user.dart';
import 'package:intellicoffee/shared/widgets/form_section.dart';
import 'package:intellicoffee/shared/widgets/module_header.dart';

/// Tela de edição de usuário usando sistema de validação melhorado
class UserEditScreenImproved extends ConsumerStatefulWidget {
  final String? userId;
  
  const UserEditScreenImproved({
    super.key,
    this.userId,
  });

  @override
  ConsumerState<UserEditScreenImproved> createState() => _UserEditScreenImprovedState();
}

class _UserEditScreenImprovedState extends ConsumerState<UserEditScreenImproved> 
    with ValidationMixin {
  
  late SystemUser _user;
  bool _isLoading = false;
  bool _isNewUser = true;
  
  // Estado para a foto do usuário
  Uint8List? _imageBytes;
  bool _imageSelected = false;
  final bool _loadingPhoto = false;
  
  // Controladores para campos de formulário
  final _fullNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _notesController = TextEditingController();
  
  // Estado do toggle de usuário ativo
  bool _isActive = true;
  
  // Função selecionada
  UserRole _selectedRole = UserRole.atendente;
  
  // Permissões de módulo
  Map<String, bool> _moduleAccess = {
    'atendimento': true,
    'clientes': false,
    'torrefacao': false,
    'vendasB2B': false,
    'eventos': false,
    'gestao': false,
  };

  @override
  void initState() {
    super.initState();
    
    _isNewUser = widget.userId == null || widget.userId!.isEmpty;
    
    if (!_isNewUser) {
      _loadUserData();
    } else {
      _user = SystemUser.empty();
    }
  }

  @override
  void setupValidators() {
    // Nome completo
    addValidator(
      'fullName',
      Validators.string()
          .required('Nome completo é obrigatório')
          .minLength(2, 'Nome deve ter pelo menos 2 caracteres')
          .maxLength(100, 'Nome deve ter no máximo 100 caracteres')
          .alphabetic('Nome deve conter apenas letras')
          .build(),
    );

    // Email
    addValidator(
      'email',
      Validators.string()
          .required('E-mail é obrigatório')
          .email('E-mail inválido')
          .build(),
    );

    // Telefone
    addValidator(
      'phone',
      Validators.string()
          .brazilianPhone('Telefone deve estar no formato (XX) XXXXX-XXXX')
          .build(),
    );

    // Senha (apenas para novos usuários)
    if (_isNewUser) {
      addValidator(
        'password',
        Validators.string()
            .required('Senha é obrigatória')
            .minLength(8, 'Senha deve ter pelo menos 8 caracteres')
            .pattern(
              RegExp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)'),
              'Senha deve conter pelo menos: 1 letra minúscula, 1 maiúscula e 1 número',
            )
            .build(),
      );

      // Confirmação de senha
      addValidator(
        'confirmPassword',
        Validators.custom<String>((value) {
          if (value != _passwordController.text) {
            return 'Senhas não conferem';
          }
          if (value.isEmpty && _passwordController.text.isNotEmpty) {
            return 'Confirme a senha';
          }
          return null;
        }),
      );
    }

    // Função/Role
    addValidator(
      'role',
      Validators.custom<UserRole?>((value) {
        if (value == null) return 'Selecione uma função';
        return null;
      }),
    );

    // Anotações
    addValidator(
      'notes',
      Validators.string()
          .maxLength(500, 'Anotações devem ter no máximo 500 caracteres')
          .build(),
    );

    // Validação de módulos (pelo menos um deve estar ativo)
    addValidator(
      'modules',
      Validators.custom<Map<String, bool>>((modules) {
        if (modules.values.every((access) => !access)) {
          return 'Usuário deve ter acesso a pelo menos um módulo';
        }
        return null;
      }),
    );
  }

  Future<void> _loadUserData() async {
    setState(() => _isLoading = true);
    
    try {
      final repository = ref.read(systemUserRepositoryProvider);
      final user = await repository.getUserById(widget.userId!);
      
      if (user != null) {
        _user = user;
        
        // Preencher controladores
        _fullNameController.text = user.fullName;
        _emailController.text = user.email;
        _phoneController.text = user.phone ?? '';
        _notesController.text = user.notes ?? '';
        
        // Atualizar valores no validador
        setValue('fullName', user.fullName);
        setValue('email', user.email);
        setValue('phone', user.phone ?? '');
        setValue('notes', user.notes ?? '');
        setValue('role', user.role);
        setValue('modules', user.moduleAccess);
        
        setState(() {
          _isActive = user.isActive;
          _selectedRole = user.role;
          _moduleAccess = Map<String, bool>.from(user.moduleAccess);
        });

        // TODO: Carregar foto se existir
        // if (user.photoUrl != null && user.photoUrl!.isNotEmpty) {
        //   _loadUserPhoto(user.id);
        // }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao carregar dados do usuário: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }


  Future<void> _pickImage() async {
    try {
      final ImagePicker picker = ImagePicker();
      final XFile? image = await picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 512,
        maxHeight: 512,
        imageQuality: 85,
      );
      
      if (image != null) {
        final bytes = await image.readAsBytes();
        setState(() {
          _imageBytes = bytes;
          _imageSelected = true;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao selecionar imagem: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _saveUser() async {
    if (!validateForm()) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Por favor, corrija os erros no formulário'),
            backgroundColor: Colors.orange,
          ),
        );
      }
      return;
    }

    setState(() => _isLoading = true);

    try {
      final repository = ref.read(systemUserRepositoryProvider);
      
      // Criar usuário com os dados do formulário
      final userData = SystemUser(
        id: _isNewUser ? '' : _user.id,
        fullName: _fullNameController.text.trim(),
        email: _emailController.text.trim(),
        phone: _phoneController.text.trim().isEmpty ? null : _phoneController.text.trim(),
        username: _emailController.text.trim(), // usar email como username
        role: _selectedRole,
        isActive: _isActive,
        moduleAccess: Map<String, bool>.from(_moduleAccess),
        notes: _notesController.text.trim().isEmpty ? null : _notesController.text.trim(),
        photoUrl: _user.photoUrl, // Mantém URL existente
        createdAt: _isNewUser ? DateTime.now() : _user.createdAt,
        lastModifiedAt: DateTime.now(),
      );

      String userId;
      if (_isNewUser) {
        // Criar novo usuário
        userId = await repository.createUser(userData);
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Usuário criado com sucesso!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else {
        // Atualizar usuário existente
        await repository.updateUser(userData);
        userId = userData.id;
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Usuário atualizado com sucesso!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      }

      // Upload da foto se uma nova foi selecionada
      if (_imageSelected && _imageBytes != null) {
        final photoService = ref.read(userPhotoServiceProvider);
        await photoService.uploadUserPhoto(userId, _imageBytes!);
      }

      if (mounted) {
        context.go(AppConstants.routeUserList);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao salvar usuário: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      backgroundColor: theme.colorScheme.surface,
      appBar: ModuleHeader(
        title: _isNewUser ? 'Adicionar Usuário' : 'Editar Usuário',
        moduleColor: const Color(0xFF4CAF50),
        moduleIcon: Icons.person_add_alt,
        showBackButton: true,
        backRoute: AppConstants.routeUserList,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: EdgeInsets.all(16.r),
              child: Column(
                children: [
                  _buildUserPhotoSection(),
                  SizedBox(height: 24.h),
                  _buildBasicInfoSection(),
                  SizedBox(height: 24.h),
                  if (_isNewUser) ...[
                    _buildPasswordSection(),
                    SizedBox(height: 24.h),
                  ],
                  _buildRoleSection(),
                  SizedBox(height: 24.h),
                  _buildModuleAccessSection(),
                  SizedBox(height: 24.h),
                  _buildNotesSection(),
                  SizedBox(height: 32.h),
                  _buildActionButtons(),
                ],
              ),
            ),
    );
  }

  Widget _buildUserPhotoSection() {
    return FormSection(
      title: 'Foto do Usuário',
      icon: Icon(Icons.photo_camera),
      children: [
        Center(
          child: GestureDetector(
            onTap: _pickImage,
            child: Container(
              width: 120.r,
              height: 120.r,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.grey[200],
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: _loadingPhoto
                  ? const CircularProgressIndicator()
                  : _imageBytes != null
                      ? ClipOval(
                          child: Image.memory(
                            _imageBytes!,
                            fit: BoxFit.cover,
                          ),
                        )
                      : Icon(
                          Icons.add_a_photo,
                          size: 48.r,
                          color: Colors.grey[600],
                        ),
            ),
          ),
        ),
        SizedBox(height: 8.h),
        Center(
          child: Text(
            'Toque para ${_imageBytes != null ? 'alterar' : 'adicionar'} foto',
            style: TextStyle(
              fontSize: 14.sp,
              color: Colors.grey[600],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBasicInfoSection() {
    return FormSection(
      title: 'Informações Básicas',
      icon: Icon(Icons.person_outline),
      children: [
        buildValidatedTextField(
          fieldName: 'fullName',
          label: 'Nome completo',
          hint: 'Nome do usuário',
          icon: Icons.person,
          controller: _fullNameController,
          onChanged: (value) => setValue('fullName', value),
        ),
        SizedBox(height: 16.h),
        
        buildValidatedTextField(
          fieldName: 'email',
          label: 'E-mail',
          hint: 'email@exemplo.com',
          icon: Icons.email,
          keyboardType: TextInputType.emailAddress,
          controller: _emailController,
          onChanged: (value) => setValue('email', value),
        ),
        SizedBox(height: 16.h),
        
        buildValidatedTextField(
          fieldName: 'phone',
          label: 'Telefone',
          hint: '(11) 99999-9999',
          icon: Icons.phone,
          keyboardType: TextInputType.phone,
          controller: _phoneController,
          onChanged: (value) => setValue('phone', value),
        ),
        SizedBox(height: 16.h),
        
        buildValidatedSwitch(
          fieldName: 'isActive',
          label: 'Usuário Ativo',
          value: _isActive,
          onChanged: (value) {
            setState(() => _isActive = value);
            setValue('isActive', value);
          },
        ),
      ],
    );
  }

  Widget _buildPasswordSection() {
    return FormSection(
      title: 'Senha de Acesso',
      icon: Icon(Icons.lock_outline),
      children: [
        buildValidatedTextField(
          fieldName: 'password',
          label: 'Senha',
          hint: 'Mínimo 8 caracteres',
          icon: Icons.lock,
          obscureText: true,
          controller: _passwordController,
          onChanged: (value) {
            setValue('password', value);
            // Re-validar confirmação quando senha muda
            if (_confirmPasswordController.text.isNotEmpty) {
              setValue('confirmPassword', _confirmPasswordController.text);
            }
          },
        ),
        SizedBox(height: 16.h),
        
        buildValidatedTextField(
          fieldName: 'confirmPassword',
          label: 'Confirmar Senha',
          hint: 'Digite a senha novamente',
          icon: Icons.lock_outline,
          obscureText: true,
          controller: _confirmPasswordController,
          onChanged: (value) => setValue('confirmPassword', value),
        ),
      ],
    );
  }

  Widget _buildRoleSection() {
    return FormSection(
      title: 'Função e Perfil',
      icon: Icon(Icons.badge_outlined),
      children: [
        buildValidatedDropdown<UserRole>(
          fieldName: 'role',
          label: 'Função',
          value: _selectedRole,
          icon: Icons.work_outline,
          items: UserRole.values.map((role) {
            return DropdownMenuItem(
              value: role,
              child: Text(role.displayName),
            );
          }).toList(),
          onChanged: (value) {
            if (value != null) {
              setState(() => _selectedRole = value);
              setValue('role', value);
              _updateDefaultModuleAccess(value);
            }
          },
        ),
      ],
    );
  }

  Widget _buildModuleAccessSection() {
    return FormSection(
      title: 'Acesso aos Módulos',
      icon: Icon(Icons.apps_outlined),
      children: [
        Text(
          'Selecione os módulos que o usuário pode acessar:',
          style: TextStyle(
            fontSize: 14.sp,
            color: Colors.grey[600],
          ),
        ),
        SizedBox(height: 16.h),
        
        ..._moduleAccess.entries.map((entry) {
          return Padding(
            padding: EdgeInsets.only(bottom: 8.h),
            child: SwitchListTile(
              title: Text(_getModuleName(entry.key)),
              subtitle: Text(_getModuleDescription(entry.key)),
              value: entry.value,
              onChanged: (value) {
                setState(() {
                  _moduleAccess[entry.key] = value;
                });
                setValue('modules', _moduleAccess);
              },
              activeThumbColor: const Color(0xFF4CAF50),
            ),
          );
        }),
        
        if (getError('modules') != null)
          Padding(
            padding: EdgeInsets.only(top: 8.h),
            child: Text(
              getError('modules')!,
              style: TextStyle(
                color: Colors.red,
                fontSize: 12.sp,
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildNotesSection() {
    return FormSection(
      title: 'Anotações',
      icon: Icon(Icons.note_outlined),
      children: [
        buildValidatedTextField(
          fieldName: 'notes',
          label: 'Anotações',
          hint: 'Informações adicionais sobre o usuário...',
          icon: Icons.note,
          maxLines: 3,
          controller: _notesController,
          onChanged: (value) => setValue('notes', value),
        ),
      ],
    );
  }

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton(
            onPressed: _isLoading ? null : () => context.pop(),
            child: const Text('Cancelar'),
          ),
        ),
        SizedBox(width: 16.w),
        Expanded(
          child: buildSubmitButton(
            label: _isNewUser ? 'Criar Usuário' : 'Salvar Alterações',
            icon: _isNewUser ? Icons.person_add : Icons.save,
            onPressed: _saveUser,
          ),
        ),
      ],
    );
  }

  void _updateDefaultModuleAccess(UserRole role) {
    // Definir acesso padrão baseado na função
    final defaultAccess = <String, bool>{
      'atendimento': true, // Todos têm acesso ao atendimento
      'clientes': role == UserRole.gerente || role == UserRole.admin,
      'torrefacao': role == UserRole.admin,
      'vendasB2B': role == UserRole.gerente || role == UserRole.admin,
      'eventos': role == UserRole.gerente || role == UserRole.admin,
      'gestao': role == UserRole.admin,
    };

    setState(() {
      _moduleAccess = defaultAccess;
    });
    setValue('modules', _moduleAccess);
  }

  String _getModuleName(String key) {
    const names = {
      'atendimento': 'Atendimento',
      'clientes': 'Clientes',
      'torrefacao': 'Torrefação',
      'vendasB2B': 'Vendas B2B',
      'eventos': 'Eventos',
      'gestao': 'Gestão',
    };
    return names[key] ?? key;
  }

  String _getModuleDescription(String key) {
    const descriptions = {
      'atendimento': 'Pedidos, mesas e pagamentos',
      'clientes': 'CRM e programa de fidelidade',
      'torrefacao': 'Gestão de lotes e torras',
      'vendasB2B': 'Clientes corporativos',
      'eventos': 'Workshops e cursos',
      'gestao': 'Relatórios e configurações',
    };
    return descriptions[key] ?? '';
  }

  @override
  void dispose() {
    _fullNameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _notesController.dispose();
    super.dispose();
  }
}