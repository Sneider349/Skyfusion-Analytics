#!/bin/bash
# On-open script para devcontainer de Skyfusion Analytics
# Ejecuta cuando se abre el proyecto en Codespaces

set -e

echo ""
echo "=========================================="
echo "Bienvenido a Skyfusion Analytics"
echo "=========================================="
echo ""
echo "Este contenedor incluye:"
echo "  - GDAL 3.6.2 (sistema)"
echo "  - Rasterio 1.3.8 (Python)"
echo "  - Python 3.10"
echo "  - Node.js 18+"
echo "  - Jupyter notebooks"
echo ""
echo "Estructura del proyecto:"
echo "  /workspace/"
echo "    ├── .devcontainer/   # Config del contenedor"
echo "    ├── agents/          # Agentes Node.js"
echo "    ├── src/"
echo "    │   ├── python/      # Scripts Python"
echo "    │   ├── frontend/     # React app"
echo "    │   └── backend/      # Express API"
echo "    └── data/            # Datos del proyecto"
echo ""
echo "Para comenzar:"
echo "  1. Abre una terminal (Ctrl+`)"
echo "  2. Ejecuta: npm start"
echo "  3. Abre http://localhost:3000"
echo ""
echo "=========================================="
