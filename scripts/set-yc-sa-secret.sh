#!/usr/bin/env bash
# Записывает ключ SA в GitHub Secrets без порчи многострочного JSON.
#
# Использование:
#   ./scripts/set-yc-sa-secret.sh path/to/authorized_key.json
#   ./scripts/set-yc-sa-secret.sh path/to/authorized_key.json --base64
#
set -euo pipefail

KEY_FILE="${1:?Укажите путь к authorized_key.json}"
MODE="${2:-}"

if [[ ! -f "$KEY_FILE" ]]; then
  echo "Файл не найден: $KEY_FILE" >&2
  exit 1
fi

if ! python3 -c "import json; d=json.load(open('$KEY_FILE')); assert {'id','service_account_id','private_key'} <= d.keys()"; then
  echo "Файл не похож на authorized_key.json Yandex Cloud" >&2
  exit 1
fi

REPO="${GITHUB_REPOSITORY:-}"
if [[ -z "$REPO" ]]; then
  REPO="$(git remote get-url origin 2>/dev/null | sed -n 's#.*github\.com[:/]\([^/]*/[^/.]*\).*#\1#p' || true)"
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Установите GitHub CLI: https://cli.github.com/" >&2
  exit 1
fi

SECRET_NAME="YC_SERVICE_ACCOUNT_KEY_FILE"

if [[ "$MODE" == "--base64" ]]; then
  VALUE="$(base64 -w0 "$KEY_FILE")"
  gh secret set "$SECRET_NAME" --body "$VALUE" ${REPO:+--repo "$REPO"}
  echo "Секрет $SECRET_NAME записан (base64, ${#VALUE} символов)."
else
  gh secret set "$SECRET_NAME" --body-file "$KEY_FILE" ${REPO:+--repo "$REPO"}
  echo "Секрет $SECRET_NAME записан из файла $KEY_FILE."
fi

echo "Проверка локально:"
SA_KEY="$(cat "$KEY_FILE")" python3 infra/prepare_sa_key.py && rm -f authorized_key.json
echo "OK — можно запускать workflow Terraform."
