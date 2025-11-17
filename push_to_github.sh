#!/bin/bash
cd "/c/Users/gchav/OneDrive/Documentos/Claude_acceso/inegi_mcp"

echo "=== Verificando estado actual ==="
git status

echo ""
echo "=== Agregando archivos ==="
git add .

echo ""
echo "=== Verificando qué se agregará ==="
git status

echo ""
echo "=== Creando commit ==="
git commit -m "Initial commit: INEGI MCP Server - Servidor para acceder a APIs del INEGI desde Claude"

echo ""
echo "=== Verificando configuración remota ==="
git remote -v

echo ""
echo "=== Haciendo push a GitHub ==="
git push -u origin main

echo ""
echo "=== Push completado ==="
