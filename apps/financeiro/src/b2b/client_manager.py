"""
Gerenciador de clientes B2B integrado com dados do Omie
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ..omie_client import OmieClient

class ClientManager:
    """
    Gerenciador de clientes B2B que integra dados do Omie com análises específicas
    """
    
    def __init__(self, omie_client: OmieClient = None):
        self.omie_client = omie_client
        self.client_cache = {}
        self.cache_duration = 3600  # 1 hora
    
    def get_client_list(self, include_inactive: bool = True) -> List[Dict[str, Any]]:
        """
        Obtém lista de todos os clientes do Omie com informações enriquecidas
        """
        try:
            if not self.omie_client:
                return self._get_mock_clients()
            
            # Buscar clientes do Omie
            clients_data = self._fetch_omie_clients()
            
            # Enriquecer com dados de vendas
            enriched_clients = []
            for client in clients_data:
                enriched_client = self._enrich_client_data(client)
                
                if include_inactive or enriched_client.get('active', True):
                    enriched_clients.append(enriched_client)
            
            return sorted(enriched_clients, key=lambda x: x.get('last_purchase_date', ''), reverse=True)
            
        except Exception as e:
            print(f"❌ Erro ao obter lista de clientes: {e}")
            return self._get_mock_clients()
    
    def get_client_details(self, client_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes completos de um cliente específico
        """
        try:
            if not self.omie_client:
                return self._get_mock_client_details(client_id)
            
            # Buscar dados básicos do cliente no Omie
            client_info = self._fetch_single_client(client_id)
            
            if not client_info:
                return {'error': 'Cliente não encontrado'}
            
            # Buscar histórico de transações
            transaction_history = self._get_client_transactions(client_id)
            
            # Calcular métricas do cliente
            client_metrics = self._calculate_client_metrics(transaction_history)
            
            return {
                'client_info': client_info,
                'metrics': client_metrics,
                'transaction_history': transaction_history,
                'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
            
        except Exception as e:
            print(f"❌ Erro ao obter detalhes do cliente {client_id}: {e}")
            return {'error': str(e)}
    
    def get_inactive_clients(self, days_threshold: int = 60) -> List[Dict[str, Any]]:
        """
        Identifica clientes inativos (sem compras no período especificado)
        """
        try:
            all_clients = self.get_client_list(include_inactive=True)
            
            cutoff_date = datetime.now() - timedelta(days=days_threshold)
            inactive_clients = []
            
            for client in all_clients:
                last_purchase = client.get('last_purchase_date')
                if last_purchase:
                    try:
                        last_purchase_date = datetime.strptime(last_purchase, '%d/%m/%Y')
                        if last_purchase_date < cutoff_date:
                            inactive_clients.append({
                                **client,
                                'days_inactive': (datetime.now() - last_purchase_date).days,
                                'risk_level': self._calculate_churn_risk(
                                    (datetime.now() - last_purchase_date).days
                                )
                            })
                    except ValueError:
                        # Se não conseguir converter data, considerar inativo
                        inactive_clients.append({
                            **client,
                            'days_inactive': days_threshold + 1,
                            'risk_level': 'high'
                        })
                else:
                    # Cliente sem histórico de compras
                    inactive_clients.append({
                        **client,
                        'days_inactive': 9999,
                        'risk_level': 'high'
                    })
            
            # Ordenar por valor total decrescente (clientes de maior valor primeiro)
            return sorted(inactive_clients, key=lambda x: x.get('total_revenue', 0), reverse=True)
            
        except Exception as e:
            print(f"❌ Erro ao identificar clientes inativos: {e}")
            return []
    
    def get_high_value_clients(self, min_revenue: float = 5000) -> List[Dict[str, Any]]:
        """
        Identifica clientes de alto valor
        """
        try:
            all_clients = self.get_client_list()
            
            high_value_clients = [
                client for client in all_clients 
                if client.get('total_revenue', 0) >= min_revenue
            ]
            
            return sorted(high_value_clients, key=lambda x: x.get('total_revenue', 0), reverse=True)
            
        except Exception as e:
            print(f"❌ Erro ao identificar clientes de alto valor: {e}")
            return []
    
    def _fetch_omie_clients(self) -> List[Dict[str, Any]]:
        """
        Busca clientes do Omie via API
        """
        try:
            # Usar método existente do omie_client se disponível
            result = self.omie_client.omie._chamar_api(
                call='ListarClientes',
                endpoint='geral/clientes/',
                param={'pagina': 1, 'registros_por_pagina': 500}
            )
            
            clients = []
            if isinstance(result, dict) and 'clientes_cadastro' in result:
                for client in result['clientes_cadastro']:
                    clients.append({
                        'id': client.get('codigo_cliente_omie', ''),
                        'name': client.get('razao_social', client.get('nome_fantasia', '')),
                        'cnpj_cpf': client.get('cnpj_cpf', ''),
                        'email': client.get('email', ''),
                        'phone': client.get('telefone1_numero', ''),
                        'active': client.get('inativo', 'N') == 'N',
                        'registration_date': client.get('data_cadastro', ''),
                        'city': client.get('cidade', ''),
                        'state': client.get('estado', '')
                    })
            
            return clients
            
        except Exception as e:
            print(f"❌ Erro ao buscar clientes do Omie: {e}")
            return []
    
    def _fetch_single_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca um cliente específico do Omie
        """
        try:
            all_clients = self._fetch_omie_clients()
            return next((c for c in all_clients if str(c['id']) == str(client_id)), None)
            
        except Exception as e:
            print(f"❌ Erro ao buscar cliente {client_id}: {e}")
            return None
    
    def _get_client_transactions(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Obtém histórico de transações de um cliente específico
        """
        try:
            # Buscar lançamentos dos últimos 12 meses
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            result = self.omie_client.omie.listar_lanc_c_c(
                nPagina=1,
                nRegPorPagina=500,
                dtPagInicial=start_date.strftime('%d/%m/%Y'),
                dtPagFinal=end_date.strftime('%d/%m/%Y')
            )
            
            transactions = []
            if isinstance(result, dict) and 'listaLancamentos' in result:
                for lanc in result['listaLancamentos']:
                    cabecalho = lanc.get('cabecalho', {})
                    
                    # Filtrar apenas transações deste cliente
                    if str(cabecalho.get('nCodCliente', '')) == str(client_id):
                        transactions.append({
                            'date': cabecalho.get('dDataLanc', ''),
                            'value': float(cabecalho.get('nValor', 0)),
                            'description': cabecalho.get('cDescLanc', ''),
                            'category': cabecalho.get('cCodCateg', ''),
                            'document': cabecalho.get('cNumDoc', ''),
                            'type': 'credit' if float(cabecalho.get('nValor', 0)) > 0 else 'debit'
                        })
            
            # Ordenar por data (mais recente primeiro)
            return sorted(transactions, key=lambda x: x['date'], reverse=True)
            
        except Exception as e:
            print(f"❌ Erro ao buscar transações do cliente {client_id}: {e}")
            return []
    
    def _enrich_client_data(self, client: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece dados do cliente com métricas calculadas
        """
        try:
            client_id = client['id']
            transactions = self._get_client_transactions(client_id)
            
            if not transactions:
                return {
                    **client,
                    'total_revenue': 0,
                    'total_orders': 0,
                    'avg_order_value': 0,
                    'last_purchase_date': None,
                    'purchase_frequency': 0
                }
            
            # Calcular métricas
            total_revenue = sum(t['value'] for t in transactions if t['type'] == 'credit')
            total_orders = len([t for t in transactions if t['type'] == 'credit'])
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Última compra
            credit_transactions = [t for t in transactions if t['type'] == 'credit']
            last_purchase_date = credit_transactions[0]['date'] if credit_transactions else None
            
            # Frequência de compra (aproximada)
            if len(credit_transactions) > 1 and last_purchase_date:
                date_range_days = (datetime.strptime(credit_transactions[0]['date'], '%d/%m/%Y') - 
                                 datetime.strptime(credit_transactions[-1]['date'], '%d/%m/%Y')).days
                purchase_frequency = total_orders / max(date_range_days / 30, 1) if date_range_days > 0 else 0
            else:
                purchase_frequency = 0
            
            return {
                **client,
                'total_revenue': total_revenue,
                'total_orders': total_orders,
                'avg_order_value': avg_order_value,
                'last_purchase_date': last_purchase_date,
                'purchase_frequency': round(purchase_frequency, 2)
            }
            
        except Exception as e:
            print(f"❌ Erro ao enriquecer dados do cliente: {e}")
            return client
    
    def _calculate_client_metrics(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula métricas específicas de um cliente
        """
        try:
            if not transactions:
                return {'error': 'Sem transações para calcular métricas'}
            
            credit_transactions = [t for t in transactions if t['type'] == 'credit']
            
            total_revenue = sum(t['value'] for t in credit_transactions)
            total_orders = len(credit_transactions)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Calcular LTV estimado
            if total_orders > 1:
                first_purchase = datetime.strptime(credit_transactions[-1]['date'], '%d/%m/%Y')
                last_purchase = datetime.strptime(credit_transactions[0]['date'], '%d/%m/%Y')
                customer_lifespan_months = max((last_purchase - first_purchase).days / 30, 1)
                monthly_value = total_revenue / customer_lifespan_months
                estimated_ltv = monthly_value * 24  # Estimativa de 2 anos
            else:
                estimated_ltv = total_revenue
            
            return {
                'total_revenue': total_revenue,
                'total_revenue_formatted': f"R$ {total_revenue:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'total_orders': total_orders,
                'avg_order_value': avg_order_value,
                'avg_order_value_formatted': f"R$ {avg_order_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'estimated_ltv': estimated_ltv,
                'estimated_ltv_formatted': f"R$ {estimated_ltv:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            }
            
        except Exception as e:
            print(f"❌ Erro ao calcular métricas do cliente: {e}")
            return {'error': str(e)}
    
    def _calculate_churn_risk(self, days_inactive: int) -> str:
        """
        Calcula nível de risco de churn baseado em dias de inatividade
        """
        if days_inactive <= 30:
            return 'low'
        elif days_inactive <= 90:
            return 'medium'
        else:
            return 'high'
    
    def _get_mock_clients(self) -> List[Dict[str, Any]]:
        """
        Retorna dados mock de clientes para desenvolvimento
        """
        return [
            {
                'id': '12345',
                'name': 'Empresa ABC Ltda',
                'cnpj_cpf': '12.345.678/0001-90',
                'email': 'contato@abc.com',
                'phone': '(11) 9999-1111',
                'active': True,
                'total_revenue': 15000.00,
                'total_orders': 8,
                'avg_order_value': 1875.00,
                'last_purchase_date': '15/12/2024',
                'purchase_frequency': 2.1
            },
            {
                'id': '67890',
                'name': 'Comércio XYZ S.A.',
                'cnpj_cpf': '98.765.432/0001-10',
                'email': 'vendas@xyz.com',
                'phone': '(11) 8888-2222',
                'active': True,
                'total_revenue': 8500.00,
                'total_orders': 5,
                'avg_order_value': 1700.00,
                'last_purchase_date': '28/11/2024',
                'purchase_frequency': 1.5
            }
        ]
    
    def _get_mock_client_details(self, client_id: str) -> Dict[str, Any]:
        """
        Retorna detalhes mock de um cliente específico
        """
        mock_clients = self._get_mock_clients()
        client = next((c for c in mock_clients if c['id'] == client_id), None)
        
        if not client:
            return {'error': 'Cliente não encontrado'}
        
        return {
            'client_info': client,
            'metrics': {
                'total_revenue': client['total_revenue'],
                'total_revenue_formatted': f"R$ {client['total_revenue']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'total_orders': client['total_orders'],
                'avg_order_value': client['avg_order_value'],
                'avg_order_value_formatted': f"R$ {client['avg_order_value']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'estimated_ltv': client['total_revenue'] * 1.5,
                'estimated_ltv_formatted': f"R$ {client['total_revenue'] * 1.5:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            },
            'transaction_history': [
                {
                    'date': '15/12/2024',
                    'value': 2500.00,
                    'description': 'Venda de produto/serviço',
                    'type': 'credit'
                },
                {
                    'date': '10/11/2024',
                    'value': 1800.00,
                    'description': 'Venda de produto/serviço',
                    'type': 'credit'
                }
            ],
            'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M')
        }