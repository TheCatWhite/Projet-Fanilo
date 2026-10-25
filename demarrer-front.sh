#!/usr/bin/env bash
# Lance le frontend Angular sur http://localhost:5173
set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$RACINE/factcheck-mada-front"

if [[ ! -d node_modules ]]; then
  echo "Installation des dépendances npm..."
  npm install
fi

exec npm start
