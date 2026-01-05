#!/usr/bin/env python3
"""
Migração de Dados do Omie - Sistema de Importação Histórica
Importa todos os dados do Omie desde 2023 para o banco local
"""

import os
import sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from src.database_manager import DatabaseManager
from src.omie_client import OmieClient
import time
import json

class OmieMigration:
    def __init__(self):
        load_dotenv()

        # Inicializar componentes
        self.db = DatabaseManager()
        self.omie = OmieClient(
            app_key=os.getenv('OMIE_APP_KEY'),
            app_secret=os.getenv('OMIE_APP_SECRET')
        )

        # Configurações de migração
        self.start_date = date(2023, 1, 1)
        self.end_date = date.today()

        # Descobrir contas dinamicamente
        self.discovered_accounts = self.discover_omie_accounts()

        print(f"🔄 Iniciando migração de dados do Omie")
        print(f"📅 Período: {self.start_date} até {self.end_date}")
        print(f"🏦 Contas descobertas: {len(self.discovered_accounts)}")
        for account in self.discovered_accounts:
            print(f"  - ID {account['id']}: {account['nome']}")

    def run_full_migration(self):
        """Executa migração completa"""
        try:
            # Criar lote de importação principal
            batch_id = self.db.create_import_batch(
                source='omie_migration',
                metadata={
                    'start_date': self.start_date.isoformat(),
                    'end_date': self.end_date.isoformat(),
                    'migration_version': '1.0'
                }
            )

            print(f"📦 Lote de migração criado: ID {batch_id}")

            # Etapa 1: Migrar estruturas básicas
            print("\n🏗️ ETAPA 1: Migrando estruturas básicas...")
            self.migrate_accounts()
            self.migrate_categories()
            self.migrate_clients()

            # Etapa 2: Migrar dados históricos
            print("\n📊 ETAPA 2: Migrando dados históricos...")
            total_records = 0
            successful_records = 0
            failed_records = 0

            for account in self.discovered_accounts:
                account_id = account['id']
                print(f"\n💳 Processando conta ID {account_id}: {account['nome']}...")
                account_stats = self.migrate_account_history(account_id, batch_id, account)
                total_records += account_stats['total']
                successful_records += account_stats['successful']
                failed_records += account_stats['failed']

            # Atualizar status do lote
            self.db.update_import_batch(
                batch_id=batch_id,
                total_records=total_records,
                successful_records=successful_records,
                failed_records=failed_records,
                status='completed'
            )

            # Mostrar estatísticas finais
            self.show_migration_summary()

            print(f"\n✅ Migração concluída com sucesso!")
            print(f"📊 Total: {total_records} | Sucessos: {successful_records} | Falhas: {failed_records}")

        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            self.db.update_import_batch(batch_id, status='failed', error_log=str(e))
            raise

    def discover_omie_accounts(self):
        """Descobre contas disponíveis usando a API existente e busca descrições"""
        print("🔍 Descobrindo contas disponíveis no Omie...")

        try:
            # Usar método similar ao buscar_contas_omie do app.py
            result = self.omie.omie.listar_contas_correntes(pagina=1, registros_por_pagina=100)

            accounts = []
            if isinstance(result, dict) and 'ListarContasCorrentes' in result:
                for conta in result['ListarContasCorrentes']:
                    account_id = conta.get('nCodCC')
                    account_name = conta.get('descricao', '') or conta.get('cNome', '')

                    # Se não tem nome, buscar descrição via API de extrato
                    if not account_name and account_id:
                        account_name = self.get_account_description_from_api(account_id)

                    # Verificar status da conta
                    is_inactive = conta.get('inativo', 'N') == 'S'
                    is_blocked = conta.get('bloqueado', 'N') == 'S'
                    account_type_code = conta.get('tipo', 'CC')
                    bank_code = conta.get('codigo_banco', '')

                    account_info = {
                        'id': account_id,
                        'nome': account_name or f'Conta {account_id}',
                        'tipo': self.determine_account_type(account_name or '', account_type_code),
                        'banco': self.extract_bank_name(account_name or '', bank_code),
                        'ativo': not is_inactive,
                        'bloqueado': is_blocked,
                        'tipo_omie': account_type_code,
                        'codigo_banco': bank_code
                    }
                    accounts.append(account_info)

                    status_text = ""
                    if is_inactive:
                        status_text += " [INATIVA]"
                    if is_blocked:
                        status_text += " [BLOQUEADA]"

                    print(f"  ✅ Descoberta: ID {account_info['id']} - {account_info['nome']}{status_text}")

            return accounts

        except Exception as e:
            print(f"❌ Erro ao descobrir contas: {e}")
            # Fallback para contas conhecidas
            return [
                {'id': 8, 'nome': 'Conta Corrente Nubank PJ', 'tipo': 'checking', 'banco': 'Nubank'},
                {'id': 9, 'nome': 'Cartão de Crédito Nubank PJ', 'tipo': 'credit', 'banco': 'Nubank'}
            ]

    def get_account_description_from_api(self, account_id: int) -> str:
        """Busca descrição da conta através da API de extrato"""
        try:
            # Fazer uma chamada de extrato pequena para obter informações da conta
            from datetime import date
            hoje = date.today()

            result = self.omie.omie._chamar_api(
                call='ListarExtrato',
                endpoint='financas/extrato/',
                param={
                    'nCodCC': account_id,
                    'dPeriodoInicial': hoje.strftime('%d/%m/%Y'),
                    'dPeriodoFinal': hoje.strftime('%d/%m/%Y')
                }
            )

            if isinstance(result, dict):
                # Extrair descrição da conta
                description = result.get('cDescricao', '')
                if description and description.strip():
                    return description.strip()

                # Se não tem descrição, tentar montar baseado em outras informações
                bank_code = result.get('nCodBanco')
                account_num = result.get('nNumConta')
                account_type = result.get('cDesTipo', '')

                if bank_code or account_num or account_type:
                    parts = []
                    if account_type:
                        parts.append(account_type)
                    if bank_code:
                        parts.append(f"Banco {bank_code}")
                    if account_num:
                        parts.append(f"Conta {account_num}")

                    if parts:
                        return " - ".join(parts)

            return ""

        except Exception as e:
            print(f"    ⚠️ Erro ao buscar descrição da conta {account_id}: {e}")
            return ""

    def determine_account_type(self, account_name: str, account_type_code: str = '') -> str:
        """Determina o tipo da conta baseado no nome e código do Omie"""
        name_lower = account_name.lower()

        # Primeiro, verificar pelo código do Omie
        if account_type_code == 'CC':
            if 'cartão' in name_lower or 'credit' in name_lower or 'mastercard' in name_lower or 'visa' in name_lower:
                return 'credit'
            else:
                return 'checking'
        elif account_type_code == 'CP':
            return 'savings'
        elif account_type_code == 'CX':
            return 'cash'

        # Fallback para análise por nome
        if 'cartão' in name_lower or 'credit' in name_lower or 'mastercard' in name_lower or 'visa' in name_lower:
            return 'credit'
        elif 'corrente' in name_lower or 'checking' in name_lower:
            return 'checking'
        elif 'poupança' in name_lower or 'savings' in name_lower:
            return 'savings'
        elif 'caixinha' in name_lower or 'cash' in name_lower:
            return 'cash'
        elif 'aporte' in name_lower or 'investimento' in name_lower:
            return 'investment'
        else:
            return 'other'

    def extract_bank_name(self, account_name: str, bank_code: str = '') -> str:
        """Extrai o nome do banco da descrição da conta e código"""
        # Mapear códigos de banco conhecidos
        bank_codes = {
            '001': 'Banco do Brasil',
            '033': 'Santander',
            '104': 'Caixa Econômica',
            '237': 'Bradesco',
            '341': 'Itaú',
            '260': 'Nu Pagamentos (Nubank)',
            '077': 'Banco Inter',
            '208': 'BTG Pactual',
            '212': 'Banco Original',
            '290': 'Banco Pagseguro',
            '323': 'Mercado Pago'
        }

        # Verificar pelo código primeiro
        if bank_code and bank_code in bank_codes:
            return bank_codes[bank_code]

        # Fallback para análise por nome
        name_lower = account_name.lower()
        if 'nubank' in name_lower or 'nu pagamentos' in name_lower:
            return 'Nubank'
        elif 'btg' in name_lower or 'pactual' in name_lower:
            return 'BTG Pactual'
        elif 'bradesco' in name_lower:
            return 'Bradesco'
        elif 'itau' in name_lower or 'itaú' in name_lower:
            return 'Itaú'
        elif 'santander' in name_lower:
            return 'Santander'
        elif 'bb' in name_lower or 'brasil' in name_lower:
            return 'Banco do Brasil'
        elif 'cora' in name_lower:
            return 'Cora'
        elif 'inter' in name_lower:
            return 'Banco Inter'
        elif 'mercado' in name_lower:
            return 'Mercado Pago'
        elif 'porto' in name_lower:
            return 'Porto Seguro'
        elif 'omie' in name_lower:
            return 'Omie'
        else:
            return 'Outros'

    def migrate_accounts(self):
        """Migra contas descobertas"""
        print("🏦 Migrando contas...")

        for account in self.discovered_accounts:
            try:
                # Usar a API de insert/update mais completa
                conn = self.db.get_connection()
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO accounts
                    (omie_id, name, type, bank_name, active, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    account['id'],
                    account['nome'],
                    account['tipo'],
                    account['banco'],
                    account.get('ativo', True)
                ))
                conn.commit()
                conn.close()

                status_info = ""
                if not account.get('ativo', True):
                    status_info += " [INATIVA]"
                if account.get('bloqueado', False):
                    status_info += " [BLOQUEADA]"

                print(f"  ✅ Conta {account['id']}: {account['nome']}{status_info}")
            except Exception as e:
                print(f"  ❌ Erro na conta {account['id']}: {e}")

    def migrate_categories(self):
        """Migra categorias do Omie"""
        print("🏷️ Migrando categorias...")

        try:
            # Buscar categorias no Omie
            categories_result = self.omie.omie._chamar_api(
                call='ListarCategorias',
                endpoint='geral/categorias/',
                param={
                    'pagina': 1,
                    'registros_por_pagina': 500,
                    'apenas_importado_api': 'N'
                }
            )

            if categories_result and 'categoria_cadastro' in categories_result:
                categories = categories_result['categoria_cadastro']

                for category in categories:
                    try:
                        # Extrair dados da categoria
                        omie_code = category.get('codigo', '')
                        name = category.get('descricao', '')

                        # Determinar tipo baseado nos flags da categoria
                        if category.get('conta_receita') == 'S':
                            category_type = 'R'  # Receita
                        elif category.get('conta_despesa') == 'S':
                            category_type = 'D'  # Despesa
                        else:
                            category_type = 'N'  # Neutro

                        # Pular categorias inativas ou sem descrição
                        if (omie_code and name and
                            category.get('conta_inativa') != 'S' and
                            not name.startswith('<')):

                            self.db.insert_category(
                                omie_code=omie_code,
                                name=name,
                                category_type=category_type
                            )
                            print(f"  ✅ Categoria {omie_code}: {name} ({category_type})")
                    except Exception as e:
                        print(f"  ❌ Erro na categoria {category}: {e}")

            print(f"📊 Total de categorias migradas: {len(categories) if 'categories' in locals() else 0}")

        except Exception as e:
            print(f"❌ Erro ao migrar categorias: {e}")

    def migrate_clients(self):
        """Migra clientes e fornecedores do Omie"""
        print("👥 Migrando clientes e fornecedores...")

        total_clients = 0

        # Migrar clientes
        try:
            clients_result = self.omie.omie._chamar_api(
                call='ListarClientes',
                endpoint='geral/clientes/',
                param={'pagina': 1, 'registros_por_pagina': 500}
            )

            if clients_result and 'clientes_cadastro' in clients_result:
                clients = clients_result['clientes_cadastro']

                for client in clients:
                    try:
                        omie_id = client.get('codigo_cliente_omie', 0)
                        name = client.get('razao_social', '') or client.get('nome_fantasia', '')
                        email = client.get('email', '')
                        phone = client.get('telefone1_numero', '')

                        if omie_id and name:
                            self.db.insert_client(
                                omie_id=omie_id,
                                name=name,
                                client_type='Cliente',
                                email=email,
                                phone=phone
                            )
                            total_clients += 1
                    except Exception as e:
                        print(f"  ❌ Erro no cliente {client}: {e}")

        except Exception as e:
            print(f"❌ Erro ao migrar clientes: {e}")

        # Migrar fornecedores
        try:
            suppliers_result = self.omie.omie._chamar_api(
                call='ListarFornecedores',
                endpoint='geral/fornecedores/',
                param={'pagina': 1, 'registros_por_pagina': 500}
            )

            if suppliers_result and 'fornecedor_cadastro' in suppliers_result:
                suppliers = suppliers_result['fornecedor_cadastro']

                for supplier in suppliers:
                    try:
                        omie_id = supplier.get('codigo_fornecedor_omie', 0)
                        name = supplier.get('razao_social', '') or supplier.get('nome_fantasia', '')
                        email = supplier.get('email', '')
                        phone = supplier.get('telefone1_numero', '')

                        if omie_id and name:
                            self.db.insert_client(
                                omie_id=omie_id,
                                name=name,
                                client_type='Fornecedor',
                                email=email,
                                phone=phone
                            )
                            total_clients += 1
                    except Exception as e:
                        print(f"  ❌ Erro no fornecedor {supplier}: {e}")

        except Exception as e:
            print(f"❌ Erro ao migrar fornecedores: {e}")

        print(f"📊 Total de clientes/fornecedores migrados: {total_clients}")

    def migrate_account_history(self, account_id: int, batch_id: int, account_info: dict = None) -> dict:
        """Migra histórico de uma conta específica"""
        print(f"💳 Migrando conta {account_id}...")

        # Buscar conta local
        local_account = self.db.get_account_by_omie_id(account_id)
        if not local_account:
            print(f"❌ Conta {account_id} não encontrada no banco local")
            return {'total': 0, 'successful': 0, 'failed': 0}

        total_records = 0
        successful_records = 0
        failed_records = 0

        # Processar mês a mês para evitar timeouts
        current_date = self.start_date

        while current_date <= self.end_date:
            # Calcular fim do mês
            month_end = current_date + relativedelta(months=1) - timedelta(days=1)
            if month_end > self.end_date:
                month_end = self.end_date

            print(f"  📅 Processando {current_date.strftime('%m/%Y')}...")

            month_stats = self.migrate_month_data(
                account_id=account_id,
                local_account_id=local_account['id'],
                start_date=current_date,
                end_date=month_end,
                batch_id=batch_id
            )

            total_records += month_stats['total']
            successful_records += month_stats['successful']
            failed_records += month_stats['failed']

            # Próximo mês
            current_date = current_date + relativedelta(months=1)

            # Pausa para não sobrecarregar API
            time.sleep(1)

        print(f"  📊 Conta {account_id}: {successful_records}/{total_records} transações migradas")

        return {
            'total': total_records,
            'successful': successful_records,
            'failed': failed_records
        }

    def migrate_month_data(self, account_id: int, local_account_id: int, start_date: date,
                          end_date: date, batch_id: int) -> dict:
        """Migra dados de um mês específico"""

        total_records = 0
        successful_records = 0
        failed_records = 0

        try:
            # Formatar datas para API do Omie
            start_str = start_date.strftime('%d/%m/%Y')
            end_str = end_date.strftime('%d/%m/%Y')

            # Chamar API do Omie
            result = self.omie.omie._chamar_api(
                call='ListarExtrato',
                endpoint='financas/extrato/',
                param={
                    'nCodCC': account_id,
                    'dPeriodoInicial': start_str,
                    'dPeriodoFinal': end_str
                }
            )

            if result and 'listaMovimentos' in result:
                movements = result['listaMovimentos']
                total_records = len(movements)

                for movement in movements:
                    try:
                        # Pular saldos e registros que não são transações reais
                        client_name = movement.get('cDesCliente', '')
                        if client_name in ['SALDO ANTERIOR', 'SALDO INICIAL', 'SALDO']:
                            continue

                        # Pular se não tem valor de documento (não é transação real)
                        if not movement.get('nValorDocumento'):
                            continue

                        # Extrair dados da transação
                        transaction_data = self.parse_omie_transaction(movement, local_account_id, batch_id)

                        if transaction_data:
                            # Inserir no banco local
                            self.db.insert_transaction(**transaction_data)
                            successful_records += 1

                    except Exception as e:
                        failed_records += 1
                        print(f"    ❌ Erro na transação {movement}: {e}")

        except Exception as e:
            print(f"    ❌ Erro no mês {start_date}: {e}")
            failed_records = total_records  # Marcar todas como falha

        return {
            'total': total_records,
            'successful': successful_records,
            'failed': failed_records
        }

    def parse_omie_transaction(self, movement: dict, local_account_id: int, batch_id: int) -> dict:
        """Converte transação do Omie para formato local"""
        try:
            # Dados básicos (nova estrutura API)
            omie_code = str(movement.get('nCodLancamento', movement.get('nCodMovCC', '')))
            date_str = movement.get('dDataLancamento', movement.get('dDataMovimento', ''))
            description = movement.get('cDesCliente', '') or movement.get('cRazCliente', '') or movement.get('cHistorico', '')
            amount = float(movement.get('nValorDocumento', movement.get('nValorMovimento', 0)))
            balance = float(movement.get('nSaldo', movement.get('nSaldoCC', 0)))

            # Converter data
            if date_str:
                transaction_date = datetime.strptime(date_str, '%d/%m/%Y').date()
            else:
                return None

            # Determinar tipo (crédito/débito)
            transaction_type = 'credit' if amount > 0 else 'debit'
            amount = abs(amount)  # Armazenar sempre como positivo

            # Buscar categoria pelo código
            category_id = None
            categoria_codigo = movement.get('cCodCategoria', '')
            if categoria_codigo:
                category = self.db.get_category_by_omie_code(categoria_codigo)
                if category:
                    category_id = category['id']

            # Buscar cliente pelo código Omie
            client_id = None
            client_omie_id = movement.get('nCodCliente')
            if client_omie_id:
                client = self.db.get_client_by_omie_id(client_omie_id)
                if client:
                    client_id = client['id']

            # Dados adicionais
            document_number = movement.get('cParcela', '') or movement.get('nNumDocumento', '')

            return {
                'account_id': local_account_id,
                'date': transaction_date,
                'description': description,
                'amount': amount,
                'transaction_type': transaction_type,
                'balance': balance,
                'category_id': category_id,
                'client_id': client_id,
                'omie_code': omie_code,
                'document_number': document_number,
                'import_batch_id': batch_id
            }

        except Exception as e:
            print(f"    ❌ Erro ao parsear transação: {e}")
            print(f"    📊 Dados da transação: {movement}")
            return None

    def show_migration_summary(self):
        """Mostra resumo da migração"""
        print("\n📊 RESUMO DA MIGRAÇÃO")
        print("=" * 50)

        stats = self.db.get_statistics()

        print(f"🏦 Contas ativas: {stats['total_accounts']}")
        print(f"🏷️ Categorias ativas: {stats['total_categories']}")
        print(f"👥 Clientes/Fornecedores: {stats['total_clients']}")
        print(f"💰 Total de transações: {stats['total_transactions']}")

        if stats['date_range']['start'] and stats['date_range']['end']:
            print(f"📅 Período dos dados: {stats['date_range']['start']} até {stats['date_range']['end']}")

        print("\n🔄 Status de conciliação:")
        for status, count in stats['reconciliation_status'].items():
            print(f"  {status}: {count}")

def main():
    """Função principal"""
    print("🚀 Iniciando migração completa do Omie...")

    try:
        migration = OmieMigration()
        migration.run_full_migration()

    except KeyboardInterrupt:
        print("\n⚠️ Migração cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal na migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()