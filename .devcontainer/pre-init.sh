#!/bin/bash
# Pre-init script para devcontainer de Skyfusion Analytics
# Ejecuta ANTES de que el contenedor se cree

set -e

echo "=========================================="
echo "Skyfusion Analytics - Pre-Inicialización"
echo "=========================================="

# Verificar que el archivo requirements.txt existe
if [ ! -f "../requirements.txt" ]; then
    echo "ADVERTENCIA: requirements.txt no encontrado en la raíz del proyecto"
    echo "Creando archivo requirements.txt base..."
fi

# Verificar estructura del proyecto
if [ ! -d "../src/python" ]; then
    echo "ADVERTENCIA: src/python no encontrado"
fi

if [ ! -d "../agents" ]; then
    echo "ADVERTENCIA: agents no encontrado"
fi

echo "Pre-inicialización completada"
echo "=========================================="
