-- ============================================================================
--  Sistema de Versionado Temporal de Estructura Académica
--  UTEQ · Sistema de Gestión de Vinculación
-- ----------------------------------------------------------------------------
--  Problema que resuelve:
--    Las facultades y carreras cambian de nombre, se crean o se desactivan
--    con el paso de los períodos. Un proyecto histórico debe mostrar el
--    nombre de la facultad TAL COMO SE LLAMABA en su período, no el actual.
--
--  Estrategia:
--    - facultad / carrera        -> IDENTIDAD canónica (nunca cambia el id)
--    - facultad_periodo          -> SNAPSHOT inmutable del nombre/estado por período
--    - carrera_periodo           -> SNAPSHOT inmutable de la carrera por período
--    - estructura_cambio         -> BITÁCORA de auditoría de cada cambio confirmado
--
--  Un proyecto sigue apuntando a id_facultad (identidad), pero su nombre
--  histórico se obtiene con:
--    JOIN facultad_periodo ON (id_facultad = proyecto.id_facultad
--                              AND id_periodo = proyecto.id_periodo_inicio)
-- ============================================================================

BEGIN;

-- ── SNAPSHOT DE FACULTADES POR PERÍODO ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS facultad_periodo (
    id_facultad_periodo SERIAL       PRIMARY KEY,
    id_facultad         INTEGER      NOT NULL REFERENCES facultad(id_facultad),
    id_periodo          INTEGER      NOT NULL REFERENCES periodo_academico(id_periodo),
    codigo              VARCHAR(15)  NOT NULL,
    nombre              VARCHAR(200) NOT NULL,
    nombre_corto        VARCHAR(80),
    campus              VARCHAR(80),
    vigente             BOOLEAN      NOT NULL DEFAULT TRUE,   -- ¿la facultad se ofertó en este período?
    creado_en           TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_facultad_periodo UNIQUE (id_facultad, id_periodo)
);

-- ── SNAPSHOT DE CARRERAS POR PERÍODO ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS carrera_periodo (
    id_carrera_periodo  SERIAL       PRIMARY KEY,
    id_carrera          INTEGER      NOT NULL REFERENCES carrera(id_carrera),
    id_facultad_periodo INTEGER      NOT NULL REFERENCES facultad_periodo(id_facultad_periodo),
    id_periodo          INTEGER      NOT NULL REFERENCES periodo_academico(id_periodo),
    codigo              VARCHAR(50),
    nombre              VARCHAR(200) NOT NULL,
    horas_vinculacion   INTEGER      NOT NULL DEFAULT 160,
    vigente             BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en           TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_carrera_periodo UNIQUE (id_carrera, id_periodo)
);

-- ── BITÁCORA DE CAMBIOS ESTRUCTURALES ───────────────────────────────────────
--  Registra cada decisión tomada en la reconciliación al crear un período.
CREATE TABLE IF NOT EXISTS estructura_cambio (
    id_cambio      SERIAL      PRIMARY KEY,
    id_periodo     INTEGER     NOT NULL REFERENCES periodo_academico(id_periodo),
    entidad_tipo   VARCHAR(10) NOT NULL,   -- 'FACULTAD' | 'CARRERA'
    entidad_id     INTEGER     NOT NULL,   -- id_facultad | id_carrera
    tipo_cambio    VARCHAR(15) NOT NULL,   -- CREADA | RENOMBRADA | DESACTIVADA | REACTIVADA | SIN_CAMBIO
    valor_anterior TEXT,
    valor_nuevo    TEXT,
    id_usuario     INTEGER     REFERENCES usuario(id_usuario),
    creado_en      TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ── ÍNDICES DE CONSULTA ─────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_facultad_periodo_periodo  ON facultad_periodo(id_periodo);
CREATE INDEX IF NOT EXISTS idx_facultad_periodo_facultad ON facultad_periodo(id_facultad);
CREATE INDEX IF NOT EXISTS idx_carrera_periodo_periodo   ON carrera_periodo(id_periodo);
CREATE INDEX IF NOT EXISTS idx_carrera_periodo_carrera   ON carrera_periodo(id_carrera);
CREATE INDEX IF NOT EXISTS idx_carrera_periodo_facper    ON carrera_periodo(id_facultad_periodo);
CREATE INDEX IF NOT EXISTS idx_estructura_cambio_periodo ON estructura_cambio(id_periodo);
CREATE INDEX IF NOT EXISTS idx_estructura_cambio_entidad ON estructura_cambio(entidad_tipo, entidad_id);

COMMIT;
