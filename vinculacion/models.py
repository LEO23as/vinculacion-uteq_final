from django.db import models


class PeriodoAcademico(models.Model):
    id_periodo = models.AutoField(primary_key=True)
    codigo = models.CharField(unique=True, max_length=20)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField()
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'periodo_academico'

    def __str__(self):
        return self.nombre


class Facultad(models.Model):
    id_facultad = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=15)
    nombre = models.CharField(max_length=200)
    nombre_corto = models.CharField(max_length=80, blank=True, null=True)
    campus = models.CharField(max_length=80, blank=True, null=True)
    fecha_desde = models.DateField()
    fecha_hasta = models.DateField(blank=True, null=True)
    activo = models.BooleanField()
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'facultad'

    def __str__(self):
        return self.nombre


class Carrera(models.Model):
    id_carrera = models.AutoField(primary_key=True)
    id_facultad = models.ForeignKey(Facultad, models.DO_NOTHING, db_column='id_facultad')
    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20, blank=True, null=True)
    horas_vinculacion = models.IntegerField()
    area_conocimiento = models.CharField(max_length=200, blank=True, null=True)
    sub_area = models.CharField(max_length=200, blank=True, null=True)
    activo = models.BooleanField()
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'carrera'

    def __str__(self):
        return self.nombre


class TipoEntidad(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_entidad'

    def __str__(self):
        return self.nombre


class EntidadCooperante(models.Model):
    id_entidad = models.AutoField(primary_key=True)
    id_tipo = models.ForeignKey(TipoEntidad, models.DO_NOTHING, db_column='id_tipo')
    nombre = models.CharField(max_length=300)
    nombre_corto = models.CharField(max_length=100, blank=True, null=True)
    ruc = models.CharField(unique=True, max_length=15, blank=True, null=True)
    representante_legal = models.CharField(max_length=200, blank=True, null=True)
    cargo_representante = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.CharField(max_length=150, blank=True, null=True)
    pagina_web = models.CharField(max_length=200, blank=True, null=True)
    provincia = models.CharField(max_length=80, blank=True, null=True)
    canton = models.CharField(max_length=80, blank=True, null=True)
    parroquia = models.CharField(max_length=100, blank=True, null=True)
    sector = models.CharField(max_length=200, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    numero_acuerdo = models.CharField(max_length=100, blank=True, null=True)
    fecha_constitucion = models.DateField(blank=True, null=True)
    activo = models.BooleanField()
    observaciones = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'entidad_cooperante'

    def __str__(self):
        return self.nombre


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rol'

    def __str__(self):
        return self.nombre


class Docente(models.Model):
    id_docente = models.AutoField(primary_key=True)
    cedula = models.CharField(unique=True, max_length=13)
    apellidos = models.CharField(max_length=150)
    nombres = models.CharField(max_length=150)
    titulo = models.CharField(max_length=50, blank=True, null=True)
    correo = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    titularidad = models.CharField(max_length=30, blank=True, null=True)
    activo = models.BooleanField()
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'docente'

    def __str__(self):
        return f'{self.apellidos} {self.nombres}'


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=255)
    id_rol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='id_rol')
    id_docente = models.ForeignKey(Docente, models.DO_NOTHING, db_column='id_docente', blank=True, null=True)
    id_facultad = models.ForeignKey(Facultad, models.DO_NOTHING, db_column='id_facultad', blank=True, null=True)
    nombres = models.CharField(max_length=200, blank=True, null=True)
    correo = models.CharField(max_length=150, blank=True, null=True)
    activo = models.BooleanField()
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'usuario'

    def __str__(self):
        return self.username


