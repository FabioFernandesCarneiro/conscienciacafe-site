import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/validation/form_validator.dart';
import 'package:intellicoffee/core/validation/validation_mixin.dart';
import 'package:intellicoffee/features/products/data/providers/product_category_provider.dart';
import 'package:intellicoffee/features/products/domain/models/product_category.dart';
import 'package:intellicoffee/shared/widgets/form_section.dart';
import 'package:intellicoffee/shared/widgets/module_header.dart';

/// Tela de formulário de categoria de produto usando sistema de validação melhorado
class ProductCategoryFormScreenImproved extends ConsumerStatefulWidget {
  final String? categoryId;
  
  const ProductCategoryFormScreenImproved({
    super.key,
    this.categoryId,
  });

  @override
  ConsumerState<ProductCategoryFormScreenImproved> createState() => 
      _ProductCategoryFormScreenImprovedState();
}

class _ProductCategoryFormScreenImprovedState 
    extends ConsumerState<ProductCategoryFormScreenImproved> 
    with ValidationMixin {
  
  bool _isLoading = false;
  bool _isNewCategory = true;
  
  // Controladores para os campos do formulário
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  
  // Valores selecionados
  ProductType _selectedType = ProductType.coffee;
  bool _isActive = true;
  
  // Estado para gerenciar campos personalizados
  List<CustomField> _customFields = [];
  
  // Cor do módulo de produtos (verde)
  static const _moduleColor = Color(0xFF4CAF50);

  @override
  void initState() {
    super.initState();
    _initializeForm();
  }

  @override
  void setupValidators() {
    // Configurar validadores para cada campo
    addValidator(
      'name',
      Validators.string()
          .required('Nome da categoria é obrigatório')
          .minLength(2, 'Nome deve ter pelo menos 2 caracteres')
          .maxLength(50, 'Nome deve ter no máximo 50 caracteres')
          .build(),
    );

    addValidator(
      'description',
      Validators.string()
          .maxLength(500, 'Descrição deve ter no máximo 500 caracteres')
          .build(),
    );

    addValidator(
      'type',
      Validators.custom<ProductType?>((value) {
        if (value == null) return 'Selecione um tipo de produto';
        return null;
      }),
    );
  }

  void _initializeForm() {
    _isNewCategory = widget.categoryId == null;
    
    if (!_isNewCategory) {
      _loadExistingCategory();
    }
  }

  void _loadExistingCategory() async {
    setState(() => _isLoading = true);
    
    try {
      final notifier = ref.read(productCategoryNotifierProvider.notifier);
      await notifier.loadCategoryById(widget.categoryId!);
      
      final state = ref.read(productCategoryNotifierProvider);
      final category = state.currentCategory;
      
      if (category != null) {
        _nameController.text = category.name;
        _descriptionController.text = category.description;
        _selectedType = category.productType;
        _isActive = category.isActive;
        _customFields = List.from(category.customFields);
        
        // Atualizar valores no validador
        setValue('name', category.name);
        setValue('description', category.description);
        setValue('type', category.productType);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao carregar categoria: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _saveCategory() async {
    if (!validateForm()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Por favor, corrija os erros no formulário'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final notifier = ref.read(productCategoryNotifierProvider.notifier);
      
      final category = ProductCategory(
        id: _isNewCategory ? '' : widget.categoryId!,
        name: _nameController.text.trim(),
        description: _descriptionController.text.trim(),
        productType: _selectedType,
        isActive: _isActive,
        order: 0, // Será definido automaticamente
        customFields: _customFields,
        createdAt: _isNewCategory ? DateTime.now() : DateTime.now(), // Simplificado para o exemplo
        updatedAt: DateTime.now(),
      );

      if (_isNewCategory) {
        await notifier.addCategory(category);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Categoria criada com sucesso!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else {
        await notifier.updateCategory(category);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Categoria atualizada com sucesso!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      }

      if (mounted) {
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao salvar categoria: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _addCustomField() {
    showDialog(
      context: context,
      builder: (context) => _CustomFieldDialog(
        onFieldAdded: (field) {
          setState(() {
            _customFields.add(field);
          });
        },
      ),
    );
  }

  void _editCustomField(int index) {
    showDialog(
      context: context,
      builder: (context) => _CustomFieldDialog(
        initialField: _customFields[index],
        onFieldAdded: (field) {
          setState(() {
            _customFields[index] = field;
          });
        },
      ),
    );
  }

  void _removeCustomField(int index) {
    setState(() {
      _customFields.removeAt(index);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: Column(
        children: [
          ModuleHeader(
            title: _isNewCategory ? 'Nova Categoria' : 'Editar Categoria',
            moduleColor: _moduleColor,
            moduleIcon: Icons.category,
          ),
          
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : SingleChildScrollView(
                    padding: EdgeInsets.all(16.r),
                    child: Column(
                      children: [
                        _buildBasicInfoSection(),
                        SizedBox(height: 24.h),
                        _buildCustomFieldsSection(),
                        SizedBox(height: 32.h),
                        _buildActionButtons(),
                      ],
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildBasicInfoSection() {
    return FormSection(
      title: 'Informações Básicas',
      icon: Icon(Icons.info_outline),
      children: [
        buildValidatedTextField(
          fieldName: 'name',
          label: 'Nome da Categoria',
          hint: 'Ex: Cafés Especiais',
          icon: Icons.category,
          controller: _nameController,
          onChanged: (value) => setValue('name', value),
        ),
        SizedBox(height: 16.h),
        
        buildValidatedTextField(
          fieldName: 'description',
          label: 'Descrição',
          hint: 'Descreva a categoria...',
          icon: Icons.description,
          controller: _descriptionController,
          maxLines: 3,
          onChanged: (value) => setValue('description', value),
        ),
        SizedBox(height: 16.h),
        
        buildValidatedDropdown<ProductType>(
          fieldName: 'type',
          label: 'Tipo de Produto',
          value: _selectedType,
          icon: Icons.category_outlined,
          items: ProductType.values.map((type) {
            return DropdownMenuItem(
              value: type,
              child: Text(type.displayName),
            );
          }).toList(),
          onChanged: (value) {
            if (value != null) {
              setState(() => _selectedType = value);
              setValue('type', value);
            }
          },
        ),
        SizedBox(height: 16.h),
        
        buildValidatedSwitch(
          fieldName: 'isActive',
          label: 'Categoria Ativa',
          value: _isActive,
          onChanged: (value) {
            setState(() => _isActive = value);
            setValue('isActive', value);
          },
        ),
      ],
    );
  }

  Widget _buildCustomFieldsSection() {
    return FormSection(
      title: 'Campos Personalizados',
      icon: Icon(Icons.tune),
      children: [
        if (_customFields.isEmpty)
          const Text(
            'Nenhum campo personalizado adicionado ainda.',
            style: TextStyle(color: Colors.grey),
          )
        else
          ..._customFields.asMap().entries.map((entry) {
            final index = entry.key;
            final field = entry.value;
            
            return Card(
              margin: EdgeInsets.only(bottom: 8.h),
              child: ListTile(
                title: Text(field.name),
                subtitle: Text(field.fieldType.displayName),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.edit),
                      onPressed: () => _editCustomField(index),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete),
                      onPressed: () => _removeCustomField(index),
                    ),
                  ],
                ),
              ),
            );
          }),
        
        SizedBox(height: 16.h),
        
        ElevatedButton.icon(
          onPressed: _addCustomField,
          icon: const Icon(Icons.add),
          label: const Text('Adicionar Campo'),
          style: ElevatedButton.styleFrom(
            backgroundColor: _moduleColor,
            foregroundColor: Colors.white,
          ),
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
            label: _isNewCategory ? 'Criar Categoria' : 'Salvar Alterações',
            icon: _isNewCategory ? Icons.add : Icons.save,
            onPressed: _saveCategory,
          ),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }
}

/// Dialog para adicionar/editar campos personalizados
class _CustomFieldDialog extends StatefulWidget {
  final CustomField? initialField;
  final Function(CustomField) onFieldAdded;

  const _CustomFieldDialog({
    this.initialField,
    required this.onFieldAdded,
  });

  @override
  State<_CustomFieldDialog> createState() => _CustomFieldDialogState();
}

class _CustomFieldDialogState extends State<_CustomFieldDialog> 
    with ValidationMixin {
  
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  FieldType _selectedType = FieldType.text;
  bool _isRequired = false;

  @override
  void initState() {
    super.initState();
    
    if (widget.initialField != null) {
      final field = widget.initialField!;
      _nameController.text = field.name;
      _descriptionController.text = field.description;
      _selectedType = field.fieldType;
      _isRequired = field.isRequired;
    }
  }

  @override
  void setupValidators() {
    addValidator(
      'name',
      Validators.string()
          .required('Nome do campo é obrigatório')
          .minLength(2, 'Nome deve ter pelo menos 2 caracteres')
          .build(),
    );
  }

  void _saveField() {
    if (!validateForm()) return;

    final field = CustomField(
      id: widget.initialField?.id ?? DateTime.now().millisecondsSinceEpoch.toString(),
      name: _nameController.text.trim(),
      description: _descriptionController.text.trim(),
      fieldType: _selectedType,
      isRequired: _isRequired,
      options: [],
      defaultValue: null,
      validation: '',
      order: widget.initialField?.order ?? 0,
      isSearchable: false,
      isDisplayedInList: false,
    );

    widget.onFieldAdded(field);
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.initialField == null ? 'Novo Campo' : 'Editar Campo'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            buildValidatedTextField(
              fieldName: 'name',
              label: 'Nome do Campo',
              controller: _nameController,
            ),
            SizedBox(height: 16.h),
            
            buildValidatedTextField(
              fieldName: 'description',
              label: 'Descrição',
              controller: _descriptionController,
            ),
            SizedBox(height: 16.h),
            
            DropdownButtonFormField<FieldType>(
              initialValue: _selectedType,
              decoration: const InputDecoration(
                labelText: 'Tipo do Campo',
                border: OutlineInputBorder(),
              ),
              items: FieldType.values.map((type) {
                return DropdownMenuItem(
                  value: type,
                  child: Text(type.displayName),
                );
              }).toList(),
              onChanged: (value) {
                if (value != null) {
                  setState(() => _selectedType = value);
                }
              },
            ),
            SizedBox(height: 16.h),
            
            buildValidatedCheckbox(
              fieldName: 'isRequired',
              label: 'Campo obrigatório',
              value: _isRequired,
              onChanged: (value) {
                setState(() => _isRequired = value ?? false);
              },
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancelar'),
        ),
        ElevatedButton(
          onPressed: _saveField,
          child: const Text('Salvar'),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }
}