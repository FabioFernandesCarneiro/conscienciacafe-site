#!/bin/bash
# Script para iniciar o sistema web de gestao - Consciencia Cafe
# Requer Python 3.11 instalado via Homebrew

cd "$(dirname "$0")"

PYTHON="/opt/homebrew/bin/python3.11"

if [ ! -f "$PYTHON" ]; then
    echo "Python 3.11 nao encontrado em $PYTHON"
    echo "Instale com: brew install python@3.11"
    exit 1
fi

echo "Iniciando servidor web..."
echo "Acesse: http://localhost:5002"
echo ""

$PYTHON app.py