class Proyecto(models.Model):
    id_proyecto = models.AutoField(primary_key=True)
    codigo = models.CharField(unique=True, max_length=40)
    nombre = models.TextField()
    nombre_corto = models.CharField(max_length=300, blank=True, null=True)
    id_facultad = models.ForeignKey(Facultad, models.DO_NOTHING, db_column='id_facultad')
    id_carrera = models.ForeignKey(Carrera, models.DO_NOTHING, db_column='id_carrera')
    id_periodo_inicio = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo_inicio')
    id_periodo_fin = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo_fin', related_name='proyecto_fin_set', blank=True, null=True)
    programa = models.CharField(max_length=300, blank=True, null=True)
    linea_vinculacion = models.CharField(max_length=300, blank=True, null=True)
    area_conocimiento = models.CharField(max_length=200, blank=True, null=True)
    sub_area_conocimiento = models.CharField(max_length=200, blank=True, null=True)
    alcance = models.CharField(max_length=50, blank=True, null=True)
    objetivo_general = models.TextField(blank=True, null=True)
    objetivos_especificos = models.TextField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    presupuesto_planificado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=30)
    motivo_detencion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin_planificada = models.DateField(blank=True, null=True)
    fecha_fin_real = models.DateField(blank=True, null=True)
    ods = models.CharField(max_length=300, blank=True, null=True)
    provincia = models.CharField(max_length=80, blank=True, null=True)
    canton = models.CharField(max_length=80, blank=True, null=True)
    parroquia = models.CharField(max_length=100, blank=True, null=True)
    sector = models.CharField(max_length=200, blank=True, null=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'proyecto'

    def __str__(self):
        return self.nombre


class ProyectoUbicacion(models.Model):
    id_ubicacion = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_entidad = models.ForeignKey(EntidadCooperante, models.DO_NOTHING, db_column='id_entidad', blank=True, null=True)
    nombre_lugar = models.CharField(max_length=300, blank=True, null=True)
    provincia = models.CharField(max_length=80)
    canton = models.CharField(max_length=80, blank=True, null=True)
    parroquia = models.CharField(max_length=100, blank=True, null=True)
    sector = models.CharField(max_length=200, blank=True, null=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    es_principal = models.BooleanField()
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proyecto_ubicacion'


class TipoDocumento(models.Model):
    id_tipo_doc = models.AutoField(primary_key=True)
    codigo = models.CharField(unique=True, max_length=10)
    nombre = models.CharField(max_length=200)
    numero_carpeta = models.IntegerField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    obligatorio = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'tipo_documento'

    def __str__(self):
        return self.nombre


class DocumentoProyecto(models.Model):
    id_documento = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_tipo_doc = models.ForeignKey(TipoDocumento, models.DO_NOTHING, db_column='id_tipo_doc')
    id_periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo', blank=True, null=True)
    nombre_archivo = models.CharField(max_length=300)
    ruta_archivo = models.CharField(max_length=500)
    tamanio_kb = models.IntegerField(blank=True, null=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    subido_por = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='subido_por', blank=True, null=True)
    subido_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'documento_proyecto'


class Beneficiario(models.Model):
    id_beneficiario = models.AutoField(primary_key=True)
    cedula = models.CharField(max_length=13, blank=True, null=True)
    apellidos = models.CharField(max_length=150)
    nombres = models.CharField(max_length=150)
    genero = models.CharField(max_length=15, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.CharField(max_length=150, blank=True, null=True)
    direccion = models.CharField(max_length=300, blank=True, null=True)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'beneficiario'

    def __str__(self):
        return f'{self.apellidos} {self.nombres}'


class Estudiante(models.Model):
    id_estudiante = models.AutoField(primary_key=True)
    cedula = models.CharField(unique=True, max_length=13)
    apellidos = models.CharField(max_length=150)
    nombres = models.CharField(max_length=150)
    genero = models.CharField(max_length=15, blank=True, null=True)
    correo = models.CharField(max_length=150, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    id_carrera = models.ForeignKey(Carrera, models.DO_NOTHING, db_column='id_carrera', blank=True, null=True)
    activo = models.BooleanField()
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'estudiante'

    def __str__(self):
        return f'{self.apellidos} {self.nombres}'


class ProyectoDocente(models.Model):
    id_proyecto_docente = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_docente = models.ForeignKey(Docente, models.DO_NOTHING, db_column='id_docente')
    id_periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo')
    rol = models.CharField(max_length=30)
    dia_laborable = models.CharField(max_length=20, blank=True, null=True)
    horas_semana = models.IntegerField(blank=True, null=True)
    activo = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'proyecto_docente'


class ProyectoEstudiante(models.Model):
    id_proyecto_estudiante = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_estudiante = models.ForeignKey(Estudiante, models.DO_NOTHING, db_column='id_estudiante')
    id_periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo')
    id_entidad = models.ForeignKey(EntidadCooperante, models.DO_NOTHING, db_column='id_entidad', blank=True, null=True)
    horas_requeridas = models.IntegerField()
    horas_cumplidas = models.IntegerField(blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proyecto_estudiante'


class Convenio(models.Model):
    id_convenio = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_entidad = models.ForeignKey(EntidadCooperante, models.DO_NOTHING, db_column='id_entidad')
    id_periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo')
    numero_memorando = models.CharField(max_length=100, blank=True, null=True)
    fecha_firma = models.DateField(blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    duracion_anios = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    estudiantes_asignados = models.IntegerField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'convenio'


class InformeSemestral(models.Model):
    id_informe = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_docente = models.ForeignKey(Docente, models.DO_NOTHING, db_column='id_docente')
    id_periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo')
    tipo = models.CharField(max_length=20)
    actividades_planificadas = models.TextField(blank=True, null=True)
    actividades_cumplidas = models.TextField(blank=True, null=True)
    porcentaje_cumplimiento = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    resultados_obtenidos = models.TextField(blank=True, null=True)
    problemas_encontrados = models.TextField(blank=True, null=True)
    recomendaciones = models.TextField(blank=True, null=True)
    impacto_social = models.TextField(blank=True, null=True)
    impacto_economico = models.TextField(blank=True, null=True)
    fecha_presentacion = models.DateField(blank=True, null=True)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'informe_semestral'


class EvaluacionImpacto(models.Model):
    id_evaluacion = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo')
    total_encuestados = models.IntegerField(blank=True, null=True)
    p1_totalmente_acuerdo = models.IntegerField(blank=True, null=True)
    p1_acuerdo = models.IntegerField(blank=True, null=True)
    p1_desacuerdo = models.IntegerField(blank=True, null=True)
    p1_totalmente_desacuerdo = models.IntegerField(blank=True, null=True)
    promedio_general = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    nivel_satisfaccion = models.CharField(max_length=30, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_aplicacion = models.DateField(blank=True, null=True)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'evaluacion_impacto'


class FotoProyecto(models.Model):
    id_foto = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo', blank=True, null=True)
    ruta_foto = models.CharField(max_length=500)
    titulo = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    fecha_tomada = models.DateField(blank=True, null=True)
    subida_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'foto_proyecto'


class ActividadSemanal(models.Model):
    id_actividad = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo')
    id_entidad = models.ForeignKey(EntidadCooperante, models.DO_NOTHING, db_column='id_entidad', blank=True, null=True)
    numero_semana = models.IntegerField()
    nombre_lugar = models.CharField(max_length=300, blank=True, null=True)
    descripcion = models.TextField()
    fecha = models.DateField(blank=True, null=True)
    horas = models.IntegerField(blank=True, null=True)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'actividad_semanal'


class ProyectoBeneficiario(models.Model):
    id_proyecto_beneficiario = models.AutoField(primary_key=True)
    id_proyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='id_proyecto')
    id_beneficiario = models.ForeignKey(Beneficiario, models.DO_NOTHING, db_column='id_beneficiario')
    id_entidad = models.ForeignKey(EntidadCooperante, models.DO_NOTHING, db_column='id_entidad', blank=True, null=True)
    id_periodo = models.ForeignKey(PeriodoAcademico, models.DO_NOTHING, db_column='id_periodo')

    class Meta:
        managed = False
        db_table = 'proyecto_beneficiario'