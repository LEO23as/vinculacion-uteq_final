#!/usr/bin/env bash
# Descarga el esquema public de Supabase a docker/initdb/dump.sql usando un
# contenedor Postgres efímero (no requiere pg_dump instalado en el host).
#
# IMPORTANTE: ejecutar ANTES de cambiar .env a la BD local, porque lee las
# credenciales de Supabase desde el .env actual.
set -euo pipefail

cd "$(dirname "$0")/.."

# Lee credenciales de la BD desde el .env actual (debe apuntar a Supabase)
DB_HOST=$(grep -E '^DB_HOST=' .env | cut -d= -f2-)
DB_PORT=$(grep -E '^DB_PORT=' .env | cut -d= -f2-)
DB_USER=$(grep -E '^DB_USER=' .env | cut -d= -f2-)
DB_NAME=$(grep -E '^DB_NAME=' .env | cut -d= -f2-)
DB_PASSWORD=$(grep -E '^DB_PASSWORD=' .env | cut -d= -f2-)

echo "Volcando $DB_NAME desde $DB_HOST (esquema public)..."

docker run --rm -e PGPASSWORD="$DB_PASSWORD" postgres:17 \
  pg_dump \
    -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" -d "$DB_NAME" \
    --schema=public \
    --no-owner --no-privileges --no-comments \
    --exclude-table=spatial_ref_sys \
    --exclude-table=geometry_columns \
    --exclude-table=geography_columns \
  | sed 's/^CREATE SCHEMA public;/CREATE SCHEMA IF NOT EXISTS public;/' \
  > docker/initdb/dump.sql

LINEAS=$(wc -l < docker/initdb/dump.sql)
echo "OK: docker/initdb/dump.sql generado ($LINEAS líneas)."
