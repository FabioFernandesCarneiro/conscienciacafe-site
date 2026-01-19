from src.db import init_engine, Base, session_scope
from src.models import Account, Category

def init_db():
    print("Initializing database...")
    engine = init_engine()
    Base.metadata.create_all(engine)
    
    with session_scope() as session:
        # Seed Accounts
        if session.query(Account).count() == 0:
            print("Seeding accounts...")
            accounts = [
                Account(name="Nubank", type="checking", bank_name="Nubank"),
                Account(name="Cartão Corporativo", type="credit_card", bank_name="Nubank"),
                Account(name="Caixinha", type="cash", bank_name="Caixa")
            ]
            session.add_all(accounts)
            
        # Seed Categories
        if session.query(Category).count() == 0:
            print("Seeding categories...")
            categories = [
                # Revenue
                Category(name="Vendas Balcão", type="revenue"),
                Category(name="Vendas B2B", type="revenue"),
                Category(name="Outras Receitas", type="revenue"),
                
                # Expenses
                Category(name="Fornecedores", type="expense"),
                Category(name="Aluguel", type="expense"),
                Category(name="Energia", type="expense"),
                Category(name="Água", type="expense"),
                Category(name="Internet", type="expense"),
                Category(name="Pessoal", type="expense"),
                Category(name="Marketing", type="expense"),
                Category(name="Impostos", type="expense"),
                Category(name="Taxas Bancárias", type="expense"),
                Category(name="Outras Despesas", type="expense"),
                
                # Transfers
                Category(name="Transferência", type="transfer")
            ]
            session.add_all(categories)
            
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
