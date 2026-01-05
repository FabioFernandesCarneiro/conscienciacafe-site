# 🌐 Sistema Web de Gestão Financeira - Consciência Café

Uma aplicação web moderna para gestão financeira empresarial e pessoal, com integração completa à API do Omie e recursos avançados de conciliação e análise.

## ✨ Funcionalidades

### 📊 Dashboard
- Visão geral do status financeiro
- Cards de resumo (receitas, despesas, saldo atual)
- Gráficos de fluxo de caixa *(em desenvolvimento)*
- Ações rápidas para funcionalidades principais
- Status do sistema e estatísticas

### 💰 Extrato Pessoa Jurídica
- **Visualização completa** de lançamentos das contas
- **Filtros avançados** por período e tipo de conta
- **Resumo financeiro** com totais de créditos, débitos e saldo
- **Status de conciliação** para cada lançamento
- **Detalhes completos** de cada transação
- **Interface responsiva** e moderna

### 🏦 Contas Suportadas
- **Conta Corrente Nubank PJ** (ID 8)
- **Cartão de Crédito Nubank PJ** (ID 9)

## 🚀 Como Executar

### Pré-requisitos
```bash
# Instalar dependências
pip3 install -r requirements.txt

# Configurar variáveis de ambiente no .env
OMIE_APP_KEY=seu_app_key_aqui
OMIE_APP_SECRET=seu_app_secret_aqui
FLASK_SECRET_KEY=sua_chave_secreta_aqui  # Opcional
```

### Executar a Aplicação
```bash
# Iniciar servidor
python3 app.py

# Acessar aplicação
Dashboard: http://localhost:5001
Extrato PJ: http://localhost:5001/extrato-pj
```

## 📡 APIs Disponíveis

### Contas Disponíveis
```bash
GET /api/contas-disponiveis
```

### Extrato de Conta Corrente
```bash
GET /api/extrato-conta-corrente
Parâmetros:
- conta_id: ID da conta (8=Corrente, 9=Cartão)
- data_inicio: Data inicial (formato dd/mm/yyyy)
- data_fim: Data final (formato dd/mm/yyyy)
- pagina: Número da página (padrão: 1)
```

## 🛠️ Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, Chart.js, Axios
- **Integração**: API Omie oficial
- **Estilo**: Bootstrap Icons, CSS customizado
- **Responsividade**: Layout mobile-first

## 📋 Estrutura do Projeto

```
├── app.py                 # Aplicação Flask principal
├── templates/             # Templates HTML
│   ├── base.html         # Template base
│   ├── dashboard.html    # Dashboard principal
│   └── extrato_pj.html   # Tela de extrato PJ
├── static/               # Arquivos estáticos (CSS, JS)
├── src/                  # Código fonte existente
│   ├── omie_client.py   # Cliente integração Omie
│   └── ...
└── requirements.txt      # Dependências Python
```

## 🎨 Interface

### Características da UI
- **Design moderno** com gradientes e sombras sutis
- **Sidebar navegação** com ícones intuitivos
- **Cards informativos** com cores temáticas
- **Tabelas responsivas** com hover effects
- **Modals detalhados** para informações extras
- **Alertas contextuais** para feedback do usuário

### Recursos de UX
- **Loading states** durante carregamento de dados
- **Filtros intuitivos** com validação
- **Formatação automática** de valores monetários
- **Status visuais** para lançamentos conciliados
- **Ações rápidas** acessíveis
- **Tooltips informativos**

## 🔮 Próximas Funcionalidades

### Em Desenvolvimento
- [ ] Gráficos interativos (Chart.js)
- [ ] Funcionalidade de conciliação via web
- [ ] Upload de arquivos OFX
- [ ] Relatórios personalizados
- [ ] Financeiro pessoal
- [ ] Exportação de dados
- [ ] Dashboard com métricas avançadas

### Planejado
- [ ] Autenticação e usuários
- [ ] API REST completa
- [ ] Notificações push
- [ ] Backup automático
- [ ] Integração com outros bancos
- [ ] Mobile app (PWA)

## 🚦 Status do Sistema

✅ **Funcionando**:
- Aplicação web Flask
- APIs de integração Omie
- Extrato PJ com filtros
- Interface responsiva
- Sistema de conciliação (CLI)

⚠️ **Em Desenvolvimento**:
- Gráficos e visualizações
- Funcionalidades avançadas
- Otimizações de performance

## 📞 Suporte

Para dúvidas ou suporte:
- Verificar logs da aplicação no terminal
- Validar configuração das variáveis de ambiente
- Confirmar conectividade com API do Omie
- Verificar se as dependências estão instaladas

## 🎯 Objetivo

Criar uma plataforma completa de gestão financeira que combine:
- **Automatização** via IA e ML
- **Visualização** clara e intuitiva
- **Integração** robusta com ERPs
- **Usabilidade** para usuários não-técnicos
- **Escalabilidade** para crescimento futuro