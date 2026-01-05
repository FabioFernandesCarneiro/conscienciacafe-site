# Melhorias para CRM B2B - Consciência Café

## ✅ Correções Implementadas

### 1. Instagram e WhatsApp no Google Maps
**Problema**: A API do Google Maps Text Search não retorna links de Instagram e WhatsApp diretamente.

**Solução Implementada**:
- ✅ Adicionada integração com **Place Details API** para buscar mais informações
- ✅ Campos `instagram` e `whatsapp` agora disponíveis no banco de dados
- ✅ Interface de edição de leads permite adicionar manualmente Instagram e WhatsApp
- ✅ Links clicáveis para WhatsApp (abre conversa) e Instagram (perfil)
- ✅ Telefone pode ser automaticamente sugerido como WhatsApp

**Limitações da API do Google**:
- Instagram e WhatsApp não são retornados pela API oficial do Google Maps
- Esses dados precisam ser:
  1. Preenchidos manualmente após importar o lead
  2. Extraídos do website da empresa (implementação futura via web scraping)
  3. Buscados em outras fontes (redes sociais, APIs alternativas)

---

## 🎯 Melhorias Sugeridas para o Fluxo B2B

### **Fase 1: Descoberta de Leads**

#### Atual:
- Busca manual no Google Maps
- Importação de leads básicos

#### Melhorias Propostas:

**1.1 Busca em Múltiplas Fontes**
```python
# Adicionar integrações:
- LinkedIn Sales Navigator API
- Instagram Graph API (busca por localização + categoria)
- Base de dados públicos (CNPJ, Receita Federal)
- Scraping ético de diretórios empresariais
```

**1.2 Enriquecimento Automático de Dados**
```python
# Após importar lead do Google Maps:
1. Buscar CNPJ no site da Receita Federal
2. Verificar porte da empresa (MEI, Pequeno, Médio, Grande)
3. Buscar perfil no Instagram automaticamente
4. Validar se o telefone tem WhatsApp ativo (API WhatsApp Business)
5. Extrair informações do website (scraping)
```

**Implementação Sugerida**:
```python
# src/b2b/lead_enrichment.py
class LeadEnrichmentService:
    def enrich_from_cnpj(self, cnpj: str) -> Dict:
        """Busca dados da Receita Federal"""
        pass

    def find_instagram(self, business_name: str, city: str) -> Optional[str]:
        """Tenta encontrar perfil no Instagram"""
        pass

    def validate_whatsapp(self, phone: str) -> bool:
        """Verifica se número tem WhatsApp ativo"""
        pass

    def scrape_website_contacts(self, website: str) -> Dict:
        """Extrai Instagram/WhatsApp do site"""
        pass
```

---

### **Fase 2: Qualificação de Leads**

#### Atual:
- Status manual (new, contacted, qualified, etc)

#### Melhorias Propostas:

**2.1 Sistema de Pontuação (Lead Scoring)**
```python
# Critérios de pontuação:
pontos = {
    'tem_website': 10,
    'tem_instagram': 15,
    'tem_whatsapp': 15,
    'porte_empresa': {'MEI': 5, 'Pequeno': 10, 'Médio': 15, 'Grande': 20},
    'localizacao_estrategica': 10,
    'categoria_prioritaria': 20,  # Ex: cafeterias, restaurantes
    'horario_funcionamento': 5,
}

# Score total determina prioridade:
- 0-30: Baixa prioridade
- 31-60: Média prioridade
- 61-100: Alta prioridade
```

**2.2 Workflow Automático**
```python
# Triggers automáticos:
if lead.score >= 60 and not lead.contacted:
    send_notification_to_sales_team()
    create_first_contact_task()

if lead.has_instagram and not lead.instagram_dm_sent:
    suggest_dm_template()
```

---

### **Fase 3: Contato e Relacionamento**

#### Atual:
- Interações manuais (em desenvolvimento)

#### Melhorias Propostas:

