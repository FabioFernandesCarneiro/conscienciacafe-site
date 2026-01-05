# Consciência Café - Monorepo

Repositório centralizado com todos os projetos do Consciência Café.

## Estrutura

```
ConscienciaCafe/
├── apps/
│   ├── site/           # Site institucional (Astro + Tailwind)
│   ├── financeiro/     # Sistema de gestão financeira (Python/Flask)
│   └── intellicoffee/  # App de gestão (Flutter + Firebase)
└── README.md
```

## Projetos

### Site (`apps/site/`)

Site institucional do Consciência Café com blog sobre café.

**Tecnologias:** Astro, Tailwind CSS, TypeScript

```bash
cd apps/site
npm install
npm run dev      # Dev server em localhost:4321
npm run build    # Build para produção
```

### Financeiro (`apps/financeiro/`)

Sistema de gestão financeira com conciliação bancária inteligente, integração Omie ERP e CRM B2B.

**Tecnologias:** Python, Flask, SQLAlchemy, scikit-learn

```bash
cd apps/financeiro
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
cp .env.example .env      # Configurar variáveis de ambiente
python app.py
```

### IntelliCoffee (`apps/intellicoffee/`)

Aplicativo de gestão para cafeterias com suporte a iOS, Android e Web.

**Tecnologias:** Flutter, Dart, Firebase (Firestore, Auth, Functions)

```bash
cd apps/intellicoffee
flutter pub get
flutter run -d chrome     # Web
flutter run               # Mobile
```

## Desenvolvimento

Cada projeto mantém suas próprias dependências e pode ser desenvolvido independentemente.

---

Consciência Café - Foz do Iguaçu, PR
