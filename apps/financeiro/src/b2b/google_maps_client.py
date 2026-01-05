"""Simple Google Places client for CRM lead discovery."""

from __future__ import annotations

import os
from typing import Dict, Any, List, Optional
import requests


class GoogleMapsClient:
    def __init__(self, api_key: Optional[str] = None):
        env_key = os.getenv('GOOGLE_MAPS_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.api_key = api_key or env_key
        if not self.api_key:
            raise RuntimeError('GOOGLE_MAPS_API_KEY / GOOGLE_API_KEY não configurada no ambiente')

    BASE_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
    DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'

    def text_search(self, query: str, region: Optional[str] = None) -> Dict[str, Any]:
        params = {
            'key': self.api_key,
            'query': query,
            'language': 'pt-BR'
        }
        if region:
            params['region'] = region

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        Busca detalhes completos de um lugar via Place Details API.
        Retorna informações adicionais como telefone internacional, website, e links sociais.
        """
        params = {
            'key': self.api_key,
            'place_id': place_id,
            'language': 'pt-BR',
            'fields': 'name,formatted_address,formatted_phone_number,international_phone_number,website,url,types,address_components,geometry'
        }

        response = requests.get(self.DETAILS_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def build_address(self, result: Dict[str, Any]) -> Dict[str, Any]:
        address_components = {comp['types'][0]: comp for comp in result.get('address_components', [])}

        def get_component(key: str, field: str = 'long_name'):
            component = address_components.get(key)
            return component.get(field) if component else None

        return {
            'address_line': result.get('formatted_address'),
            'address_number': get_component('street_number'),
            'neighborhood': get_component('sublocality'),
            'city': get_component('locality') or get_component('administrative_area_level_2'),
            'state': get_component('administrative_area_level_1', 'short_name'),
            'postal_code': get_component('postal_code'),
            'country': get_component('country'),
        }

    def extract_social_links(self, website: Optional[str]) -> Dict[str, Optional[str]]:
        """
        Extrai links de redes sociais do website.
        Nota: A API do Google Maps não retorna diretamente Instagram/WhatsApp.
        Esses dados precisam ser extraídos do website ou adicionados manualmente.
        """
        social = {
            'instagram': None,
            'whatsapp': None
        }

        # Se houver website, podemos tentar buscar na página (futuro)
        # Por enquanto, retornamos None para serem preenchidos manualmente
        return social

    def parse_results(self, query: str, results: List[Dict[str, Any]], search_city: str, fetch_details: bool = False) -> List[Dict[str, Any]]:
        """
        Processa resultados da busca do Google Maps.

        Args:
            query: Termo de busca usado
            results: Lista de resultados da API
            search_city: Cidade buscada
            fetch_details: Se True, busca detalhes adicionais de cada lugar (mais lento, mas mais completo)
        """
        leads = []
        for item in results:
            location = item.get('geometry', {}).get('location', {})
            address_info = self.build_address(item)
            place_id = item.get('place_id')

            # Dados básicos do Text Search
            phone = item.get('formatted_phone_number')
            website = item.get('website')

            # Se solicitado, buscar detalhes adicionais
            if fetch_details and place_id:
                try:
                    details_response = self.get_place_details(place_id)
                    if details_response.get('status') == 'OK':
                        details = details_response.get('result', {})
                        phone = details.get('formatted_phone_number') or details.get('international_phone_number') or phone
                        website = details.get('website') or website
                except Exception as e:
                    print(f"⚠️ Erro ao buscar detalhes do place_id {place_id}: {e}")

            lead = {
                'name': item.get('name'),
                'category': ', '.join(item.get('types', [])[:3]) if item.get('types') else None,
                'address': address_info.get('address_line'),
                'address_line': address_info.get('address_line'),
                'address_number': address_info.get('address_number'),
                'neighborhood': address_info.get('neighborhood'),
                'city': address_info.get('city'),
                'state': address_info.get('state'),
                'postal_code': address_info.get('postal_code'),
                'country': address_info.get('country'),
                'latitude': location.get('lat'),
                'longitude': location.get('lng'),
                'place_id': place_id,
                'source': 'Google Maps',
                'search_keyword': query,
                'search_city': search_city,
                'phone': phone,
                'website': website,
                'instagram': None,  # Precisa ser preenchido manualmente ou via scraping
                'whatsapp': None,   # Precisa ser preenchido manualmente ou derivado do telefone
            }
            leads.append(lead)
        return leads
