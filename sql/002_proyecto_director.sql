-- ============================================================================
--  Campo Director del proyecto (ficha oficial UTEQ)
--  La página oficial muestra: Director: Ing. Nombre, MSc. + correo institucional
-- ============================================================================
BEGIN;

ALTER TABLE proyecto ADD COLUMN IF NOT EXISTS director_nombre  VARCHAR(200);
ALTER TABLE proyecto ADD COLUMN IF NOT EXISTS director_correo  VARCHAR(150);

COMMIT;
