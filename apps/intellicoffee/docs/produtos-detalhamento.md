# IntelliCoffee - Módulo de Produtos

## Visão Geral
O módulo de produtos é responsável pelo cadastro, gestão e visualização dos diversos produtos oferecidos pela cafeteria e torrefação, incluindo cafés especiais, bebidas preparadas, alimentos, acessórios, livros e ingredientes. Este módulo contempla atributos específicos para cada categoria de produto, além de funcionalidades comuns como controle de estoque, precificação e personalização de produtos.

## Estrutura do Módulo

O módulo de produtos será composto por três componentes principais:

1. **Categorias de Produtos**: Agrupamento lógico de produtos com campos personalizáveis
2. **Tipos de Personalização**: Configurações para personalização dos produtos pelos clientes
3. **Produtos**: Cadastro dos itens com suas características específicas

## Modelagem de Dados

### 1. Modelo de Categoria (`ProductCategory`)
```dart
{
  id: String (auto-gerado),
  name: String, // Nome da categoria (ex: "Bebidas Quentes", "Cafés Filtrados")
  productType: ProductType, // Tipo de produto associado
  description: String,
  isActive: bool,
  order: int, // Ordem de exibição
  customFields: List<CustomField>, // Campos personalizados para esta categoria
  createdAt: DateTime,
  updatedAt: DateTime
}
```

### 2. Modelo de Campo Personalizado (`CustomField`)
```dart
{
  id: String (auto-gerado),
  name: String, // Nome do campo
  description: String,
  isRequired: bool,
  fieldType: FieldType, // Texto, Booleano, Numérico, Financeiro, Seleção
  options: List<String>, // Para campos do tipo Seleção
  defaultValue: dynamic,
  validation: String, // Regras de validação quando aplicável
  order: int, // Ordem de exibição
  isSearchable: bool, // Se pode ser usado em buscas
  isDisplayedInList: bool // Se aparece na listagem
}
```

### 3. Modelo de Personalização (`Customization`)
```dart
{
  id: String (auto-gerado),
  name: String, // Ex: "Método de Preparo", "Ingredientes"
  description: String,
  options: List<CustomizationOption>,
  minSelection: int, // Mínimo de opções selecionáveis
  maxSelection: int, // Máximo de opções selecionáveis
  isRequired: bool,
  additionalPrice: bool, // Se a personalização afeta o preço
}
```

### 4. Modelo de Opção de Personalização (`CustomizationOption`)
```dart
{
  id: String (auto-gerado),
  name: String, // Ex: "Chemex", "V60", "Bacon"
  description: String,
  additionalPrice: double, // Preço adicional (se houver)
  relatedProductId: String, // Produto relacionado (ex: ingrediente)
  isAvailable: bool
}
```

### 5. Enumeração de Tipos de Produto
```dart
enum ProductType {
  coffee,     // Grãos de café torrados
  beverage,   // Cafés preparados e bebidas
  food,       // Itens alimentícios
  accessory,  // Equipamentos e produtos para preparo
  book,       // Livros
  ingredient  // Ingredientes para personalização
}
```

### 6. Modelo Base: `Product`
```dart
{
  id: String (auto-gerado),
  name: String,
  description: String,
  productType: ProductType,
  categoryId: String, // Referência à categoria
  price: double,
  code: String, // SKU
  photoUrl: String (opcional),
  isAvailable: bool,
  createdAt: DateTime,
  updatedAt: DateTime,
  costCenters: List<String>, // Ex: Torrefação, Cafeteria, Livraria
  
  // Dados fiscais
  ncm: String, // Nomenclatura Comum do Mercosul
  cest: String, // Código Especificador da Substituição Tributária
  origin: String, // Origem da Mercadoria
  
  // Estoque
  stock: {
    current: double,
    minimum: double,
    unit: String (kg, g, un),
    alertEnabled: bool
  },
  
  // Personalizações disponíveis para este produto
  customizations: List<String>, // IDs das personalizações associadas
  
  // Campos dinâmicos específicos da categoria
  customFieldValues: Map<String, dynamic>, // Valores dos campos personalizados
  
  // Preços diferenciados (se aplicável)
  priceVariations: Map<String, double>, // Por tamanho, tipo de cliente, etc.
}
```

