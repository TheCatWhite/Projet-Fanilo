#!/usr/bin/env bash
# Vérifie le backend et le frontend sans lancer les serveurs.
# Usage : ./verifier-tout.sh [--e2e]
set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$RACINE/env/bin/python"

echo "== Backend : configuration =="
cd "$RACINE/backend"
"$PYTHON" manage.py check
"$PYTHON" manage.py makemigrations --check --dry-run
"$PYTHON" -m pip check

echo "== Backend : tests =="
"$PYTHON" manage.py test investigation -v 1

echo "== Backend : schéma OpenAPI =="
"$PYTHON" manage.py spectacular --file /tmp/opencode/openapi.yaml --validate

echo "== Frontend : build =="
cd "$RACINE/factcheck-mada-front"
npm run build

echo "== Frontend : tests unitaires =="
npm test -- --watch=false

if [[ "${1:-}" == "--e2e" ]]; then
  echo "== Frontend : tests end-to-end =="
  echo "Le backend doit être lancé (./demarrer-backend.sh)."
  npm run test:e2e
fi

echo "Toutes les vérifications sont passées."
