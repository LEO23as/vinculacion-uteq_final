from rest_framework import serializers
from .models import (
    PeriodoAcademico, Facultad, Carrera, EntidadCooperante,
    TipoEntidad, Proyecto, Convenio, Docente, Usuario, Rol
)


class PeriodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoAcademico
        fields = ['id_periodo', 'codigo', 'nombre', 'tipo', 'fecha_inicio', 'fecha_fin', 'activo', 'creado_en']


class FacultadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facultad
        fields = ['id_facultad', 'codigo', 'nombre', 'nombre_corto', 'campus', 'fecha_desde', 'fecha_hasta', 'activo']


class CarreraSerializer(serializers.ModelSerializer):
    facultad_nombre = serializers.CharField(source='id_facultad.nombre', read_only=True)

    class Meta:
        model = Carrera
        fields = ['id_carrera', 'nombre', 'codigo', 'horas_vinculacion', 'area_conocimiento', 'activo', 'id_facultad', 'facultad_nombre']


class TipoEntidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEntidad
        fields = ['id_tipo', 'nombre', 'descripcion']


class EntidadSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source='id_tipo.nombre', read_only=True)

    class Meta:
        model = EntidadCooperante
        fields = [
            'id_entidad', 'nombre', 'nombre_corto', 'ruc', 'representante_legal',
            'cargo_representante', 'telefono', 'correo', 'pagina_web',
            'provincia', 'canton', 'parroquia', 'direccion',
            'latitud', 'longitud', 'activo', 'id_tipo', 'tipo_nombre', 'creado_en'
        ]


class ProyectoSerializer(serializers.ModelSerializer):
    facultad_nombre = serializers.CharField(source='id_facultad.nombre', read_only=True)
    carrera_nombre = serializers.CharField(source='id_carrera.nombre', read_only=True)
    periodo_inicio_nombre = serializers.CharField(source='id_periodo_inicio.nombre', read_only=True)

    class Meta:
        model = Proyecto
        fields = [
            'id_proyecto', 'codigo', 'nombre', 'nombre_corto',
            'facultad_nombre', 'carrera_nombre', 'periodo_inicio_nombre',
            'estado', 'provincia', 'canton', 'latitud', 'longitud',
            'fecha_inicio', 'fecha_fin_planificada', 'creado_en'
        ]


class ConvenioSerializer(serializers.ModelSerializer):
    proyecto_nombre = serializers.CharField(source='id_proyecto.nombre_corto', read_only=True)
    entidad_nombre = serializers.CharField(source='id_entidad.nombre', read_only=True)
    periodo_nombre = serializers.CharField(source='id_periodo.nombre', read_only=True)

    class Meta:
        model = Convenio
        fields = [
            'id_convenio', 'numero_memorando', 'estado',
            'fecha_firma', 'fecha_inicio', 'fecha_fin', 'duracion_anios',
            'estudiantes_asignados', 'observaciones', 'creado_en',
            'proyecto_nombre', 'entidad_nombre', 'periodo_nombre'
        ]


class DocenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Docente
        fields = ['id_docente', 'cedula', 'apellidos', 'nombres', 'titulo', 'correo', 'telefono', 'titularidad', 'activo']


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id_rol', 'nombre', 'descripcion']