## Funcionalidades Principais

### 1. Gestão de Categorias
- **Cadastro de categorias**: Criação e edição de categorias para organizar produtos
- **Campos personalizados**: Configuração de campos específicos para cada categoria
- **Ordenação**: Definição da ordem de exibição das categorias
- **Ativação/desativação**: Controle da visibilidade das categorias

### 2. Gestão de Personalizações
- **Cadastro de tipos de personalização**: Criação de opções de personalização para produtos
- **Configuração de regras**: Definição de mínimo/máximo de opções selecionáveis
- **Preços adicionais**: Configuração de valores extras para personalizações
- **Vínculos com produtos**: Associação entre personalizações e produtos/ingredientes

### 3. Listagem de Produtos
- **Visualização por tipo/categoria**: Filtros hierárquicos (Tipo > Categoria)
- **Busca por nome/código/campos personalizados**: Campo de busca avançada
- **Ordenação**: Por nome, preço, disponibilidade
- **Visualização de status**: Indicação visual para produtos disponíveis/indisponíveis
- **Preview de atributos específicos**: Exibição resumida de atributos relevantes por categoria

### 4. Cadastro/Edição de Produto
- **Formulário base**: Campos comuns para todos os produtos
- **Seções dinâmicas**: Campos específicos conforme a categoria selecionada
- **Upload de imagem**: Funcionalidade para adicionar foto do produto
- **Gestão de estoque**: Controle de quantidades e configuração de alertas
- **Seleção de centros de custo**: Definição de onde o produto estará disponível
- **Dados fiscais**: Inclusão de informações para emissão de notas
- **Personalizações disponíveis**: Associação com opções de personalização
- **Preços variáveis**: Configuração de preços diferentes por contexto (B2B/B2C, tamanhos)

### 5. Gestão de Estoque
- **Controle de quantidade**: Registro de estoque atual
- **Alertas de mínimo**: Configuração de estoque mínimo e notificações
- **Histórico de movimentação**: Registro de entradas e saídas
- **Unidades personalizadas**: Suporte a diferentes unidades (kg, g, un)

### 6. Precificação
- **Preço base**: Valor padrão do produto
- **Preços por contexto**: Valores diferentes para B2B e B2C
- **Variações por tamanho**: Preços diferentes conforme tamanho (para cafés, bebidas)
- **Histórico de preços**: Registro de alterações de preço ao longo do tempo

## Interfaces

### 1. Tela de Categorias
- **Listagem**: Visualização de todas as categorias cadastradas
- **Formulário**: Interface para criação/edição de categorias
- **Campos personalizados**: Configuração dos campos específicos por categoria

### 2. Tela de Personalizações
- **Listagem**: Visualização de tipos de personalização existentes
- **Formulário**: Interface para criação/edição de personalizações
- **Opções**: Gestão das opções de cada personalização
- **Regras**: Configuração de regras de seleção (mín/máx)

### 3. Tela de Listagem de Produtos
- **Header**: Título "Produtos" e botões de ação
- **Busca e filtros**: Campo de busca e filtros por tipo/categoria
- **Cards de produto**: Exibição de informações essenciais
  - Nome e preço do produto
  - Tipo, categoria e código
  - Status de disponibilidade
  - Atributos específicos relevantes
  - Botão para visualizar/editar

### 4. Tela de Edição/Cadastro de Produto
- **Header**: Título "Editar Produto" ou "Novo Produto" e botão de salvar
- **Seção inicial**: Foto, nome, tipo, categoria, descrição, preço, código, disponibilidade
- **Dados fiscais**: Campos para NCM, CEST e origem
- **Atributos específicos**: Seção dinâmica com campos relevantes para a categoria selecionada
- **Personalizações**: Associação com opções de personalização disponíveis
- **Centro de custo**: Seleção de áreas onde o produto estará disponível
- **Controle de estoque**: Configuração de quantidades e alertas
- **Preços variáveis**: Configuração de preços por contexto quando aplicável

## Exemplos de Campos Específicos por Tipo