**3.1 Templates de Mensagens**
```python
# Criar biblioteca de templates para cada canal:
templates = {
    'whatsapp_first_contact': """
        Olá {nome_empresa}!
        Somos da Consciência Café e gostaríamos de apresentar nossos produtos...
    """,
    'instagram_dm': "...",
    'email_follow_up': "..."
}
```

**3.2 Histórico de Interações Completo**
```python
# Tabela crm_interactions já existe, expandir para:
- Registrar automaticamente envio de mensagens WhatsApp
- Capturar respostas (via webhook WhatsApp Business API)
- Log de visualizações de Instagram DM
- Registrar ligações telefônicas (integração com VoIP)
```

**3.3 Agendamento de Follow-ups**
```python
# Sistema de lembretes:
- "Ligar para lead X em 3 dias"
- "Enviar amostra grátis para lead Y"
- "Lead Z não respondeu há 7 dias - tentar outro canal"
```

---

### **Fase 4: Amostras e Visitas**

#### Proposta:

**4.1 Gestão de Amostras**
```sql
CREATE TABLE crm_samples (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    product_name TEXT,
    quantity INTEGER,
    sent_date DATE,
    delivery_status TEXT, -- pending, delivered, failed
    tracking_code TEXT,
    cost DECIMAL(10,2),
    feedback_received BOOLEAN DEFAULT 0,
    feedback_rating INTEGER, -- 1-5
    feedback_notes TEXT,
    FOREIGN KEY (lead_id) REFERENCES crm_leads(id)
);
```

**4.2 Agendamento de Visitas**
```sql
CREATE TABLE crm_visits (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    scheduled_date DATETIME,
    visit_type TEXT, -- presentation, delivery, meeting
    assigned_to TEXT,
    status TEXT, -- scheduled, completed, cancelled
    address TEXT,
    notes TEXT,
    result TEXT,
    next_steps TEXT,
    FOREIGN KEY (lead_id) REFERENCES crm_leads(id)
);
```

**4.3 Integração com Google Calendar**
```python
# Sincronizar visitas agendadas com calendário da equipe
from google.oauth2 import service_account
from googleapiclient.discovery import build

def schedule_visit_to_calendar(visit_data):
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': f'Visita - {visit_data["lead_name"]}',
        'location': visit_data['address'],
        'start': {'dateTime': visit_data['scheduled_date']},
        'end': {'dateTime': visit_data['scheduled_date'] + timedelta(hours=1)},
    }
    service.events().insert(calendarId='primary', body=event).execute()
```

---

### **Fase 5: Conversão para Cliente**

#### Proposta:

**5.1 Processo de Conversão**
```python
# Quando lead vira cliente:
def convert_lead_to_customer(lead_id: int):
    lead = crm_service.get_lead(lead_id)

    # 1. Criar cliente no Omie
    omie_customer_id = omie_client.create_customer({
        'name': lead['name'],
        'cnpj': lead.get('cnpj'),
        'phone': lead.get('whatsapp'),
        'email': lead.get('email'),
        'address': lead.get('address_line'),
    })

    # 2. Atualizar lead
    crm_service.update_lead(lead_id, {
        'status': 'won',
        'is_customer': True,
        'converted_account_id': omie_customer_id
    })

    # 3. Criar primeiro pedido/orçamento
    # 4. Notificar equipe
    # 5. Iniciar programa de fidelização
```

**5.2 Análise de Conversão**
```python
# Dashboard de métricas:
- Taxa de conversão por fonte (Google Maps, Instagram, etc)
- Tempo médio do lead até conversão
- ROI por canal de aquisição
- Leads perdidos: motivos e análise
```

---

## 🛠️ Implementações Prioritárias

### **Prioridade 1 (Semana 1-2)**
1. ✅ Corrigir exibição de Instagram/WhatsApp (FEITO)
2. ✅ Adicionar edição de leads (FEITO)
3. Implementar enriquecimento manual facilitado
4. Criar templates de mensagens

