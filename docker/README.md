# Base de datos local con Docker

Réplica local de la base de Supabase para desarrollo **sin latencia de red**.
La app carga mucho más rápido apuntando a este Postgres local.

## Requisitos
- Docker Desktop **corriendo** (abre la app y espera a que el ícono deje de animarse).

## Pasos (primera vez)

### 1. Generar el dump desde Supabase
Con el `.env` de la raíz apuntando todavía a **Supabase**, ejecuta:

```bash
bash docker/dump-supabase.sh
```

Esto crea `docker/initdb/dump.sql` con el esquema `public` y todos los datos.

### 2. Levantar la base local
```bash
docker compose -f docker/docker-compose.yml up -d
```

El contenedor carga `dump.sql` automáticamente la primera vez.
Verifica que esté sano:

```bash
docker compose -f docker/docker-compose.yml ps
```

### 3. Apuntar la app a la BD local
Edita el `.env` de la raíz y cambia el bloque de base de datos (ver
`docker/.env.local.example`):

```
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5433
```

> El puerto local es **5433** (no 5432) para no chocar con un Postgres nativo
> que ya está instalado en la máquina y ocupa el 5432.

> Tip: guarda las líneas de Supabase comentadas (`# DB_HOST=aws-1-...`) para
> poder volver cuando quieras.

### 4. Reiniciar Django
```bash
python manage.py runserver
```

## Comandos útiles

| Acción | Comando |
|---|---|
| Ver estado | `docker compose -f docker/docker-compose.yml ps` |
| Ver logs | `docker compose -f docker/docker-compose.yml logs -f db` |
| Detener | `docker compose -f docker/docker-compose.yml down` |
| Borrar datos y empezar de cero | `docker compose -f docker/docker-compose.yml down -v` |
| Reconstruir desde un dump nuevo | `down -v` y luego `up -d` |

## Volver a Supabase
Restaura el bloque `DB_*` de Supabase en `.env` y reinicia Django.
La base local sigue disponible en Docker para cuando la necesites.

## Notas
- El dump excluye las tablas de sistema de PostGIS (`spatial_ref_sys`,
  `geometry_columns`, `geography_columns`) porque la app no usa geometría;
  las coordenadas son columnas decimales normales.
- Para refrescar la copia local con datos nuevos de Supabase: vuelve a apuntar
  `.env` a Supabase, corre `dump-supabase.sh`, luego `down -v && up -d`.
