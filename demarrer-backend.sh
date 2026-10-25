#!/usr/bin/env bash
# Lance l'API Django/DRF sur http://localhost:8000/api/
set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$RACINE/env/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "Environnement virtuel introuvable : $PYTHON" >&2
  echo "Créez-le avec : python3 -m venv env && ./env/bin/pip install -r backend/requirements.txt" >&2
  exit 1
fi

cd "$RACINE/backend"
exec "$PYTHON" manage.py runserver "${1:-127.0.0.1:8000}"
