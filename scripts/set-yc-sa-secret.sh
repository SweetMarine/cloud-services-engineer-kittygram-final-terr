#!/usr/bin/env bash
# Записывает ключ SA в GitHub Secrets (рекомендуется base64 — надёжнее в Actions).
#
#   ./scripts/set-yc-sa-secret.sh authorized_key.json
#
set -euo pipefail

KEY_FILE="${1:?Укажите путь к authorized_key.json}"

if [[ ! -f "$KEY_FILE" ]]; then
  echo "Файл не найден: $KEY_FILE" >&2
  exit 1
fi

python3 -c "
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
need = {'id', 'service_account_id', 'private_key'}
if not need <= d.keys():
    raise SystemExit(f'В файле нет полей: {need - d.keys()}')
" "$KEY_FILE"

REPO="${GITHUB_REPOSITORY:-}"
if [[ -z "$REPO" ]]; then
  REPO="$(git remote get-url origin 2>/dev/null | sed -n 's#.*github\.com[:/]\([^/]*/[^/.]*\).*#\1#p' || true)"
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Установите GitHub CLI: https://cli.github.com/" >&2
  exit 1
fi

B64="$(base64 -w0 "$KEY_FILE")"
gh secret set YC_SERVICE_ACCOUNT_KEY_B64 --body "$B64" ${REPO:+--repo "$REPO"}
gh secret set YC_SERVICE_ACCOUNT_KEY_FILE --body-file "$KEY_FILE" ${REPO:+--repo "$REPO"}

echo "Записаны секреты: YC_SERVICE_ACCOUNT_KEY_B64 и YC_SERVICE_ACCOUNT_KEY_FILE"

export SA_KEY_B64="$B64"
cd "$(dirname "$0")/../infra"
python3 prepare_sa_key.py --dry-run
echo "Локальная проверка прошла. Запустите workflow Terraform."
