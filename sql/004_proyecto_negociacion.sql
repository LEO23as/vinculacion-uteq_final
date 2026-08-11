-- ============================================================================
--  Términos de negociación del proyecto (Paso 1 del registro)
--  Y tipo de documento DOC_22 para Mociones y actas (reusa el portafolio
--  de documentos existente en vez de crear una tabla nueva).
-- ============================================================================
BEGIN;

ALTER TABLE proyecto ADD COLUMN IF NOT EXISTS terminos_negociacion TEXT;

INSERT INTO tipo_documento (codigo, nombre, numero_carpeta, descripcion, obligatorio)
SELECT 'DOC_22', 'Mociones y actas', 22, NULL, false
WHERE NOT EXISTS (SELECT 1 FROM tipo_documento WHERE codigo = 'DOC_22');

COMMIT;
