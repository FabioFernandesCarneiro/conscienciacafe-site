"""CRM Service - orchestration layer for B2B lead management."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import func, or_

from src.db import session_scope
from src.models import CRMLead, CRMInteraction


LEAD_STAGE_DEFINITIONS: List[Dict[str, str]] = [
    {'value': 'nao_contactado', 'label': 'Não contactado', 'badge': 'secondary'},
    {'value': 'contactado', 'label': 'Contactado', 'badge': 'info'},
    {'value': 'pedido_amostra', 'label': 'Pedido de amostra', 'badge': 'warning'},
    {'value': 'envio_amostra', 'label': 'Envio de amostra', 'badge': 'warning'},
    {'value': 'em_negociacao', 'label': 'Em negociação', 'badge': 'primary'},
    {'value': 'cliente', 'label': 'Cliente (fez pedido)', 'badge': 'success'},
    {'value': 'perdido', 'label': 'Perdido (sem interesse)', 'badge': 'dark'},
]

DEFAULT_PIPELINE_STAGES = [stage['value'] for stage in LEAD_STAGE_DEFINITIONS]
STAGE_LABELS = {stage['value']: stage['label'] for stage in LEAD_STAGE_DEFINITIONS}
STAGE_BADGES = {stage['value']: stage['badge'] for stage in LEAD_STAGE_DEFINITIONS}
LEGACY_STAGE_MAP = {
    'new': 'nao_contactado',
    'contacted': 'contactado',
    'qualified': 'em_negociacao',
    'proposal': 'em_negociacao',
    'won': 'cliente',
    'lost': 'perdido',
}


class CRMService:
    """High-level helper to manage CRM leads and interactions."""

    def __init__(self, *, use_sqlalchemy: Optional[bool] = None):
        # Sempre usar SQLAlchemy (PostgreSQL) - SQLite legado removido
        self.use_sqlalchemy = True
        self.db = None

    # ----------------------
    # Stage helpers
    # ----------------------

    def _record_interaction(
        self,
        lead_id: int,
        *,
        interaction_type: str,
        subject: Optional[str] = None,
        notes: Optional[str] = None,
        owner: Optional[str] = None,
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        follow_up_at: Optional[datetime] = None,
    ) -> int:
        payload: Dict[str, Any] = {
            'interaction_type': interaction_type,
            'subject': subject,
            'notes': notes,
            'owner': owner,
            'channel': channel,
            'metadata': metadata,
        }

        if follow_up_at:
            payload['follow_up_at'] = (
                follow_up_at.isoformat() if isinstance(follow_up_at, datetime) else follow_up_at
            )

        if not self.use_sqlalchemy:
            return self.db.add_crm_interaction(lead_id, payload)
        return self._record_interaction_sqlalchemy(lead_id, payload)

    def _parse_metadata(self, raw_metadata: Any) -> Dict[str, Any]:
        if not raw_metadata:
            return {}
        if isinstance(raw_metadata, dict):
            return raw_metadata
        if isinstance(raw_metadata, str):
            try:
                return json.loads(raw_metadata)
            except json.JSONDecodeError:
                return {'raw': raw_metadata}
        return {}

    def _normalize_timestamp(self, timestamp: Any) -> Optional[str]:
        if not timestamp:
            return None
        if isinstance(timestamp, str):
            return timestamp.replace(' ', 'T')
        if isinstance(timestamp, datetime):
            return timestamp.isoformat()
        return str(timestamp)

    def validate_stage(self, stage: Optional[str]) -> str:
        """Return a safe stage slug, defaulting to the first stage when None."""
        if not stage:
            return DEFAULT_PIPELINE_STAGES[0]
        normalized = LEGACY_STAGE_MAP.get(stage, stage)
        if normalized not in STAGE_LABELS:
            raise ValueError(f"Status inválido: {stage}")
        return normalized

    def stage_options(self) -> List[Dict[str, str]]:
        """Expose stage definitions for UI consumption."""
        return LEAD_STAGE_DEFINITIONS

    def stage_label(self, stage: Optional[str]) -> str:
        if not stage:
            return STAGE_LABELS.get(DEFAULT_PIPELINE_STAGES[0], DEFAULT_PIPELINE_STAGES[0])
        normalized = LEGACY_STAGE_MAP.get(stage, stage)
        return STAGE_LABELS.get(normalized, normalized)

    def create_lead(
        self,
        name: str,
        category: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        source: Optional[str] = None,
        owner: Optional[str] = None,
        **contact_info: Any,
    ) -> int:
        if not self.use_sqlalchemy:
            return self._create_lead_sqlite(
                name,
                category,
                city,
                state,
                source,
                owner,
                **contact_info,
            )
        return self._create_lead_sqlalchemy(
            name,
            category=category,
            city=city,
            state=state,
            source=source,
            owner=owner,
            **contact_info,
        )

    def _create_lead_sqlite(
        self,
        name: str,
        category: Optional[str],
        city: Optional[str],
        state: Optional[str],
        source: Optional[str],
        owner: Optional[str],
        **contact_info: Any,
    ) -> int:
        lead_payload: Dict[str, Any] = {
            'name': name,
            'category': category,
            'city': city,
            'state': state,
            'source': source,
            'owner': owner,
        }
        lead_payload.update(contact_info)
        lead_payload['status'] = self.validate_stage(lead_payload.get('status'))
        if lead_payload['status'] == 'cliente':
            lead_payload.setdefault('is_customer', True)
        elif lead_payload['status'] == 'perdido':
            lead_payload.setdefault('is_customer', False)
        lead_id = self.db.create_crm_lead(lead_payload)
        self._record_interaction(
            lead_id,
            interaction_type='create',
            subject='Lead criado',
            metadata={
                'status': {
                    'value': lead_payload['status'],
                    'label': self.stage_label(lead_payload['status'])
                }
            }
        )
        return lead_id

    def _create_lead_sqlalchemy(self, name: str, **payload: Any) -> int:
        normalized_status = self.validate_stage(payload.get('status'))
        if normalized_status == 'cliente':
            payload.setdefault('is_customer', True)
        elif normalized_status == 'perdido':
            payload.setdefault('is_customer', False)

        with session_scope() as session:
            lead = CRMLead(
                name=name,
                category=payload.get('category'),
                status=normalized_status,
                source=payload.get('source'),
                search_keyword=payload.get('search_keyword'),
                search_city=payload.get('search_city'),
                address_line=payload.get('address_line'),
                address_number=payload.get('address_number'),
                address_complement=payload.get('address_complement'),
                neighborhood=payload.get('neighborhood'),
                city=payload.get('city'),
                state=payload.get('state'),
                postal_code=payload.get('postal_code'),
                country=payload.get('country'),
                latitude=payload.get('latitude'),
                longitude=payload.get('longitude'),
                phone=payload.get('phone'),
                whatsapp=payload.get('whatsapp'),
                email=payload.get('email'),
                instagram=payload.get('instagram'),
                website=payload.get('website'),
                primary_contact_name=payload.get('primary_contact_name'),
                owner=payload.get('owner'),
                user_id=payload.get('user_id'),
                notes=payload.get('notes'),
                google_place_id=payload.get('google_place_id'),
                is_customer=payload.get('is_customer'),
                converted_account_id=payload.get('converted_account_id'),
            )
            session.add(lead)
            session.flush()
            lead_id = lead.id

        self._record_interaction(
            lead_id,
            interaction_type='create',
            subject='Lead criado',
            metadata={
                'status': {
                    'value': normalized_status,
                    'label': self.stage_label(normalized_status)
                }
            }
        )
        return lead_id

    def get_lead(self, lead_id: int) -> Optional[Dict[str, Any]]:
        if not self.use_sqlalchemy:
            return self.db.get_crm_lead(lead_id)
        return self._get_lead_sqlalchemy(lead_id)

    def list_leads(
        self,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        user_id: Optional[int] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        is_customer: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        if not self.use_sqlalchemy:
            leads = self._list_leads_sqlite(
                status=status,
                owner=owner,
                user_id=user_id,
                city=city,
                country=country,
                is_customer=is_customer,
                search=search,
                limit=limit,
                offset=offset,
            )
        else:
            leads = self._list_leads_sqlalchemy(
                status=status,
                owner=owner,
                user_id=user_id,
                city=city,
                country=country,
                is_customer=is_customer,
                search=search,
                limit=limit,
                offset=offset,
            )

        for lead in leads:
            stage = lead.get('status')
            normalized_stage = LEGACY_STAGE_MAP.get(stage, stage)
            lead['status'] = normalized_stage
            lead['status_label'] = self.stage_label(normalized_stage)
            lead['status_badge'] = STAGE_BADGES.get(normalized_stage, 'secondary')
        return leads

    def update_lead(self, lead_id: int, **updates: Any) -> None:
        if not updates:
            return

        if not self.use_sqlalchemy:
            result = self._update_lead_sqlite(lead_id, **updates)
        else:
            result = self._update_lead_sqlalchemy(lead_id, **updates)

        if not result:
            return

        normalized_current_status, normalized_new_status, change_events = result

        if normalized_new_status and normalized_new_status != normalized_current_status:
            self._record_interaction(
                lead_id,
                interaction_type='status_change',
                subject='Status atualizado',
                metadata={
                    'from': {
                        'value': normalized_current_status,
                        'label': self.stage_label(normalized_current_status)
                    } if normalized_current_status else None,
                    'to': {
                        'value': normalized_new_status,
                        'label': self.stage_label(normalized_new_status)
                    }
                }
            )

        if change_events:
            self._record_interaction(
                lead_id,
                interaction_type='update',
                subject='Dados do lead atualizados',
                metadata={'changes': change_events}
            )

    def advance_stage(self, lead_id: int, new_stage: str) -> None:
        self.update_lead(lead_id, status=new_stage)

    def register_interaction(
        self,
        lead_id: int,
        interaction_type: str,
        channel: Optional[str] = None,
        subject: Optional[str] = None,
        notes: Optional[str] = None,
        follow_up_at: Optional[datetime] = None,
        owner: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        return self._record_interaction(
            lead_id,
            interaction_type=interaction_type,
            subject=subject,
            notes=notes,
            owner=owner,
            channel=channel,
            metadata=metadata,
            follow_up_at=follow_up_at,
        )

    def get_interactions(self, lead_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.use_sqlalchemy:
            return self.db.list_crm_interactions(lead_id, limit=limit)
        return self._list_crm_interactions_sqlalchemy(lead_id, limit=limit)

    def delete_lead(self, lead_id: int) -> None:
        if not self.use_sqlalchemy:
            self.db.delete_crm_lead(lead_id)
        else:
            self._delete_lead_sqlalchemy(lead_id)

    def delete_all_leads(self) -> int:
        """Delete all leads and their interactions. Returns count of deleted leads."""
        if not self.use_sqlalchemy:
            # SQLite implementation would go here if needed
            raise NotImplementedError("delete_all_leads not implemented for SQLite")

        with session_scope() as session:
            count = session.query(CRMLead).count()
            session.query(CRMLead).delete()
            return count

    # ----------------------
    # Timeline helpers
    # ----------------------

    def list_interactions(self, lead_id: int, limit: int = 200) -> List[Dict[str, Any]]:
        if not self.use_sqlalchemy:
            interactions = self.db.list_crm_interactions(lead_id, limit=limit)
        else:
            interactions = self._list_crm_interactions_sqlalchemy(lead_id, limit=limit)
        timeline: List[Dict[str, Any]] = []
        for interaction in interactions:
            metadata = self._parse_metadata(interaction.get('metadata'))
            timeline.append({
                'id': interaction.get('id'),
                'interaction_type': interaction.get('interaction_type'),
                'subject': interaction.get('subject'),
                'notes': interaction.get('notes'),
                'owner': interaction.get('owner'),
                'channel': interaction.get('channel'),
                'interaction_at': self._normalize_timestamp(interaction.get('interaction_at')),
                'follow_up_at': self._normalize_timestamp(interaction.get('follow_up_at')),
                'metadata': metadata,
            })
        return timeline

    def add_comment(self, lead_id: int, notes: str, owner: Optional[str] = None) -> int:
        if not notes or not notes.strip():
            raise ValueError('Comentário não pode ser vazio')
        return self._record_interaction(
            lead_id,
            interaction_type='comment',
            subject='Comentário',
            notes=notes.strip(),
            owner=owner.strip() if owner else None,
        )

    # ----------------------
    # Helpers - backend selection
    # ----------------------

    def _record_interaction_sqlalchemy(self, lead_id: int, payload: Dict[str, Any]) -> int:
        metadata = payload.get('metadata')
        follow_up = payload.get('follow_up_at')

        with session_scope() as session:
            interaction = CRMInteraction(
                lead_id=lead_id,
                interaction_type=payload.get('interaction_type'),
                channel=payload.get('channel'),
                subject=payload.get('subject'),
                notes=payload.get('notes'),
                owner=payload.get('owner'),
            )

            if follow_up:
                if isinstance(follow_up, datetime):
                    interaction.follow_up_at = follow_up
                else:
                    try:
                        interaction.follow_up_at = datetime.fromisoformat(str(follow_up))
                    except ValueError:
                        interaction.follow_up_at = None

            interaction.metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None

            session.add(interaction)
            session.flush()
            return interaction.id

    def _get_lead_sqlalchemy(self, lead_id: int) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            lead = session.get(CRMLead, lead_id)
            if not lead:
                return None
            return self._serialize_lead(lead)

    def _list_leads_sqlite(self, **filters: Any) -> List[Dict[str, Any]]:
        leads = self.db.list_crm_leads(
            status=filters.get('status'),
            owner=filters.get('owner'),
            city=filters.get('city'),
            is_customer=filters.get('is_customer'),
            search=filters.get('search'),
            limit=filters.get('limit', 200),
            offset=filters.get('offset', 0),
        )
        country = filters.get('country')
        if country:
            leads = [lead for lead in leads if lead.get('country') == country]
        return leads

    def _list_leads_sqlalchemy(self, **filters: Any) -> List[Dict[str, Any]]:
        status = filters.get('status')
        owner = filters.get('owner')
        user_id = filters.get('user_id')
        city = filters.get('city')
        country = filters.get('country')
        is_customer = filters.get('is_customer')
        search = filters.get('search')
        limit = int(filters.get('limit', 200))
        offset = int(filters.get('offset', 0))

        with session_scope() as session:
            query = session.query(CRMLead)

            if status:
                query = query.filter(CRMLead.status == self.validate_stage(status))
            if owner:
                query = query.filter(CRMLead.owner == owner)
            if user_id:
                query = query.filter(CRMLead.user_id == user_id)
            if city:
                query = query.filter(CRMLead.city == city)
            if country:
                query = query.filter(CRMLead.country == country)
            if is_customer is not None:
                query = query.filter(CRMLead.is_customer.is_(bool(is_customer)))
            if search:
                pattern = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(CRMLead.name).like(pattern),
                        func.lower(CRMLead.city).like(pattern),
                        func.lower(CRMLead.state).like(pattern)
                    )
                )

            leads = (
                query
                .order_by(CRMLead.updated_at.desc(), CRMLead.id.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [self._serialize_lead(lead) for lead in leads]

    def _update_lead_sqlite(self, lead_id: int, **updates: Any):
        current_lead = self.db.get_crm_lead(lead_id)
        if not current_lead:
            raise ValueError('Lead não encontrado')

        normalized_current_status = (
            self.validate_stage(current_lead.get('status')) if current_lead.get('status') else None
        )

        updates = {key: value for key, value in updates.items() if value is not None}

        status_changed = False
        if 'status' in updates:
            new_status = self.validate_stage(updates['status'])
            if normalized_current_status == new_status:
                updates.pop('status')
            else:
                updates['status'] = new_status
                status_changed = True
                if new_status == 'cliente':
                    updates.setdefault('is_customer', True)
                elif new_status == 'perdido':
                    updates.setdefault('is_customer', False)

        if not updates:
            return None

        self.db.update_crm_lead(lead_id, updates)

        updated_lead = self.db.get_crm_lead(lead_id)
        if not updated_lead:
            return None

        normalized_new_status = (
            self.validate_stage(updated_lead.get('status')) if updated_lead.get('status') else None
        )

        change_events: List[Dict[str, Any]] = []
        tracked_fields = [field for field in updates.keys() if field not in {'status', 'is_customer'}]
        for field in tracked_fields:
            old_value = current_lead.get(field)
            new_value = updated_lead.get(field)
            if old_value != new_value:
                change_events.append({
                    'field': field,
                    'old': old_value,
                    'new': new_value,
                })

        return normalized_current_status, normalized_new_status, change_events

    def _update_lead_sqlalchemy(self, lead_id: int, **updates: Any):
        updates = {key: value for key, value in updates.items() if value is not None}
        if not updates:
            return None

        with session_scope() as session:
            lead = session.get(CRMLead, lead_id)
            if not lead:
                raise ValueError('Lead não encontrado')

            current_data = self._serialize_lead(lead)
            normalized_current_status = (
                self.validate_stage(lead.status) if lead.status else None
            )

            status_changed = False
            if 'status' in updates:
                new_status = self.validate_stage(updates['status'])
                if normalized_current_status == new_status:
                    updates.pop('status')
                else:
                    updates['status'] = new_status
                    status_changed = True
                    if new_status == 'cliente':
                        updates.setdefault('is_customer', True)
                    elif new_status == 'perdido':
                        updates.setdefault('is_customer', False)

            if not updates:
                return None

            allowed_fields = [
                'name', 'category', 'status', 'source', 'search_keyword', 'search_city',
                'address_line', 'address_number', 'address_complement', 'neighborhood',
                'city', 'state', 'postal_code', 'country', 'latitude', 'longitude',
                'phone', 'whatsapp', 'email', 'instagram', 'website', 'primary_contact_name',
                'owner', 'user_id', 'notes', 'google_place_id', 'is_customer', 'converted_account_id'
            ]

            for field, value in updates.items():
                if field not in allowed_fields:
                    continue
                if field == 'is_customer':
                    setattr(lead, field, bool(value))
                else:
                    setattr(lead, field, value)

            if status_changed:
                lead.last_stage_change = datetime.utcnow()
            lead.updated_at = datetime.utcnow()

            session.flush()
            updated_data = self._serialize_lead(lead)

        normalized_new_status = (
            self.validate_stage(updated_data.get('status')) if updated_data.get('status') else None
        )

        change_events: List[Dict[str, Any]] = []
        tracked_fields = [field for field in updates.keys() if field not in {'status', 'is_customer'}]
        for field in tracked_fields:
            if current_data.get(field) != updated_data.get(field):
                change_events.append({
                    'field': field,
                    'old': current_data.get(field),
                    'new': updated_data.get(field),
                })

        return normalized_current_status, normalized_new_status, change_events

    def _list_crm_interactions_sqlalchemy(self, lead_id: int, limit: int) -> List[Dict[str, Any]]:
        with session_scope() as session:
            interactions = (
                session.query(CRMInteraction)
                .filter(CRMInteraction.lead_id == lead_id)
                .order_by(CRMInteraction.interaction_at.desc(), CRMInteraction.id.desc())
                .limit(limit)
                .all()
            )
            return [self._serialize_interaction(interaction) for interaction in interactions]

    def _delete_lead_sqlalchemy(self, lead_id: int) -> None:
        with session_scope() as session:
            lead = session.get(CRMLead, lead_id)
            if lead:
                session.delete(lead)

    # ----------------------
    # Serialization helpers
    # ----------------------

    def _serialize_lead(self, lead: CRMLead) -> Dict[str, Any]:
        return {
            'id': lead.id,
            'name': lead.name,
            'category': lead.category,
            'status': lead.status,
            'source': lead.source,
            'search_keyword': lead.search_keyword,
            'search_city': lead.search_city,
            'address_line': lead.address_line,
            'address_number': lead.address_number,
            'address_complement': lead.address_complement,
            'neighborhood': lead.neighborhood,
            'city': lead.city,
            'state': lead.state,
            'postal_code': lead.postal_code,
            'country': lead.country,
            'latitude': lead.latitude,
            'longitude': lead.longitude,
            'phone': lead.phone,
            'whatsapp': lead.whatsapp,
            'email': lead.email,
            'instagram': lead.instagram,
            'website': lead.website,
            'primary_contact_name': lead.primary_contact_name,
            'owner': lead.owner,
            'user_id': lead.user_id,
            'user_name': lead.user.username if lead.user else None,
            'notes': lead.notes,
            'google_place_id': lead.google_place_id,
            'is_customer': bool(lead.is_customer),
            'converted_account_id': lead.converted_account_id,
            'last_stage_change': lead.last_stage_change.isoformat() if lead.last_stage_change else None,
            'created_at': lead.created_at.isoformat() if lead.created_at else None,
            'updated_at': lead.updated_at.isoformat() if lead.updated_at else None,
        }

    def _serialize_interaction(self, interaction: CRMInteraction) -> Dict[str, Any]:
        return {
            'id': interaction.id,
            'lead_id': interaction.lead_id,
            'interaction_type': interaction.interaction_type,
            'channel': interaction.channel,
            'subject': interaction.subject,
            'notes': interaction.notes,
            'owner': interaction.owner,
            'interaction_at': interaction.interaction_at.isoformat() if interaction.interaction_at else None,
            'follow_up_at': interaction.follow_up_at.isoformat() if interaction.follow_up_at else None,
            'metadata': interaction.metadata_json,
            'created_at': interaction.created_at.isoformat() if hasattr(interaction, 'created_at') and interaction.created_at else None,
        }


def json_dumps(payload: Dict[str, Any]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False)
