"""
Detector de tipo de arquivo OFX para identificar conta corrente vs cartão de crédito
"""

def detect_ofx_account_type(file_path: str) -> dict:
    """
    Detecta o tipo de conta OFX analisando o cabeçalho
    
    Returns:
        dict: {
            'type': 'checking' | 'credit_card',
            'omie_account_id': int,
            'account_id': str,
            'description': str
        }
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Detectar se é conta corrente ou cartão
        if '<BANKMSGSRSV1>' in content and '<ACCTTYPE>CHECKING</ACCTTYPE>' in content:
            # Conta Corrente
            return {
                'type': 'checking',
                'omie_account_id': 8,  # ID da conta corrente no Omie
                'account_id': extract_checking_account_id(content),
                'description': 'Conta Corrente Nubank PJ'
            }
        
        elif '<CREDITCARDMSGSRSV1>' in content and '<CCACCTFROM>' in content:
            # Cartão de Crédito
            return {
                'type': 'credit_card', 
                'omie_account_id': 9,  # ID do cartão no Omie
                'account_id': extract_credit_card_account_id(content),
                'description': 'Cartão de Crédito Nubank PJ'
            }
        
        else:
            # Formato desconhecido - usar conta corrente como padrão
            return {
                'type': 'unknown',
                'omie_account_id': 8,  # Padrão conta corrente
                'account_id': 'unknown',
                'description': 'Tipo desconhecido - usando conta corrente como padrão'
            }
            
    except Exception as e:
        print(f"Erro ao detectar tipo OFX: {e}")
        return {
            'type': 'error',
            'omie_account_id': 8,  # Padrão conta corrente
            'account_id': 'error',
            'description': f'Erro na detecção: {e}'
        }

def extract_checking_account_id(content: str) -> str:
    """Extrai ID da conta corrente do OFX"""
    try:
        import re
        # Procurar padrão <ACCTID>número-dígito</ACCTID>
        match = re.search(r'<ACCTID>([^<]+)</ACCTID>', content)
        if match:
            return match.group(1)
        return 'unknown'
    except:
        return 'unknown'

def extract_credit_card_account_id(content: str) -> str:
    """Extrai ID do cartão de crédito do OFX"""
    try:
        import re
        # Procurar padrão <CCACCTFROM><ACCTID>uuid</ACCTID>
        match = re.search(r'<CCACCTFROM>.*?<ACCTID>([^<]+)</ACCTID>', content, re.DOTALL)
        if match:
            return match.group(1)
        return 'unknown'
    except:
        return 'unknown'

def get_filename_pattern_info(filename: str) -> dict:
    """
    Analisa o padrão do nome do arquivo para informações adicionais
    """
    filename_lower = filename.lower()
    
    if filename_lower.startswith('nu_'):
        return {
            'pattern': 'conta_corrente',
            'confidence': 'high',
            'source': 'filename_pattern'
        }
    elif filename_lower.startswith('nubank_'):
        return {
            'pattern': 'cartao_credito', 
            'confidence': 'high',
            'source': 'filename_pattern'
        }
    else:
        return {
            'pattern': 'unknown',
            'confidence': 'low',
            'source': 'filename_pattern'
        }

def comprehensive_ofx_analysis(file_path: str) -> dict:
    """
    Análise completa do arquivo OFX combinando cabeçalho e nome do arquivo
    """
    import os
    
    filename = os.path.basename(file_path)
    
    # Análise do cabeçalho (método principal)
    header_info = detect_ofx_account_type(file_path)
    
    # Análise do nome do arquivo (validação)
    filename_info = get_filename_pattern_info(filename)
    
    # Validação cruzada
    validation = 'consistent'
    if header_info['type'] == 'checking' and filename_info['pattern'] != 'conta_corrente':
        validation = 'inconsistent'
    elif header_info['type'] == 'credit_card' and filename_info['pattern'] != 'cartao_credito':
        validation = 'inconsistent'
    
    return {
        'filename': filename,
        'file_path': file_path,
        'detected_type': header_info['type'],
        'omie_account_id': header_info['omie_account_id'],
        'account_id': header_info['account_id'],
        'description': header_info['description'],
        'filename_pattern': filename_info['pattern'],
        'validation': validation,
        'confidence': 'high' if validation == 'consistent' else 'medium'
    }