### Campos para Cafés
- Origem*
- Região
- Fazenda/Cooperativa
- Altitude
- Variedade
- Processo* (Natural, Lavado, Honey, etc.)
- Safra
- Pontuação (SCA)
- Perfil Sensorial (notas de sabor e aroma)
- Tipo da Torra* (Clara, Média, Escura)
- Métodos de Preparo Recomendados
- Tamanhos de Pacote (250g, 500g, 1kg)
- Preço por Tamanho e tipo de cliente (B2B / B2C)

### Campos para Bebidas
- Tamanhos Disponíveis
- Opções de Personalização (Método, Temperatura, Leite, etc.)
- Tempo de Preparo
- Ingredientes
- Informações Nutricionais

### Campos para Comidas
- Porção
- Ingredientes
- Alergênicos
- Tempo de Preparo
- Opções de Personalização

### Campos para Acessórios
- Marca
- Material
- Dimensões
- Capacidade
- Garantia
- País de Origem

### Campos para Livros
- Editora
- Autor
- ISBN
- Número de Páginas
- Consignação (Sim/Não)

### Campos para Ingredientes
- Unidade de Medida
- Alergênicos
- Custo por Unidade
- Valor Adicional

## Fluxos de Interação

### 1. Configurar Categoria e Campos Personalizados
```
1. Usuário acessa a tela de categorias
2. Cria uma nova categoria ou edita uma existente
3. Define os campos personalizados para esta categoria
4. Configura quais campos são obrigatórios e quais aparecem na listagem
5. Salva a configuração
```

### 2. Configurar Personalização
```
1. Usuário acessa a tela de personalizações
2. Cria um novo tipo (ex: "Método de Preparo") ou edita um existente
3. Adiciona opções de personalização (ex: "V60", "Chemex", "Aeropress")
4. Define regras de seleção (mínimo, máximo)
5. Configura preços adicionais se necessário
6. Salva a configuração
```

### 3. Adicionar Novo Produto
```
1. Usuário acessa a tela de listagem de produtos
2. Clica no botão "Adicionar Novo Produto"
3. Seleciona o tipo e categoria do produto
4. Preenche as informações básicas (nome, preço, etc.)
5. Sistema exibe campos específicos conforme a categoria selecionada
6. Usuário preenche os atributos específicos
7. Associa personalizações disponíveis para este produto
8. Configura disponibilidade, centros de custo e estoque
9. Adiciona dados fiscais e preços variáveis se necessário
10. Clica em "Salvar" para persistir o produto
```

### 4. Editar Produto Existente
```
1. Usuário acessa a tela de listagem de produtos
2. Busca ou filtra para localizar o produto desejado
3. Clica no produto para acessar detalhes/edição
4. Sistema exibe formulário preenchido com dados atuais
5. Usuário realiza as alterações necessárias
6. Clica em "Salvar" para persistir as mudanças
```

## Integrações

### 1. Com Módulo de Atendimento
- Listagem de produtos disponíveis para adicionar a pedidos
- Exibição de opções de personalização no momento do pedido
- Verificação de estoque em tempo real

### 2. Com Módulo de Estoque/Produção
- Atualização automática de estoque para cafés quando há novas torras
- Alertas quando produtos atingem estoque mínimo
- Registro de consumo de ingredientes

### 3. Com Módulo Cliente (App)
- Visualização de produtos com descrições detalhadas
- Exibição de opções de personalização para seleção
- Informações sobre origem dos cafés e detalhes específicos

### 4. Com Relatórios/Analytics
- Dados de produtos mais vendidos
- Margens de lucro por produto/categoria
- Análise de preferências de personalização
- Tendências de consumo

## Implementação Técnica

### Arquitetura
- **Domain**: Modelos e regras de negócio
- **Data**: Repositórios e fonte de dados (Firestore)
- **Presentation**: Telas e componentes visuais

### Armazenamento no Firestore
- Coleção `productCategories` para categorias e seus campos personalizados
- Coleção `customizations` para tipos de personalização e suas opções
- Coleção principal `products` para dados básicos dos produtos
- Subcoleção `products/{productId}/customFieldValues` para valores dos campos específicos
- Subcoleção `products/{productId}/priceVariations` para diferentes preços
- Storage para imagens de produtos

### Desempenho
- Paginação para listagem com muitos produtos
- Cache local para acesso rápido a produtos frequentes
- Índices compostos para consultas filtradas
- Armazenamento de campos frequentemente consultados diretamente no documento principal 