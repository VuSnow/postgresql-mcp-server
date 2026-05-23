#!/bin/bash
# Seed the PostgreSQL database with sample banking data.
# Usage: ./data/seed.sh [DATABASE_URL]
#
# Example:
#   ./data/seed.sh "postgresql://user:pass@localhost:5432/banking"
#   DATABASE_URL="postgresql://..." ./data/seed.sh
#
# Files are executed in order (001, 002, ...) and are idempotent.

set -euo pipefail

DB_URL="${1:-${DATABASE_URL:-}}"

if [[ -z "$DB_URL" ]]; then
    echo "Usage: $0 <DATABASE_URL>"
    echo "  or set DATABASE_URL environment variable"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Seeding database ==="
for sql_file in "$SCRIPT_DIR"/0*.sql; do
    echo "  Running: $(basename "$sql_file")"
    psql "$DB_URL" -f "$sql_file" --quiet --no-psqlrc -v ON_ERROR_STOP=1
done
echo "=== Done: all tables seeded ==="
