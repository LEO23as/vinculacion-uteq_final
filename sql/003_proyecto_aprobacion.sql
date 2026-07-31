-- ============================================================================
--  Datos de la Resolución de aprobación (Paso 2 del registro)
--  Salen del documento DOC_01 y se muestran en el detalle y el mapa.
-- ============================================================================
BEGIN;

ALTER TABLE proyecto ADD COLUMN IF NOT EXISTS fecha_aprobacion       DATE;
ALTER TABLE proyecto ADD COLUMN IF NOT EXISTS resolucion_aprobacion  VARCHAR(300);

COMMIT;
