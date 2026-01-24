"""B2B sales analyzer powered by database-backed order data."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sqlalchemy import func

import pandas as pd

from ..db import session_scope
from ..models import CRMLead
from .b2b_metrics import B2BMetrics
from .sales_repository import SalesRepository

if TYPE_CHECKING:
    from .crm_service import CRMService


@dataclass
class ClientMetric:
    client_id: str
    name: str
    total_revenue: float
    total_orders: int
    avg_order_value: float
    purchase_frequency: float
    days_since_last_purchase: int
    churn_risk: str
    ltv: float


class SalesAnalyzer:
    """Primary analytics façade for the B2B dashboard."""

    CURRENCY_SYMBOLS = {'BRL': 'R$', 'PYG': '₲'}

    def __init__(
        self,
        sales_repository: Optional[SalesRepository] = None,
        crm_service: Optional['CRMService'] = None,
        target_currency: str = 'BRL',
    ) -> None:
        self._target_currency = target_currency.upper() if target_currency else 'BRL'
        self.repository = sales_repository or SalesRepository()
        self.metrics_calculator = B2BMetrics()
        self.crm_service = crm_service
        self.cache_duration = 300  # seconds
        self._last_cache_update: Optional[datetime] = None
        self._cached_data: Optional[pd.DataFrame] = None
        self._cache_window: Tuple[Optional[date], Optional[date]] = (None, None)
        self._cache_user_id: Optional[int] = None
        self.data_source_label = "Banco de dados"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_sales_summary(self, period_days: int = 30, user_id: Optional[int] = None) -> Dict[str, Any]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        period_frame = self._get_sales_data(start_date, end_date, user_id=user_id)
        if period_frame.empty:
            return self._get_empty_summary()

        full_frame = self.repository.fetch_sales_dataframe(user_id=user_id)
        full_records = full_frame.to_dict("records")

        inactive_metrics = self.metrics_calculator.calculate_inactive_clients(
            full_records,
            days_threshold=period_days,
            reference_date=end_date,
        )
        monthly_revenue = self.metrics_calculator.calculate_monthly_revenue(
            full_records,
            reference_date=end_date,
        )
        top_clients = self.metrics_calculator.calculate_top_clients(full_records, top_n=5)
        ltv_metrics = self.metrics_calculator.calculate_client_lifetime_value(full_records)
        forecast = self.metrics_calculator.calculate_sales_forecast(full_records, months_ahead=3)

        summary = self._calculate_summary_metrics(period_frame, inactive_metrics, monthly_revenue)

        return {
            'summary': summary,
            'inactive_clients': inactive_metrics.get('inactive_clients', [])[:10],
            'top_clients': top_clients,
            'trends': self._build_trends(monthly_revenue),
            'alerts': self._build_alerts(inactive_metrics, forecast),
            'period': {
                'start': start_date.strftime('%d/%m/%Y'),
                'end': end_date.strftime('%d/%m/%Y'),
                'days': period_days,
            },
            'data_source': 'database',
            'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'ltv': ltv_metrics,
            'forecast': forecast,
        }

    def get_client_analysis(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        frame = self._get_sales_data(start_date, end_date)

        if frame.empty:
            return {'error': 'Nenhum dado de vendas disponível'}

        metrics = self._calculate_client_metrics(frame)

        if client_id:
            metric = next((m for m in metrics if m.client_id == str(client_id)), None)
            if not metric:
                return {'error': 'Cliente não encontrado nos dados de vendas'}

            client_frame = frame[frame['client_id'] == metric.client_id].sort_values('date')
            purchase_history = [
                {
                    'date': row['date'].strftime('%d/%m/%Y'),
                    'value': float(row['valor']),
                    'product': row.get('produto', ''),
                    'value_formatted': self._format_currency(row['valor']),
                }
                for _, row in client_frame.iterrows()
            ]

            return {
                'client_info': {
                    'id': metric.client_id,
                    'name': metric.name,
                    'total_revenue': metric.total_revenue,
                    'total_orders': metric.total_orders,
                    'avg_order_value': metric.avg_order_value,
                    'purchase_frequency': metric.purchase_frequency,
                    'days_since_last_purchase': metric.days_since_last_purchase,
                    'churn_risk': metric.churn_risk,
                    'ltv': metric.ltv,
                },
                'purchase_history': purchase_history,
            }

        return {
            'total_clients': len(metrics),
            'clients': [
                {
                    'id': metric.client_id,
                    'name': metric.name,
                    'total_revenue': metric.total_revenue,
                    'total_orders': metric.total_orders,
                    'avg_order_value': metric.avg_order_value,
                    'days_since_last_purchase': metric.days_since_last_purchase,
                    'churn_risk': metric.churn_risk,
                    'ltv': metric.ltv,
                }
                for metric in metrics
            ],
        }

    def get_sales_forecast(self, months_ahead: int = 3) -> Dict[str, Any]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        frame = self._get_sales_data(start_date, end_date)

        if frame.empty:
            return {'error': 'Dados insuficientes para previsão'}

        records = frame.to_dict('records')
        forecast = self.metrics_calculator.calculate_sales_forecast(records, months_ahead)
        return {'forecast': forecast.get('forecast', []), 'trend': forecast.get('trend')}

    def get_dashboard_data(
        self,
        reference_month: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        frame = self.repository.fetch_sales_dataframe(user_id=user_id)
        if frame.empty:
            return self._get_empty_dashboard_data()

        month_start, month_end = self._resolve_month_window(reference_month)

        full_records = frame.to_dict('records')
        selected_mask = (frame['date'] >= month_start) & (frame['date'] <= month_end)
        selected_frame = frame[selected_mask]
        selected_records = selected_frame.to_dict('records')

        inactive_metrics = self.metrics_calculator.calculate_inactive_clients(
            full_records,
            days_threshold=60,
            reference_date=month_end,
        )
        monthly_revenue_all = self.metrics_calculator.calculate_monthly_revenue(
            full_records,
            reference_date=month_end,
        )
        monthly_revenue = self._build_monthly_revenue_view(monthly_revenue_all, month_start)
        # Top clientes no período total (não só mês selecionado), top 10
        top_clients = self.metrics_calculator.calculate_top_clients(full_records, top_n=10)
        ltv_metrics = self.metrics_calculator.calculate_client_lifetime_value(selected_records)
        ltv_metrics.setdefault('average_transaction_value', float(selected_frame['valor'].mean()) if not selected_frame.empty else 0.0)
        ltv_metrics.setdefault('trend', 'Estável')

        forecast = self.metrics_calculator.calculate_sales_forecast(full_records, months_ahead=3)
        base_country_metrics = self.metrics_calculator.calculate_country_metrics(
            full_records,
            reference_date=month_end,
        )
        country_metrics = self._build_country_metrics(base_country_metrics, selected_frame)

        lead_funnel = self._build_lead_funnel(month_start, month_end)

        metrics = {
            'inactive_clients': inactive_metrics,
            'monthly_revenue': monthly_revenue,
            'top_clients': top_clients,
            'ltv': ltv_metrics,
            'forecast': forecast,
            'country_metrics': country_metrics,
            'lead_funnel': lead_funnel,
        }
        metrics['alerts'] = self._build_alerts(metrics['inactive_clients'], metrics['forecast'])

        summary = self._calculate_summary_metrics(selected_frame, inactive_metrics, monthly_revenue)
        summary['total_revenue_overall'] = monthly_revenue.get('total_revenue_overall', monthly_revenue.get('total_revenue', summary['total_revenue']))
        summary['month'] = month_start.strftime('%Y-%m')

        return {
            'success': True,
            'summary': summary,
            'metrics': metrics,
            'data_source': 'Banco de dados',
            'selected_month': summary['month'],
            'total_records': len(selected_records),
            'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'currency': self._target_currency,
            'currency_symbol': self.CURRENCY_SYMBOLS.get(self._target_currency, 'R$'),
        }

    def clear_cache(self) -> None:
        self._cached_data = None
        self._last_cache_update = None
        self._cache_window = (None, None)
        print("🗑️ Cache de dados B2B limpo")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_sales_data(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None
    ) -> pd.DataFrame:
        window = (start_date.date(), end_date.date())
        if (
            self._cached_data is not None
            and self._last_cache_update
            and (datetime.now() - self._last_cache_update).seconds < self.cache_duration
            and self._cache_window == window
            and self._cache_user_id == user_id
        ):
            return self._cached_data

        frame = self.repository.fetch_sales_dataframe(
            start_date=window[0],
            end_date=window[1],
            user_id=user_id
        )
        self._cached_data = frame
        self._cache_window = window
        self._cache_user_id = user_id
        self._last_cache_update = datetime.now()
        return frame

    def _resolve_month_window(self, reference_month: Optional[str]) -> Tuple[datetime, datetime]:
        if reference_month:
            try:
                month_start = datetime.strptime(f"{reference_month}-01", "%Y-%m-%d")
            except ValueError:
                month_start = datetime.now().replace(day=1)
        else:
            month_start = datetime.now().replace(day=1)

        last_day = calendar.monthrange(month_start.year, month_start.month)[1]
        month_end = month_start.replace(day=last_day)
        return month_start, month_end

    def _build_monthly_revenue_view(self, revenue_data: Dict[str, Any], selected_month_start: datetime) -> Dict[str, Any]:
        monthly_data = revenue_data.get('monthly_data', [])
        volume_data = revenue_data.get('monthly_volume_data', [])

        month_key = selected_month_start.strftime('%Y-%m')
        prev_month_start = (selected_month_start - timedelta(days=1)).replace(day=1)
        prev_month_key = prev_month_start.strftime('%Y-%m')

        current_revenue = self._find_month_value(monthly_data, month_key, 'valor')
        previous_revenue = self._find_month_value(monthly_data, prev_month_key, 'valor')
        growth = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue else 0.0

        current_volume = self._find_month_value(volume_data, month_key, 'quantidade')
        previous_volume = self._find_month_value(volume_data, prev_month_key, 'quantidade')
        volume_growth = ((current_volume - previous_volume) / previous_volume * 100) if previous_volume else 0.0

        total_revenue_overall = float(sum(item.get('valor', 0) for item in monthly_data))
        total_volume = float(sum(item.get('quantidade', 0) for item in volume_data))

        return {
            'monthly_data': monthly_data,
            'monthly_volume_data': volume_data,
            'current_month': current_revenue,
            'previous_month': previous_revenue,
            'growth_percentage': float(growth),
            'total_revenue': total_revenue_overall,
            'total_revenue_overall': total_revenue_overall,
            'current_volume': current_volume,
            'previous_volume': previous_volume,
            'volume_growth_percentage': float(volume_growth),
            'total_volume': total_volume,
            'selected_month': month_key,
        }

    def _build_country_metrics(
        self,
        base_metrics: Dict[str, Any],
        selected_frame: pd.DataFrame,
    ) -> Dict[str, Any]:
        metrics = dict(base_metrics)
        if selected_frame.empty:
            metrics['countries_revenue_selected'] = []
            return metrics

        grouped = (
            selected_frame.groupby('pais')
            .agg({'valor': 'sum', 'quantidade': 'sum'})
            .reset_index()
        )
        total_value = float(grouped['valor'].sum())
        totals = {}
        countries_revenue = []
        for _, row in grouped.iterrows():
            country = row['pais'] or 'Indefinido'
            value = float(row['valor'])
            quantity = float(row['quantidade'])
            percentage = (value / total_value * 100) if total_value else 0.0
            totals[country] = {
                'receita_total': value,
                'percentual_receita': percentage,
                'receita_mes_atual': value,
                'volume_total': quantity,
                'volume_mes_atual': quantity,
            }
            countries_revenue.append({
                'pais': country,
                'valor': value,
                'percentual': percentage,
            })

        metrics['total_by_country'] = totals
        metrics['countries_revenue'] = countries_revenue
        metrics['countries_revenue_selected'] = countries_revenue
        return metrics

    def _build_lead_funnel(self, month_start: datetime, month_end: datetime) -> Dict[str, Any]:
        stage_options: List[Dict[str, Any]] = []
        if self.crm_service:
            try:
                stage_options = self.crm_service.stage_options()
            except Exception:
                stage_options = []

        stage_order = [stage['value'] for stage in stage_options] if stage_options else []
        stage_labels = {stage['value']: stage.get('label', stage['value']) for stage in stage_options}
        stage_badges = {stage['value']: stage.get('badge', 'secondary') for stage in stage_options}

        with session_scope() as session:
            status_counts = {
                (status or 'nao_contactado'): count
                for status, count in session.query(CRMLead.status, func.count(CRMLead.id)).group_by(CRMLead.status)
            }
            total_leads = sum(status_counts.values())

            month_end_next = month_end + timedelta(days=1)
            new_leads = session.query(func.count(CRMLead.id)).filter(
                CRMLead.created_at >= month_start,
                CRMLead.created_at < month_end_next,
            ).scalar() or 0
            converted_leads = session.query(func.count(CRMLead.id)).filter(
                CRMLead.status == 'cliente',
                CRMLead.updated_at >= month_start,
                CRMLead.updated_at < month_end_next,
            ).scalar() or 0

        if not stage_order:
            stage_order = sorted(status_counts.keys()) or ['nao_contactado', 'contactado', 'em_negociacao', 'cliente']
            for stage in stage_order:
                stage_labels.setdefault(stage, stage.replace('_', ' ').title())
                stage_badges.setdefault(stage, 'secondary')

        stages: List[Dict[str, Any]] = []
        for stage in stage_order:
            count = status_counts.pop(stage, 0)
            percentage = (count / total_leads * 100) if total_leads else 0.0
            stages.append({
                'status': stage,
                'label': stage_labels.get(stage, stage),
                'badge': stage_badges.get(stage, 'secondary'),
                'count': int(count),
                'percentage': percentage,
            })

        for stage, count in status_counts.items():
            safe_stage = stage or 'sem_status'
            percentage = (count / total_leads * 100) if total_leads else 0.0
            stages.append({
                'status': safe_stage,
                'label': stage_labels.get(stage, safe_stage.replace('_', ' ').title()),
                'badge': stage_badges.get(stage, 'secondary'),
                'count': int(count),
                'percentage': percentage,
            })

        return {
            'total_leads': int(total_leads),
            'stages': stages,
            'new_leads': int(new_leads),
            'converted_leads': int(converted_leads),
        }

    @staticmethod
    def _find_month_value(data: List[Dict[str, Any]], month_key: str, value_key: str) -> float:
        for item in data:
            candidate = item.get('mes_ano') or item.get('mes_ano_str')
            if candidate == month_key:
                try:
                    return float(item.get(value_key, 0))
                except (TypeError, ValueError):
                    return 0.0
        return 0.0

    def _calculate_summary_metrics(
        self,
        period_frame: pd.DataFrame,
        inactive_metrics: Dict[str, Any],
        monthly_revenue: Dict[str, Any],
    ) -> Dict[str, Any]:
        total_revenue = float(period_frame['valor'].sum())
        unique_orders = int(period_frame['order_id'].nunique())
        active_clients = int(period_frame['client_id'].nunique())
        avg_ticket = total_revenue / unique_orders if unique_orders else 0.0

        growth_rate = float(monthly_revenue.get('growth_percentage', 0))
        new_clients = inactive_metrics.get('new_clients_count', 0)
        churn_clients = inactive_metrics.get('high_risk_count', 0)
        inactive_count = inactive_metrics.get('total_inactive', 0)
        total_clients = inactive_metrics.get('total_clients')
        if total_clients is None:
            total_clients = active_clients + inactive_count

        return {
            'total_revenue': total_revenue,
            'total_revenue_formatted': self._format_currency(total_revenue),
            'avg_ticket': avg_ticket,
            'avg_ticket_formatted': self._format_currency(avg_ticket),
            'active_clients': active_clients,
            'inactive_clients': inactive_count,
            'total_clients': total_clients,
            'growth_rate': growth_rate,
            'ticket_trend': self._trend_label(growth_rate),
            'new_clients': new_clients,
            'churn_clients': churn_clients,
            'total_orders': unique_orders,
        }

    def _calculate_client_metrics(self, frame: pd.DataFrame) -> List[ClientMetric]:
        if frame.empty:
            return []

        metrics: List[ClientMetric] = []
        now = datetime.now().date()
        grouped = frame.groupby('client_id')

        for client_id, group in grouped:
            client_id_str = str(client_id).strip()
            if not client_id_str:
                continue

            name_series = group['cliente'].dropna()
            name = name_series.iloc[0] if not name_series.empty else f'Cliente #{client_id_str}'

            total_revenue = float(group['valor'].sum())
            total_orders = int(group['order_id'].nunique())
            avg_order_value = total_revenue / total_orders if total_orders else 0.0

            last_purchase = group['date'].max()
            first_purchase = group['date'].min()
            days_since_last_purchase = (now - last_purchase.date()).days if pd.notnull(last_purchase) else 0
            months_active = max(((last_purchase - first_purchase).days / 30) if last_purchase and first_purchase else 0, 1)
            purchase_frequency = total_orders / months_active if months_active else 0.0

            churn_risk = self._classify_churn_risk(days_since_last_purchase)
            ltv = total_revenue  # simplistic LTV approximation

            metrics.append(
                ClientMetric(
                    client_id=client_id_str,
                    name=name,
                    total_revenue=total_revenue,
                    total_orders=total_orders,
                    avg_order_value=avg_order_value,
                    purchase_frequency=round(purchase_frequency, 2),
                    days_since_last_purchase=days_since_last_purchase,
                    churn_risk=churn_risk,
                    ltv=ltv,
                )
            )

        metrics.sort(key=lambda item: item.total_revenue, reverse=True)
        return metrics

    @staticmethod
    def _build_trends(monthly_revenue: Dict[str, Any]) -> Dict[str, List[Any]]:
        monthly_data = monthly_revenue.get('monthly_data', [])
        months = [entry.get('mes_ano') for entry in monthly_data]
        revenue = [float(entry.get('valor', 0)) for entry in monthly_data]
        return {
            'months': months,
            'revenue': revenue,
            'clients': [],
            'orders': [],
        }

    @staticmethod
    def _build_alerts(inactive_metrics: Dict[str, Any], forecast: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        high_risk = inactive_metrics.get('high_risk_count', 0)
        if high_risk:
            alerts.append({
                'type': 'warning',
                'title': 'Clientes em alto risco',
                'message': f'{high_risk} clientes com risco elevado de churn.',
            })
        if forecast.get('trend') == 'declínio':
            alerts.append({
                'type': 'danger',
                'title': 'Previsão de queda nas vendas',
                'message': 'A tendência indica queda de receita nos próximos meses.',
            })
        return alerts

    def _format_currency(self, value: float) -> str:
        symbol = self.CURRENCY_SYMBOLS.get(self._target_currency, 'R$')
        if self._target_currency == 'PYG':
            # Guarani não usa centavos
            return f"{symbol} {value:,.0f}".replace(',', '.')
        return f"{symbol} {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    @staticmethod
    def _trend_label(value: float) -> str:
        if value > 1:
            return 'Crescimento'
        if value < -1:
            return 'Queda'
        return 'Estável'

    @staticmethod
    def _classify_churn_risk(days_since_last_purchase: int) -> str:
        if days_since_last_purchase >= 60:
            return 'alto'
        if days_since_last_purchase >= 45:
            return 'médio'
        return 'baixo'

    def _get_empty_summary(self) -> Dict[str, Any]:
        symbol = self.CURRENCY_SYMBOLS.get(self._target_currency, 'R$')
        zero_formatted = f"{symbol} 0,00" if self._target_currency != 'PYG' else f"{symbol} 0"
        return {
            'summary': {
                'total_revenue': 0,
                'total_revenue_formatted': zero_formatted,
                'active_clients': 0,
                'inactive_clients': 0,
                'avg_ticket': 0,
                'avg_ticket_formatted': zero_formatted,
                'growth_rate': 0.0,
                'new_clients': 0,
                'churn_clients': 0,
            },
            'inactive_clients': [],
            'top_clients': [],
            'trends': {'months': [], 'revenue': [], 'clients': [], 'orders': []},
            'alerts': [],
            'period': {'start': '', 'end': '', 'days': 0},
            'data_source': 'no_data',
            'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'ltv': {'average_ltv': 0, 'median_ltv': 0, 'ltv_distribution': []},
            'forecast': {'forecast': [], 'trend': 'dados insuficientes'},
            'total_clients': 0,
            'ticket_trend': 'Estável',
            'total_orders': 0,
            'total_revenue_overall': 0,
            'month': '',
            'currency': self._target_currency,
            'currency_symbol': symbol,
        }

    def _get_empty_dashboard_data(self) -> Dict[str, Any]:
        return {
            'success': True,
            'summary': self._get_empty_summary(),
            'metrics': self._get_empty_metrics(),
            'data_source': 'No Data',
            'selected_month': None,
            'total_records': 0,
            'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'currency': self._target_currency,
            'currency_symbol': self.CURRENCY_SYMBOLS.get(self._target_currency, 'R$'),
        }

    def _get_empty_metrics(self) -> Dict[str, Any]:
        return {
            'inactive_clients': {
                'inactive_clients': [],
                'total_inactive': 0,
                'total_clients': 0,
                'inactive_percentage': 0,
                'threshold_days': 30,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
            },
            'monthly_revenue': {
                'monthly_data': [],
                'current_month': 0,
                'previous_month': 0,
                'growth_percentage': 0,
                'total_revenue': 0,
            },
            'top_clients': [],
            'ltv': {
                'average_ltv': 0,
                'median_ltv': 0,
                'ltv_distribution': [],
            },
            'forecast': {
                'forecast': [],
                'trend': 'dados insuficientes',
            },
            'country_metrics': {
                'countries_revenue': [],
                'countries_volume': [],
                'monthly_by_country': [],
                'total_by_country': {},
            },
            'lead_funnel': {
                'total_leads': 0,
                'stages': [],
                'new_leads': 0,
                'converted_leads': 0,
            },
            'alerts': [],
        }


__all__ = ['SalesAnalyzer']
