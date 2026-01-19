# Sistema Inteligente de Conciliação Bancária - Consciência Café

Sistema automatizado para conciliação bancária integrado com Omie ERP, utilizando Machine Learning para categorização inteligente de transações.

## Funcionalidades

- 📄 **Leitura de arquivos OFX** do banco
- 🔍 **Verificação automática** de lançamentos já existentes no Omie
- 🤖 **Categorização inteligente** usando Machine Learning
- 📚 **Aprendizado contínuo** com correções manuais
- ✅ **Marcação automática** de lançamentos como conciliados
- 🎯 **Sugestões baseadas** em transações similares anteriores

## Fluxo de Funcionamento

1. **Leitura do OFX**: Sistema lê arquivo OFX do banco
2. **Verificação**: Checa se transação já existe no Omie
3. **Categorização IA**: Se não existe, usa ML para sugerir categoria/cliente
4. **Decisão Automática**: Se confiança > 70%, cria lançamento automaticamente
5. **Revisão Manual**: Se confiança baixa, solicita input do usuário
6. **Aprendizado**: Salva decisão para melhorar futuras predições

## Configuração

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar credenciais Omie
```bash
cp .env.example .env
# Editar .env com suas credenciais do Omie
```

### 3. Executar sistema
```bash
python main.py
```

## Estrutura do Projeto

```
src/
├── ofx_parser.py          # Parser de arquivos OFX
├── omie_client.py         # Cliente API Omie
├── ml_categorizer.py      # Sistema ML de categorização
├── reconciliation_engine.py # Engine principal
data/
├── learning_data.db       # Base de dados de aprendizado
models/
├── categorizer_model.pkl  # Modelo ML treinado
```

## Como Obter Credenciais Omie

1. Acesse sua conta Omie
2. Vá em Configurações > Integração > API
3. Gere App Key e App Secret
4. Configure no arquivo `.env`

## Aprendizado do Sistema

O sistema aprende com cada decisão manual:
- Salva padrões de descrições → categorias
- Melhora predições futuras
- Sugere baseado em histórico
- Retreina modelo automaticamente