### **Prioridade 2 (Semana 3-4)**
1. Sistema de Lead Scoring
2. Gestão de amostras (tabela + interface)
3. Agendamento de visitas
4. Histórico de interações melhorado

### **Prioridade 3 (Mês 2)**
1. Integração WhatsApp Business API
2. Enriquecimento automático (CNPJ, Instagram)
3. Dashboard de métricas de conversão
4. Automação de follow-ups

### **Prioridade 4 (Futuro)**
1. IA para análise de sentimento em mensagens
2. Previsão de taxa de conversão com ML
3. Integração com outras plataformas (LinkedIn, etc)
4. App móvel para vendedores

---

## 📊 Estrutura de Dados Adicional

### Tabelas Sugeridas:

```sql
-- Lead Scoring
CREATE TABLE crm_lead_scores (
    lead_id INTEGER PRIMARY KEY,
    total_score INTEGER DEFAULT 0,
    last_updated TIMESTAMP,
    scoring_breakdown JSON,
    FOREIGN KEY (lead_id) REFERENCES crm_leads(id)
);

-- Templates de Mensagens
CREATE TABLE crm_message_templates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    channel TEXT, -- whatsapp, instagram, email, sms
    subject TEXT,
    body TEXT NOT NULL,
    variables JSON, -- {nome_empresa}, {produto}, etc
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tarefas e Follow-ups
CREATE TABLE crm_tasks (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    task_type TEXT, -- call, send_sample, visit, email
    title TEXT NOT NULL,
    description TEXT,
    due_date DATETIME,
    assigned_to TEXT,
    status TEXT DEFAULT 'pending', -- pending, completed, cancelled
    priority TEXT DEFAULT 'medium', -- low, medium, high
    completed_at TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES crm_leads(id)
);

-- Pipeline de Vendas
CREATE TABLE crm_pipeline_stages (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    display_order INTEGER,
    is_final BOOLEAN DEFAULT 0, -- won/lost
    active BOOLEAN DEFAULT 1
);

-- Histórico de mudanças de status
CREATE TABLE crm_status_history (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    from_status TEXT,
    to_status TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT,
    notes TEXT,
    FOREIGN KEY (lead_id) REFERENCES crm_leads(id)
);
```

---

## 🎨 Melhorias de Interface

### Dashboard CRM:
1. **Kanban Board**: Visualizar leads por status (estilo Trello)
2. **Mapa de Leads**: Mostrar leads em um mapa (Google Maps integrado)
3. **Calendário**: Visão das visitas e follow-ups agendados
4. **Gráficos**: Taxa de conversão, funil de vendas, leads por origem

### Página de Lead Individual:
1. Linha do tempo de todas as interações
2. Botões rápidos: "Enviar WhatsApp", "Agendar Visita", "Enviar Amostra"
3. Informações enriquecidas: porte da empresa, faturamento estimado
4. Sugestões de ações baseadas em IA

---

## 🔐 Considerações Importantes

### LGPD e Privacidade:
- Obter consentimento para armazenar dados
- Permitir que leads solicitem exclusão de dados
- Não armazenar dados sensíveis desnecessários

### APIs e Custos:
- Google Maps API: Cobrado por request (Place Details é mais caro)
- WhatsApp Business API: Requer aprovação e tem custos por mensagem
- Considerar limites de taxa (rate limits)

### Performance:
- Cache de resultados do Google Maps (evitar chamadas repetidas)
- Background jobs para enriquecimento de dados (não bloquear interface)
- Indexação adequada no SQLite para queries rápidas

---

## 📝 Próximos Passos Imediatos

1. Testar as correções implementadas (Instagram/WhatsApp)
2. Definir quais melhorias priorizar com a equipe
3. Criar protótipo do Lead Scoring
4. Implementar gestão de amostras
5. Criar templates de mensagens iniciais

---

**Última atualização**: 2025-09-29
**Autor**: Claude Code