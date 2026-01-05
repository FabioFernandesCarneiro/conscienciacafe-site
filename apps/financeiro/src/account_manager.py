"""
Gerenciador de múltiplas contas bancárias
"""

import json
import os
from typing import Dict, List, Optional
from enum import Enum

class AccountType(Enum):
    CHECKING = "conta_corrente"
    SAVINGS = "poupanca" 
    CREDIT_CARD = "cartao_credito"
    CASH = "caixinha"

class AccountManager:
    def __init__(self, config_file: str = "./data/accounts_config.json"):
        self.config_file = config_file
        self.accounts = self._load_config()
    
    def _load_config(self) -> Dict:
        """Carrega configuração de contas ou cria uma padrão"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar config: {e}")
        
        # Configuração padrão
        default_config = {
            "accounts": {
                "conta_corrente": {
                    "name": "Conta Corrente Principal",
                    "type": "checking",
                    "omie_account_id": None,
                    "patterns": ["corrente", "checking"],
                    "description": "Conta corrente principal da empresa"
                },
                "caixinha": {
                    "name": "Caixinha",
                    "type": "cash", 
                    "omie_account_id": None,
                    "patterns": ["caixa", "dinheiro", "cash"],
                    "description": "Controle de caixa físico"
                },
                "cartao_credito": {
                    "name": "Cartão de Crédito",
                    "type": "credit_card",
                    "omie_account_id": None,
                    "patterns": ["cartao", "credit", "credito"],
                    "description": "Cartão de crédito empresarial"
                }
            }
        }
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict):
        """Salva configuração no arquivo"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def detect_account_from_ofx(self, account_id: str, account_name: str = "") -> Optional[str]:
        """
        Detecta tipo de conta baseado no ID da conta no OFX
        """
        search_text = f"{account_id} {account_name}".lower()
        
        for account_key, account_info in self.accounts.get("accounts", {}).items():
            patterns = account_info.get("patterns", [])
            for pattern in patterns:
                if pattern.lower() in search_text:
                    return account_key
        
        return None
    
    def get_account_info(self, account_key: str) -> Optional[Dict]:
        """Obtém informações da conta"""
        return self.accounts.get("accounts", {}).get(account_key)
    
    def list_accounts(self) -> List[Dict]:
        """Lista todas as contas configuradas"""
        accounts_list = []
        for key, info in self.accounts.get("accounts", {}).items():
            accounts_list.append({
                "key": key,
                "name": info.get("name"),
                "type": info.get("type"), 
                "description": info.get("description")
            })
        return accounts_list
    
    def add_account(self, key: str, name: str, account_type: str, patterns: List[str], description: str = ""):
        """Adiciona nova conta"""
        if "accounts" not in self.accounts:
            self.accounts["accounts"] = {}
            
        self.accounts["accounts"][key] = {
            "name": name,
            "type": account_type,
            "omie_account_id": None,
            "patterns": patterns,
            "description": description
        }
        
        self._save_config(self.accounts)
    
    def get_omie_account_mapping(self, account_key: str) -> Optional[str]:
        """Obtém ID da conta no Omie"""
        account = self.get_account_info(account_key)
        return account.get("omie_account_id") if account else None
    
    def set_omie_account_mapping(self, account_key: str, omie_account_id: str):
        """Define mapeamento para conta no Omie"""
        if account_key in self.accounts.get("accounts", {}):
            self.accounts["accounts"][account_key]["omie_account_id"] = omie_account_id
            self._save_config(self.accounts)
    
    def select_omie_account_for_ofx(self, account_key: str, omie_contas: list) -> str:
        """
        Permite ao usuário selecionar conta do Omie para mapear com a conta do OFX
        """
        account_info = self.get_account_info(account_key)
        account_name = account_info['name'] if account_info else account_key
        
        print(f"\n🏦 MAPEAR CONTA: {account_name}")
        print("=" * 50)
        
        if not omie_contas:
            print("❌ Nenhuma conta corrente encontrada no Omie")
            return None
        
        print(f"📋 Contas disponíveis no Omie:")
        for i, conta in enumerate(omie_contas):
            descricao = conta.get('descricao', 'Sem descrição')
            banco = conta.get('banco_nome', conta.get('banco_codigo', 'N/A'))
            agencia = conta.get('agencia', 'N/A')
            conta_num = conta.get('conta', 'N/A')
            
            print(f"   {i+1}. {descricao}")
            print(f"      Banco: {banco} | Ag: {agencia} | Conta: {conta_num}")
            print(f"      ID Omie: {conta.get('codigo_omie', 'N/A')}")
            print()
        
        print(f"   0. Pular (não mapear esta conta)")
        
        while True:
            try:
                choice = input(f"Escolha a conta do Omie (0-{len(omie_contas)}): ").strip()
                
                if choice == '0':
                    print("⏭️ Conta não mapeada")
                    return None
                
                index = int(choice) - 1
                
                if 0 <= index < len(omie_contas):
                    selected_account = omie_contas[index]
                    omie_id = selected_account.get('codigo_omie')
                    
                    # Salvar mapeamento
                    self.set_omie_account_mapping(account_key, omie_id)
                    
                    print(f"✅ Mapeamento salvo:")
                    print(f"   {account_name} → {selected_account.get('descricao')} (ID: {omie_id})")
                    
                    return omie_id
                else:
                    print(f"❌ Opção inválida. Digite um número entre 0 e {len(omie_contas)}")
                    
            except ValueError:
                print("❌ Digite apenas números")
            except KeyboardInterrupt:
                print("\n⚠️ Operação cancelada")
                return None