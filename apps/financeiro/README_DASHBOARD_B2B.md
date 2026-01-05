# Dashboard B2B - Consciência Café

## Visão Geral

O Dashboard B2B é uma extensão integrada ao sistema de conciliação financeira, projetado especificamente para análise de vendas empresariais (Business-to-Business). Ele oferece insights valiosos sobre clientes, vendas e tendências de mercado.

## Funcionalidades Principais

### 📊 Métricas em Tempo Real
- **Receita B2B Total**: Valor total de vendas no período selecionado
- **Clientes Ativos/Inativos**: Monitoramento do status dos clientes
- **Ticket Médio**: Valor médio por transação B2B
- **Taxa de Crescimento**: Comparação com período anterior

### 🔍 Análise de Clientes
- **Clientes Inativos**: Identificação de clientes sem compras no período
- **Risco de Churn**: Classificação automática de risco (Alto/Médio/Baixo)
- **Top Clientes**: Ranking dos melhores clientes por receita
- **Histórico Detalhado**: Análise individual de cada cliente

### 📈 Visualizações
- **Gráfico de Evolução**: Tendência de vendas ao longo do tempo
- **Previsão de Vendas**: Projeções baseadas em histórico
- **Alertas Inteligentes**: Notificações para situações que requerem atenção

## Arquitetura Técnica

### Backend (Python/Flask)
```
src/b2b/
├── b2b_metrics.py        # Calculadora de métricas B2B
├── sales_analyzer.py     # Analisador principal de vendas
├── client_manager.py     # Gerenciador de clientes
└── google_sheets_client.py # Integração Google Sheets
```

### Frontend (HTML/JavaScript)
- **Template**: `templates/b2b_dashboard.html`
- **Charts**: Chart.js para visualizações
- **UI**: Bootstrap 5 + Bootstrap Icons

### Integrações
1. **Google Sheets API**: Para dados de vendas B2B (opcional)
2. **Omie ERP API**: Para dados de clientes e transações
3. **Sistema ML**: Para análises preditivas

## Configuração

### 1. Dependências
```bash
pip install -r requirements.txt
```

### 2. Google Sheets (Opcional)
```bash
# Variáveis de ambiente (.env)
GOOGLE_CREDENTIALS_FILE=/path/to/credentials.json
GOOGLE_SPREADSHEET_KEY=your_spreadsheet_key
```

### 3. Estrutura da Planilha
Se usando Google Sheets, organize os dados assim:

**Aba "Vendas":**
| Cliente | CNPJ | Data | Valor | Produto/Serviço | Vendedor | Status |
|---------|------|------|-------|-----------------|----------|--------|
| Empresa ABC | 12.345.678/0001-90 | 15/12/2024 | 2500.00 | Consultoria | João Silva | fechado |

**Aba "Clientes":**
| Nome | CNPJ | Segmento | Data Cadastro | Email | Telefone | Status |
|------|------|----------|---------------|-------|----------|--------|
| Empresa ABC Ltda | 12.345.678/0001-90 | Tecnologia | 15/01/2024 | contato@abc.com | (11) 9999-1111 | ativo |

## Uso do Dashboard

### Acesso
- URL: `http://localhost:5002/dashboard-b2b`
- Link disponível no dashboard principal

### Funcionalidades

#### 1. Seleção de Período
- **30 dias**: Análise mensal
- **60 dias**: Análise bimestral (padrão)
- **90 dias**: Análise trimestral

#### 2. Métricas Principais
- Cards coloridos com métricas essenciais
- Indicadores de crescimento/declínio
- Valores formatados em Real (R$)

#### 3. Clientes Inativos
- Tabela interativa com clientes sem compras
- Classificação de risco de churn
- Dados ordenados por valor total (maior valor primeiro)

#### 4. Previsão de Vendas
- Cálculo baseado nos últimos 3 meses
- Projeção para os próximos 3 meses
- Indicador de confiabilidade

### APIs Disponíveis

```javascript
// Resumo de vendas
GET /api/b2b/resumo-vendas?periodo=60

// Clientes inativos
GET /api/b2b/clientes-inativos?dias=60

// Detalhes de cliente específico
GET /api/b2b/cliente/{client_id}

// Previsão de vendas
GET /api/b2b/previsao-vendas?meses=3

// Status das integrações
GET /api/b2b/status-integracao

// Limpar cache
GET /api/b2b/cache/limpar
```

## Métricas Calculadas

### Cliente Individual
- **LTV (Lifetime Value)**: Valor total estimado do cliente
- **Frequência de Compra**: Pedidos por mês
- **Ticket Médio**: Valor médio por pedido
- **Dias desde Última Compra**: Para identificar inatividade
- **Risco de Churn**: Baseado em padrões comportamentais

### Empresa (Geral)
- **Receita Total**: Soma de todas as vendas B2B
- **Taxa de Crescimento**: Comparação entre períodos
- **Clientes Ativos**: Clientes com compras no período
- **Taxa de Retenção**: Percentual de clientes recorrentes

## Dados Mock para Desenvolvimento

O sistema inclui dados mock para desenvolvimento quando as integrações não estão configuradas:

```python
# Exemplos de dados mock incluídos
- 5 clientes fictícios
- Transações de exemplo
- Métricas calculadas
- Status de integração simulado
```

## Troubleshooting

### Problema: "Nenhum dado encontrado"
- Verifique se o Google Sheets está configurado
- Confirme se a API do Omie está respondendo
- Verifique se existem dados no período selecionado

### Problema: "Erro ao carregar gráficos"
- Verifique se Chart.js está carregando
- Confirme se os dados estão no formato correto
- Abra o console do navegador para mais detalhes

### Problema: "Google Sheets não conecta"
- Verifique as credenciais (`credentials.json`)
- Confirme se a planilha está compartilhada
- Verifique se as APIs estão habilitadas no Google Cloud

## Próximos Desenvolvimentos

### Funcionalidades Planejadas
1. **Exportação de Dados**: Excel, CSV, PDF
2. **Alertas por Email**: Notificações automáticas
3. **Segmentação Avançada**: Por região, produto, vendedor
4. **Machine Learning**: Predição de churn mais sofisticada
5. **Dashboard Mobile**: Versão otimizada para dispositivos móveis

### Melhorias Técnicas
1. **Cache Inteligente**: Redis para performance
2. **Testes Automatizados**: Cobertura completa de testes
3. **Websockets**: Updates em tempo real
4. **API Rate Limiting**: Controle de acesso
5. **Logs Estruturados**: Melhor rastreabilidade

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs da aplicação
2. Consulte a documentação da API do Omie
3. Verifique a configuração do Google Sheets
4. Entre em contato com a equipe de desenvolvimento

---

**Versão**: 1.0.0  
**Última Atualização**: Agosto 2025  
**Compatibilidade**: Python 3.8+, Flask 2.0+