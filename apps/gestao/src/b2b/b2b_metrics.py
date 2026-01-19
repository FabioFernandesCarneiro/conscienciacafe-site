#!/usr/bin/env python3
"""
Módulo de Métricas B2B
Calcula métricas essenciais para vendas B2B
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np

class B2BMetrics:
    def __init__(self):
        self.today = datetime.now().date()
        
    def calculate_inactive_clients(
        self,
        sales_data: List[Dict],
        days_threshold: int = 30,
        *,
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calcula clientes que não compraram no período especificado
        
        Args:
            sales_data: Lista de vendas com formato [{'cliente': str, 'data': str, 'valor': float}]
            days_threshold: Dias sem compra para considerar inativo (default: 30)
        """
        reference = reference_date or datetime.now()
        today = reference.date()

        if not sales_data:
            return {
                'inactive_clients': [],
                'total_inactive': 0,
                'total_clients': 0,
                'inactive_percentage': 0,
                'threshold_days': days_threshold,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'new_clients_count': 0,
                'new_clients_list': []
            }
        
        try:
            df = pd.DataFrame(sales_data)
            df['data'] = pd.to_datetime(df['data'])
            # Normalizar nomes de clientes para comparação case insensitive
            df['cliente'] = df['cliente'].str.strip().str.title()

            # Para B2B, considerar clientes inativos se não compraram no mês atual
            # Sempre usar data atual real, não cached
            cutoff_date = reference.replace(day=1).date()
            
            print(f"🎯 Considerando clientes inativos que não compraram desde: {cutoff_date}")
            
            # Última compra por cliente
            last_purchase = df.groupby('cliente')['data'].max().reset_index()
            last_purchase.columns = ['cliente', 'ultima_compra']
            
            # Clientes inativos
            inactive_clients = last_purchase[
                last_purchase['ultima_compra'].dt.date < cutoff_date
            ].copy()
            
            # Processar apenas se há clientes inativos
            inactive_list = []
            high_risk = medium_risk = low_risk = 0
            
            if not inactive_clients.empty:
                # Calcular valor histórico
                client_totals = df.groupby('cliente')['valor'].agg(['sum', 'count']).reset_index()
                client_totals.columns = ['cliente', 'valor_total_historico', 'numero_compras']
                
                for _, row in inactive_clients.iterrows():
                    cliente = row['cliente']
                    ultima_compra = row['ultima_compra']
                    
                    # Calcular dias sem comprar
                    dias_sem_comprar = (today - ultima_compra.date()).days
                    
                    # Obter histórico do cliente
                    client_total = client_totals[client_totals['cliente'] == cliente]
                    valor_total = float(client_total['valor_total_historico'].iloc[0]) if not client_total.empty else 0
                    num_compras = int(client_total['numero_compras'].iloc[0]) if not client_total.empty else 0
                    
                    # Classificar risco
                    risco = self._classify_churn_risk(dias_sem_comprar)
                    if risco == 'Alto':
                        high_risk += 1
                    elif risco == 'Médio':
                        medium_risk += 1
                    else:
                        low_risk += 1
                    
                    inactive_list.append({
                        'cliente': cliente,
                        'ultima_compra': ultima_compra.strftime('%Y-%m-%d'),
                        'dias_sem_comprar': dias_sem_comprar,
                        'valor_total_historico': valor_total,
                        'numero_compras': num_compras,
                        'risco_churn': risco
                    })
            
            # Calcular novos clientes do mês atual (sempre data atual real)
            current_month_start = reference.replace(day=1).date()
            
            # Primeira compra por cliente
            first_purchase = df.groupby('cliente')['data'].min().reset_index()
            first_purchase.columns = ['cliente', 'primeira_compra']
            
            # Clientes novos (primeira compra no mês atual)
            new_clients = first_purchase[
                first_purchase['primeira_compra'].dt.date >= current_month_start
            ]
            
            print(f"📈 {len(new_clients)} novos clientes no mês atual")
            
            return {
                'inactive_clients': inactive_list,
                'total_inactive': len(inactive_clients),
                'total_clients': len(last_purchase),
                'inactive_percentage': (len(inactive_clients) / len(last_purchase)) * 100 if len(last_purchase) > 0 else 0,
                'threshold_days': days_threshold,
                'high_risk_count': high_risk,
                'medium_risk_count': medium_risk,
                'low_risk_count': low_risk,
                'new_clients_count': len(new_clients),
                'new_clients_list': new_clients['cliente'].tolist() if not new_clients.empty else []
            }
            
        except Exception as e:
            print(f"❌ Erro ao calcular clientes inativos: {e}")
            return {
                'inactive_clients': [],
                'total_inactive': 0,
                'total_clients': 0,
                'inactive_percentage': 0,
                'threshold_days': days_threshold,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'new_clients_count': 0,
                'new_clients_list': []
            }
    
    def calculate_monthly_revenue(
        self,
        sales_data: List[Dict],
        *,
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Calcula receita mensal e tendências"""
        if not sales_data:
            return {
                'monthly_data': [],
                'current_month': 0,
                'previous_month': 0,
                'growth_percentage': 0,
                'total_revenue': 0
            }

        df = pd.DataFrame(sales_data)
        df['data'] = pd.to_datetime(df['data'])
        # Normalizar nomes de clientes para comparação case insensitive
        df['cliente'] = df['cliente'].str.strip().str.title()
        df['mes_ano'] = df['data'].dt.to_period('M')
        
        # Receita por mês
        monthly_revenue = df.groupby('mes_ano')['valor'].sum().reset_index()
        monthly_revenue['mes_ano_str'] = monthly_revenue['mes_ano'].astype(str)
        
        # Converter Period para string para serialização JSON
        monthly_revenue['mes_ano'] = monthly_revenue['mes_ano'].astype(str)
        
        # Mês atual e anterior (sempre usar data atual real)
        reference = reference_date or datetime.now()
        current_month = pd.Period(reference.date(), freq='M')
        previous_month = current_month - 1
        
        # Converter para string para comparação
        current_month_str = str(current_month)
        previous_month_str = str(previous_month)
        
        current_revenue = monthly_revenue[
            monthly_revenue['mes_ano'] == current_month_str
        ]['valor'].sum() if len(monthly_revenue[monthly_revenue['mes_ano'] == current_month_str]) > 0 else 0
        
        previous_revenue = monthly_revenue[
            monthly_revenue['mes_ano'] == previous_month_str
        ]['valor'].sum() if len(monthly_revenue[monthly_revenue['mes_ano'] == previous_month_str]) > 0 else 0
        
        # Cálculo de crescimento
        growth = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        
        # Calcular volume mensal (quantidade em Kg)
        monthly_volume = df.groupby('mes_ano')['quantidade'].sum().reset_index()
        monthly_volume['mes_ano_str'] = monthly_volume['mes_ano'].astype(str)
        monthly_volume['mes_ano'] = monthly_volume['mes_ano'].astype(str)
        
        # Volume atual e anterior
        current_volume = monthly_volume[
            monthly_volume['mes_ano'] == current_month_str
        ]['quantidade'].sum() if len(monthly_volume[monthly_volume['mes_ano'] == current_month_str]) > 0 else 0
        
        previous_volume = monthly_volume[
            monthly_volume['mes_ano'] == previous_month_str
        ]['quantidade'].sum() if len(monthly_volume[monthly_volume['mes_ano'] == previous_month_str]) > 0 else 0
        
        # Crescimento de volume
        volume_growth = ((current_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0
        
        return {
            'monthly_data': monthly_revenue.to_dict('records'),
            'monthly_volume_data': monthly_volume.to_dict('records'),
            'current_month': float(current_revenue),
            'previous_month': float(previous_revenue),
            'growth_percentage': float(growth),
            'total_revenue': float(df['valor'].sum()),
            'current_volume': float(current_volume),
            'previous_volume': float(previous_volume),
            'volume_growth_percentage': float(volume_growth),
            'total_volume': float(df['quantidade'].sum())
        }
    
    def calculate_top_clients(self, sales_data: List[Dict], top_n: int = 5) -> List[Dict]:
        """Calcula top clientes por receita"""
        if not sales_data:
            return []
        
        try:
            df = pd.DataFrame(sales_data)
            df['data'] = pd.to_datetime(df['data'])
            # Normalizar nomes de clientes para comparação case insensitive
            df['cliente'] = df['cliente'].str.strip().str.title()

            # Calcular métricas por cliente
            client_metrics = df.groupby('cliente').agg({
                'valor': ['sum', 'count', 'mean'],
                'data': 'max'
            }).reset_index()
            
            # Renomear colunas
            client_metrics.columns = ['cliente', 'receita_total', 'numero_compras', 'ticket_medio', 'ultima_compra']
            
            # Ordenar por receita e pegar top N
            top_clients = client_metrics.sort_values('receita_total', ascending=False).head(top_n)
            
            # Converter para lista de dicts com formatação segura
            result = []
            for _, row in top_clients.iterrows():
                result.append({
                    'cliente': row['cliente'],
                    'receita_total': float(row['receita_total']),
                    'numero_compras': int(row['numero_compras']),
                    'ticket_medio': float(row['ticket_medio']),
                    'ultima_compra': row['ultima_compra'].strftime('%Y-%m-%d')
                })
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao calcular top clientes: {e}")
            return []
    
    def calculate_sales_forecast(self, sales_data: List[Dict], months_ahead: int = 3) -> Dict[str, Any]:
        """Previsão simples de vendas baseada em tendência histórica"""
        if not sales_data:
            return {'forecast': [], 'trend': 'estável'}
        
        df = pd.DataFrame(sales_data)
        df['data'] = pd.to_datetime(df['data'])
        # Normalizar nomes de clientes para comparação case insensitive
        df['cliente'] = df['cliente'].str.strip().str.title()
        df['mes_ano'] = df['data'].dt.to_period('M')
        
        monthly_revenue = df.groupby('mes_ano')['valor'].sum()
        
        if len(monthly_revenue) < 3:
            return {'forecast': [], 'trend': 'dados insuficientes'}
        
        # Tendência simples (últimos 3 meses)
        recent_months = monthly_revenue.tail(3).values
        trend_slope = np.polyfit(range(len(recent_months)), recent_months, 1)[0]
        
        # Classificar tendência
        if trend_slope > 1000:
            trend = 'crescimento'
        elif trend_slope < -1000:
            trend = 'declínio'
        else:
            trend = 'estável'
        
        # Previsão simples
        last_value = recent_months[-1]
        forecast = []
        
        for i in range(1, months_ahead + 1):
            predicted_value = max(0, last_value + (trend_slope * i))
            future_month = pd.Period(self.today, freq='M') + i
            forecast.append({
                'mes': str(future_month),
                'valor_previsto': predicted_value
            })
        
        return {
            'forecast': forecast,
            'trend': trend,
            'trend_value': trend_slope
        }
    
    def _classify_churn_risk(self, days_inactive: int) -> str:
        """Classifica risco de churn baseado em dias sem comprar - mais sensível para B2B"""
        if days_inactive >= 60:  # 2 meses = Alto risco
            return 'Alto'
        elif days_inactive >= 45:  # 1.5 mês = Médio risco
            return 'Médio'
        else:  # Menos de 1.5 mês = Baixo risco
            return 'Baixo'
    
    def calculate_client_lifetime_value(self, sales_data: List[Dict]) -> Dict[str, Any]:
        """Calcula LTV médio dos clientes"""
        if not sales_data:
            return {'average_ltv': 0, 'median_ltv': 0, 'ltv_distribution': []}
        
        df = pd.DataFrame(sales_data)
        df['data'] = pd.to_datetime(df['data'])
        # Normalizar nomes de clientes para comparação case insensitive
        df['cliente'] = df['cliente'].str.strip().str.title()

        # LTV por cliente (soma total de compras)
        client_ltv = df.groupby('cliente')['valor'].sum().reset_index()
        client_ltv.columns = ['cliente', 'ltv']
        
        # Calcular ticket médio real (valor médio por transação)
        avg_transaction_value = df['valor'].mean()
        
        return {
            'average_ltv': client_ltv['ltv'].mean(),
            'median_ltv': client_ltv['ltv'].median(),
            'ltv_distribution': client_ltv.to_dict('records'),
            'average_transaction_value': float(avg_transaction_value)
        }
    
    def calculate_country_metrics(
        self,
        sales_data: List[Dict],
        *,
        reference_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Calcula métricas por país"""
        if not sales_data:
            return {
                'countries_revenue': [],
                'countries_volume': [],
                'monthly_by_country': [],
                'total_by_country': {}
            }
        
        try:
            df = pd.DataFrame(sales_data)
            df['data'] = pd.to_datetime(df['data'])
            # Normalizar nomes de clientes para comparação case insensitive
            df['cliente'] = df['cliente'].str.strip().str.title()

            if 'pais' in df.columns:
                df['pais'] = df['pais'].fillna('Brasil').astype(str).str.strip()
            else:
                # Extrair país das observações (formato: "Venda MM/YYYY - País")
                extracted = df['observacoes'].str.extract(r'-\s*([^|\n]+)')
                df['pais'] = extracted[0].fillna('Brasil').astype(str).str.strip()
            df['mes_ano'] = df['data'].dt.to_period('M')
            
            # Receita por país
            countries_revenue = df.groupby('pais')['valor'].sum().reset_index()
            total_value = countries_revenue['valor'].sum()
            if total_value:
                countries_revenue['percentual'] = (countries_revenue['valor'] / total_value * 100).round(2)
            else:
                countries_revenue['percentual'] = 0.0
            
            # Volume por país
            countries_volume = df.groupby('pais')['quantidade'].sum().reset_index()
            
            # Evolução mensal por país
            monthly_by_country = df.groupby(['mes_ano', 'pais']).agg({
                'valor': 'sum',
                'quantidade': 'sum'
            }).reset_index()
            monthly_by_country['mes_ano'] = monthly_by_country['mes_ano'].astype(str)
            
            # Mês atual por país (sempre usar data atual real)
            reference = reference_date or datetime.now()
            current_month = pd.Period(reference.date(), freq='M')
            current_month_str = str(current_month)
            
            current_month_data = monthly_by_country[
                monthly_by_country['mes_ano'] == current_month_str
            ]
            
            total_by_country = {}
            for _, row in countries_revenue.iterrows():
                pais = row['pais']
                current_country_data = current_month_data[current_month_data['pais'] == pais]
                
                receita_total = float(row['valor'])
                receita_mes = float(current_country_data['valor'].sum()) if not current_country_data.empty else receita_total
                volume_total = float(countries_volume[countries_volume['pais'] == pais]['quantidade'].sum()) if not countries_volume.empty else 0.0
                volume_mes = float(current_country_data['quantidade'].sum()) if not current_country_data.empty else volume_total

                total_by_country[pais] = {
                    'receita_total': receita_mes,
                    'percentual_receita': float(row['percentual']),
                    'receita_mes_atual': receita_mes,
                    'volume_total': volume_total,
                    'volume_mes_atual': volume_mes
                }
            
            print(f"🌎 Análise por países: {list(total_by_country.keys())}")
            
            return {
                'countries_revenue': countries_revenue.to_dict('records'),
                'countries_volume': countries_volume.to_dict('records'), 
                'monthly_by_country': monthly_by_country.to_dict('records'),
                'total_by_country': total_by_country
            }
            
        except Exception as e:
            print(f"❌ Erro ao calcular métricas por país: {e}")
            return {
                'countries_revenue': [],
                'countries_volume': [],
                'monthly_by_country': [],
                'total_by_country': {}
            }
