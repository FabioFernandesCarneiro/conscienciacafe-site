"""
Lead Enrichment Service - Busca dados adicionais de leads (Instagram, WhatsApp, etc)
"""

import re
import requests
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time


class LeadEnrichmentService:
    """
    Serviço para enriquecer leads com dados adicionais que não vêm da API do Google Maps.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def enrich_lead(self, lead_data: Dict, google_maps_client=None, skip_api_calls: bool = False) -> Dict:
        """
        Enriquece um lead com dados adicionais.

        Args:
            lead_data: Dados básicos do lead (name, place_id, website, etc)
            google_maps_client: Cliente do Google Maps para buscar detalhes
            skip_api_calls: Se True, pula chamadas à API do Google (usa apenas scraping)

        Returns:
            Dict com dados enriquecidos
        """
        enriched = lead_data.copy()

        # Verificar se já tem dados da API (evita chamadas duplicadas)
        already_has_api_data = lead_data.get('_details_fetched', False)

        # 1. Buscar detalhes via API APENAS se:
        #    - Não foi marcado como já buscado
        #    - Não foi solicitado para pular chamadas API
        #    - Ainda falta phone ou website
        if (google_maps_client and lead_data.get('place_id') and
                not already_has_api_data and not skip_api_calls and
                (not enriched.get('phone') or not enriched.get('website'))):
            print(f"   📡 Buscando detalhes via API: {lead_data.get('name')}")
            details = self._get_place_details(lead_data['place_id'], google_maps_client)
            if details:
                for key, value in details.items():
                    if not enriched.get(key) and value:
                        enriched[key] = value
                enriched['_details_fetched'] = True

        # 2. Scraping do Google Business Profile (grátis, mas pode ser lento)
        #    Só faz se ainda não tiver instagram/whatsapp
        if (lead_data.get('place_id') and
                (not enriched.get('instagram') or not enriched.get('whatsapp'))):
            print(f"   🔍 Scraping Google Business Profile: {lead_data.get('name')}")
            gmb_data = self._scrape_google_business_profile(lead_data['place_id'])
            if gmb_data:
                for key, value in gmb_data.items():
                    if not enriched.get(key) and value:
                        enriched[key] = value

        # 3. Extrair dados do website (se tiver e ainda faltar Instagram/WhatsApp)
        if (enriched.get('website') and
                (not enriched.get('instagram') or not enriched.get('whatsapp'))):
            print(f"   🌐 Scraping website: {enriched.get('website')}")
            website_data = self._scrape_website_contacts(enriched['website'])
            for key, value in website_data.items():
                if not enriched.get(key) and value:
                    enriched[key] = value

        # 4. Derivar WhatsApp do telefone (se tiver telefone e ainda não tiver WhatsApp)
        if enriched.get('phone') and not enriched.get('whatsapp'):
            enriched['whatsapp'] = self._extract_whatsapp_from_phone(enriched['phone'])

        # 5. Sugerir Instagram baseado no nome (último recurso, apenas sugestão)
        if lead_data.get('name') and not enriched.get('instagram'):
            instagram_handle = self._guess_instagram_handle(
                lead_data['name'],
                lead_data.get('city')
            )
            if instagram_handle:
                enriched['instagram_suggestion'] = instagram_handle  # Sugestão, não confirmado

        return enriched

    def _scrape_google_business_profile(self, place_id: str) -> Dict:
        """
        Faz scraping da página do Google Business Profile (Google Meu Negócio).
        Esta é a fonte mais confiável pois os próprios negócios cadastram os dados.

        Args:
            place_id: ID do lugar no Google Maps

        Returns:
            Dict com instagram, whatsapp, phone, website extraídos
        """
        try:
            # URL da página do Google Maps com o place_id
            url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            html_content = response.text

            data = {
                'instagram': None,
                'whatsapp': None,
                'phone': None,
                'website': None
            }

            # Buscar Instagram
            # Estratégia: procurar em ordem de prioridade

            # 1. Buscar no JSON estruturado do Google (mais confiável)
            # Padrão: "sameAs":["https://instagram.com/username"]
            instagram_patterns = [
                r'"sameAs":\s*\[?"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)"',
                r'"instagram":\s*"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)"',
                r'href="https?://(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)["/]',
            ]

            for pattern in instagram_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    handle = match.group(1)
                    # Filtrar handles inválidos ou genéricos
                    if len(handle) > 2 and handle not in ['instagram', 'explore', 'p', 'reel']:
                        data['instagram'] = handle
                        print(f"      ✅ Instagram encontrado: @{data['instagram']}")
                        break

            # Buscar WhatsApp
            # Padrões do Google Business: links wa.me ou números formatados
            whatsapp_patterns = [
                r'wa\.me/(\+?[\d]+)',
                r'api\.whatsapp\.com/send\?phone=(\+?[\d]+)',
                r'"whatsapp["\s:]+.*?(\+?55\d{10,11})',
            ]

            for pattern in whatsapp_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    whatsapp_number = match.group(1)
                    # Limpar e formatar
                    whatsapp_number = re.sub(r'\D', '', whatsapp_number)
                    if not whatsapp_number.startswith('55') and len(whatsapp_number) >= 10:
                        whatsapp_number = f"55{whatsapp_number}"
                    data['whatsapp'] = whatsapp_number
                    print(f"      ✅ WhatsApp encontrado: {data['whatsapp']}")
                    break

            # Buscar telefone
            # Padrão brasileiro no formato do Google
            phone_patterns = [
                r'\+55\s*\d{2}\s*\d{4,5}[-\s]?\d{4}',
                r'\(\d{2}\)\s*\d{4,5}[-\s]?\d{4}',
            ]

            for pattern in phone_patterns:
                match = re.search(pattern, html_content)
                if match:
                    data['phone'] = match.group(0)
                    print(f"      ✅ Telefone encontrado: {data['phone']}")
                    break

            # Buscar website
            # O Google Maps coloca o website em tags específicas
            website_match = re.search(r'"([^"]*(?:http|https)://[^"]+)"', html_content)
            if website_match:
                potential_website = website_match.group(1)
                # Filtrar URLs do próprio Google
                if 'google.com' not in potential_website and 'gstatic.com' not in potential_website:
                    data['website'] = potential_website
                    print(f"      ✅ Website encontrado: {data['website']}")

            return data

        except Exception as e:
            print(f"      ⚠️ Erro ao buscar no Google Business Profile: {e}")
            return {'instagram': None, 'whatsapp': None, 'phone': None, 'website': None}

    def _get_place_details(self, place_id: str, google_maps_client) -> Dict:
        """Busca detalhes via Google Maps Place Details API"""
        try:
            response = google_maps_client.get_place_details(place_id)
            if response.get('status') == 'OK':
                result = response.get('result', {})
                return {
                    'phone': result.get('formatted_phone_number') or result.get('international_phone_number'),
                    'website': result.get('website'),
                }
        except Exception as e:
            print(f"⚠️ Erro ao buscar detalhes do place_id {place_id}: {e}")
        return {}

    def _scrape_website_contacts(self, website_url: str) -> Dict:
        """
        Faz scraping do website para buscar Instagram, WhatsApp, telefone.
        """
        try:
            # Timeout de 10 segundos
            response = self.session.get(website_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            html_text = response.text.lower()

            data = {
                'instagram': None,
                'whatsapp': None,
                'phone': None
            }

            # Buscar Instagram
            # Padrões: instagram.com/username, @username em links/texto
            instagram_patterns = [
                r'instagram\.com/([a-zA-Z0-9._]+)',
                r'@([a-zA-Z0-9._]+)',
            ]

            for pattern in instagram_patterns:
                match = re.search(pattern, html_text)
                if match:
                    potential_handle = match.group(1)
                    # Filtrar handles muito genéricos
                    if len(potential_handle) > 3 and not potential_handle.startswith('http'):
                        data['instagram'] = potential_handle
                        break

            # Buscar WhatsApp
            # Padrões: wa.me/número, api.whatsapp.com/send?phone=número
            whatsapp_patterns = [
                r'wa\.me/(\+?[\d]+)',
                r'api\.whatsapp\.com/send\?phone=(\+?[\d]+)',
                r'whatsapp.*?(\+?55\d{10,11})',
            ]

            for pattern in whatsapp_patterns:
                match = re.search(pattern, html_text)
                if match:
                    data['whatsapp'] = match.group(1)
                    break

            # Buscar telefone
            # Padrões brasileiros: (XX) XXXXX-XXXX, (XX) XXXX-XXXX
            phone_patterns = [
                r'\(?(\d{2})\)?[\s-]?9?\d{4}[\s-]?\d{4}',
                r'\+55[\s-]?\(?(\d{2})\)?[\s-]?9?\d{4}[\s-]?\d{4}',
            ]

            for pattern in phone_patterns:
                match = re.search(pattern, html_text)
                if match:
                    data['phone'] = match.group(0)
                    break

            return data

        except Exception as e:
            print(f"⚠️ Erro ao fazer scraping do site {website_url}: {e}")
            return {'instagram': None, 'whatsapp': None, 'phone': None}

    def _guess_instagram_handle(self, business_name: str, city: Optional[str] = None) -> Optional[str]:
        """
        Tenta adivinhar o handle do Instagram baseado no nome da empresa.
        Retorna sugestões para o usuário validar manualmente.

        Nota: Não fazemos verificação automática pois isso violaria os termos do Instagram.
        """
        # Limpar nome: remover acentos, espaços, caracteres especiais
        import unicodedata

        clean_name = business_name.lower()
        clean_name = ''.join(
            c for c in unicodedata.normalize('NFD', clean_name)
            if unicodedata.category(c) != 'Mn'
        )
        clean_name = re.sub(r'[^a-z0-9]', '', clean_name)

        # Remover palavras comuns
        common_words = ['cafe', 'coffee', 'bar', 'restaurante', 'padaria', 'lanchonete']
        for word in common_words:
            clean_name = clean_name.replace(word, '')

        # Sugestões possíveis
        suggestions = [
            clean_name,
            f"{clean_name}oficial",
            f"{clean_name}coffee",
            f"{clean_name}cafe",
        ]

        # Adicionar variações com cidade se fornecida
        if city:
            clean_city = re.sub(r'[^a-z0-9]', '', city.lower())
            suggestions.extend([
                f"{clean_name}{clean_city}",
                f"{clean_name}.{clean_city}",
            ])

        # Retornar primeira sugestão válida (mínimo 3 caracteres)
        for suggestion in suggestions:
            if len(suggestion) >= 3:
                return suggestion

        return None

    def _extract_whatsapp_from_phone(self, phone: str) -> str:
        """
        Extrai número de WhatsApp do telefone.
        Assume que telefones brasileiros têm WhatsApp.
        """
        # Remover tudo que não é número
        clean_phone = re.sub(r'\D', '', phone)

        # Se já tem código do país, retornar
        if clean_phone.startswith('55'):
            return clean_phone

        # Adicionar código do Brasil
        if len(clean_phone) == 11 or len(clean_phone) == 10:
            return f"55{clean_phone}"

        return clean_phone

    def validate_instagram_handle(self, handle: str) -> bool:
        """
        Valida se um handle do Instagram existe.

        IMPORTANTE: Uso limitado - Instagram pode bloquear requisições automatizadas.
        Use apenas para validação manual ocasional.
        """
        if not handle:
            return False

        try:
            url = f"https://www.instagram.com/{handle.replace('@', '')}/"
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False

    def enrich_batch(
        self,
        leads: List[Dict],
        google_maps_client=None,
        delay_seconds: float = 1.0
    ) -> List[Dict]:
        """
        Enriquece múltiplos leads em lote.

        Args:
            leads: Lista de leads para enriquecer
            google_maps_client: Cliente do Google Maps
            delay_seconds: Delay entre requisições (para evitar rate limiting)

        Returns:
            Lista de leads enriquecidos
        """
        enriched_leads = []

        for i, lead in enumerate(leads):
            print(f"🔍 Enriquecendo lead {i+1}/{len(leads)}: {lead.get('name')}")

            try:
                enriched = self.enrich_lead(lead, google_maps_client)
                enriched_leads.append(enriched)

                # Delay entre requisições
                if i < len(leads) - 1:
                    time.sleep(delay_seconds)

            except Exception as e:
                print(f"❌ Erro ao enriquecer lead {lead.get('name')}: {e}")
                enriched_leads.append(lead)

        return enriched_leads