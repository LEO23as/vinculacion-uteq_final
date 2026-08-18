from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.db.models.functions import ExtractYear
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
import os
import uuid

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from vinculacion.models import (
    Usuario, PeriodoAcademico, Facultad, Carrera,
    EntidadCooperante, TipoEntidad, Proyecto, FotoProyecto,
    Convenio, AnexoConvenio, ProyectoDocente, ProyectoEstudiante,
    Docente, Rol, ProyectoUbicacion, DocumentoProyecto,
    ProyectoBeneficiario, InformeSemestral, EvaluacionImpacto, ActividadSemanal
)
from django.db import transaction
from vinculacion.serializers import (
    PeriodoSerializer, FacultadSerializer, CarreraSerializer,
    EntidadSerializer, TipoEntidadSerializer, ProyectoSerializer,
    ConvenioSerializer, DocenteSerializer, RolSerializer
)
from vinculacion.utils import verificar_password


def login_view(request):
    if request.session.get('usuario_id'):
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if not username or not password:
            messages.error(request, 'Ingrese usuario y contraseña.')
            return render(request, 'auth/login.html')
        try:
            usuario = Usuario.objects.get(username=username, activo=True)
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return render(request, 'auth/login.html')
        if not verificar_password(password, usuario.password):
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return render(request, 'auth/login.html')
        request.session['usuario_id'] = usuario.id_usuario
        request.session['usuario_nombre'] = usuario.nombres or username
        request.session['usuario_rol'] = usuario.id_rol.nombre
        usuario.ultimo_acceso = timezone.now()
        usuario.save(update_fields=['ultimo_acceso'])
        if usuario.debe_cambiar_clave:
            return redirect('cambiar_clave')
        return redirect('dashboard')
    return render(request, 'auth/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')


def cambiar_clave_view(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    try:
        usuario = Usuario.objects.get(id_usuario=usuario_id)
    except Usuario.DoesNotExist:
        request.session.flush()
        return redirect('login')
    if not usuario.debe_cambiar_clave:
        return redirect('dashboard')
    if request.method == 'POST':
        nueva = request.POST.get('nueva_clave', '')
        confirmar = request.POST.get('confirmar_clave', '')
        if len(nueva) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return render(request, 'auth/cambiar_clave.html')
        if not any(c.isupper() for c in nueva):
            messages.error(request, 'Debe tener al menos una mayúscula.')
            return render(request, 'auth/cambiar_clave.html')
        if not any(c.isdigit() for c in nueva):
            messages.error(request, 'Debe tener al menos un número.')
            return render(request, 'auth/cambiar_clave.html')
        if nueva != confirmar:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'auth/cambiar_clave.html')
        from vinculacion.utils import hashear_password
        usuario.password = hashear_password(nueva)
        usuario.debe_cambiar_clave = False
        usuario.save(update_fields=['password', 'debe_cambiar_clave'])
        messages.success(request, 'Contraseña actualizada correctamente.')
        return redirect('dashboard')
    return render(request, 'auth/cambiar_clave.html')


def dashboard_view(request):
    ctx = {
        'usuario_nombre': request.session.get('usuario_nombre'),
        'usuario_rol': request.session.get('usuario_rol'),
    }
    try:
        from vinculacion.models import Proyecto, EntidadCooperante, Convenio, ProyectoDocente
        ctx['total_proyectos'] = Proyecto.objects.count()
        ctx['total_entidades'] = EntidadCooperante.objects.filter(activo=True).count()
        ctx['total_convenios'] = Convenio.objects.count()
        ctx['total_docentes'] = ProyectoDocente.objects.values('docente').distinct().count()
    except Exception:
        pass
    return render(request, 'dashboard.html', ctx)


# ── PERIODOS ACADÉMICOS ────────────────────────────────────────────

def periodos_lista(request):
    periodos = PeriodoAcademico.objects.all().order_by('-fecha_inicio')
    return render(request, 'periodos/lista.html', {
        'periodos': periodos,
        'titulo_modulo': 'Periodos Académicos',
    })


def periodo_nuevo(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        tipo = request.POST.get('tipo', '').strip()
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        activo = request.POST.get('activo') == 'on'

        if not codigo or not nombre or not tipo or not fecha_inicio or not fecha_fin:
            messages.error(request, 'Todos los campos obligatorios deben completarse.')
            return render(request, 'periodos/form.html', {'accion': 'Nuevo', 'data': request.POST})

        if PeriodoAcademico.objects.filter(codigo=codigo).exists():
            messages.error(request, f'Ya existe un periodo con el código {codigo}.')
            return render(request, 'periodos/form.html', {'accion': 'Nuevo', 'data': request.POST})

        try:
            usuario_id = request.session.get('usuario_id')
            usuario = Usuario.objects.get(id_usuario=usuario_id)
            PeriodoAcademico.objects.create(
                codigo=codigo,
                nombre=nombre,
                tipo=tipo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                activo=activo,
                creado_por=usuario,
                creado_en=timezone.now(),
            )
            messages.success(request, f'Periodo "{nombre}" creado correctamente.')
            return redirect('periodos_lista')
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')

    return render(request, 'periodos/form.html', {'accion': 'Nuevo', 'data': {}})


def periodo_editar(request, id):
    periodo = get_object_or_404(PeriodoAcademico, id_periodo=id)
    if request.method == 'POST':
        periodo.codigo = request.POST.get('codigo', '').strip()
        periodo.nombre = request.POST.get('nombre', '').strip()
        periodo.tipo = request.POST.get('tipo', '').strip()
        periodo.fecha_inicio = request.POST.get('fecha_inicio')
        periodo.fecha_fin = request.POST.get('fecha_fin')
        periodo.activo = request.POST.get('activo') == 'on'
        try:
            periodo.save()
            messages.success(request, f'Periodo "{periodo.nombre}" actualizado.')
            return redirect('periodos_lista')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')
    return render(request, 'periodos/form.html', {
        'accion': 'Editar',
        'data': periodo,
        'editar': True,
        'periodo': periodo,
    })


def periodo_toggle(request, id):
    periodo = get_object_or_404(PeriodoAcademico, id_periodo=id)
    periodo.activo = not periodo.activo
    periodo.save(update_fields=['activo'])
    estado = 'activado' if periodo.activo else 'desactivado'
    messages.success(request, f'Periodo "{periodo.nombre}" {estado}.')
    return redirect('periodos_lista')


# ── FACULTADES Y CARRERAS ──────────────────────────────────────────

def facultades_lista(request):
    facultades = Facultad.objects.all().order_by('nombre')
    return render(request, 'facultades/lista.html', {
        'facultades': facultades,
    })


def facultad_editar(request, id):
    facultad = get_object_or_404(Facultad, id_facultad=id)
    if request.method == 'POST':
        facultad.nombre = request.POST.get('nombre', '').strip()
        facultad.nombre_corto = request.POST.get('nombre_corto', '').strip()
        facultad.codigo = request.POST.get('codigo', '').strip()
        facultad.campus = request.POST.get('campus', '').strip()
        try:
            facultad.save()
            messages.success(request, f'Facultad "{facultad.nombre}" actualizada.')
            return redirect('facultades_lista')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'facultades/form.html', {
        'facultad': facultad,
        'accion': 'Editar',
    })


def facultad_toggle(request, id):
    facultad = get_object_or_404(Facultad, id_facultad=id)
    facultad.activo = not facultad.activo
    facultad.save(update_fields=['activo'])
    estado = 'activada' if facultad.activo else 'desactivada'
    messages.success(request, f'Facultad "{facultad.nombre}" {estado}.')
    return redirect('facultades_lista')


def carreras_lista(request):
    carreras = Carrera.objects.select_related('id_facultad').all().order_by('id_facultad__nombre', 'nombre')
    facultades = Facultad.objects.filter(activo=True).order_by('nombre')
    return render(request, 'facultades/carreras_lista.html', {
        'carreras': carreras,
        'facultades': facultades,
    })


def carrera_nueva(request):
    facultades = Facultad.objects.filter(activo=True).order_by('nombre')
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip()
        id_facultad = request.POST.get('id_facultad')
        horas_vinculacion = request.POST.get('horas_vinculacion', 0)
        area_conocimiento = request.POST.get('area_conocimiento', '').strip()
        activo = request.POST.get('activo') == 'on'

        if not nombre or not id_facultad:
            messages.error(request, 'Nombre y facultad son obligatorios.')
            return render(request, 'facultades/carrera_form.html', {
                'facultades': facultades, 'data': request.POST
            })
        try:
            facultad = Facultad.objects.get(id_facultad=id_facultad)
            Carrera.objects.create(
                nombre=nombre,
                codigo=codigo,
                id_facultad=facultad,
                horas_vinculacion=horas_vinculacion or 0,
                area_conocimiento=area_conocimiento,
                activo=activo,
                creado_en=timezone.now(),
            )
            messages.success(request, f'Carrera "{nombre}" creada correctamente.')
            return redirect('carreras_lista')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'facultades/carrera_form.html', {
        'facultades': facultades, 'data': {}, 'accion': 'Nueva'
    })


def carrera_editar(request, id):
    carrera = get_object_or_404(Carrera, id_carrera=id)
    facultades = Facultad.objects.filter(activo=True).order_by('nombre')
    if request.method == 'POST':
        carrera.nombre = request.POST.get('nombre', '').strip()
        carrera.codigo = request.POST.get('codigo', '').strip()
        carrera.id_facultad = get_object_or_404(Facultad, id_facultad=request.POST.get('id_facultad'))
        carrera.horas_vinculacion = request.POST.get('horas_vinculacion', 0) or 0
        carrera.area_conocimiento = request.POST.get('area_conocimiento', '').strip()
        carrera.activo = request.POST.get('activo') == 'on'
        try:
            carrera.save()
            messages.success(request, f'Carrera "{carrera.nombre}" actualizada.')
            return redirect('carreras_lista')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'facultades/carrera_form.html', {
        'facultades': facultades,
        'carrera': carrera,
        'accion': 'Editar',
        'editar': True,
    })


def carrera_toggle(request, id):
    carrera = get_object_or_404(Carrera, id_carrera=id)
    carrera.activo = not carrera.activo
    carrera.save(update_fields=['activo'])
    estado = 'activada' if carrera.activo else 'desactivada'
    messages.success(request, f'Carrera "{carrera.nombre}" {estado}.')
    return redirect('carreras_lista')


def carrera_por_facultad(request):
    id_facultad = request.GET.get('facultad_id')
    carreras = Carrera.objects.filter(
        id_facultad=id_facultad, activo=True
    ).order_by('nombre').values('id_carrera', 'nombre')
    return JsonResponse(list(carreras), safe=False)


# ── ENTIDADES COOPERANTES ──────────────────────────────────────────

def entidades_lista(request):
    entidades = EntidadCooperante.objects.select_related('id_tipo').all().order_by('nombre')
    tipos = TipoEntidad.objects.all().order_by('nombre')

    filtro_tipo = request.GET.get('tipo', '')
    filtro_estado = request.GET.get('estado', '')
    busqueda = request.GET.get('q', '')

    if filtro_tipo:
        entidades = entidades.filter(id_tipo__id_tipo=filtro_tipo)
    if filtro_estado == '1':
        entidades = entidades.filter(activo=True)
    elif filtro_estado == '0':
        entidades = entidades.filter(activo=False)
    if busqueda:
        entidades = entidades.filter(nombre__icontains=busqueda)

    return render(request, 'entidades/lista.html', {
        'entidades': entidades,
        'tipos': tipos,
        'filtro_tipo': filtro_tipo,
        'filtro_estado': filtro_estado,
        'busqueda': busqueda,
    })


def entidad_nueva(request):
    tipos = TipoEntidad.objects.all().order_by('nombre')
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        id_tipo = request.POST.get('id_tipo')
        if not nombre or not id_tipo:
            messages.error(request, 'Nombre y tipo son obligatorios.')
            return render(request, 'entidades/form.html', {
                'tipos': tipos, 'data': request.POST, 'accion': 'Nueva'
            })
        ruc = request.POST.get('ruc', '').strip() or None
        if ruc and EntidadCooperante.objects.filter(ruc=ruc).exists():
            messages.error(request, f'Ya existe una entidad con el RUC {ruc}.')
            return render(request, 'entidades/form.html', {
                'tipos': tipos, 'data': request.POST, 'accion': 'Nueva'
            })
        try:
            tipo = TipoEntidad.objects.get(id_tipo=id_tipo)
            EntidadCooperante.objects.create(
                nombre=nombre,
                nombre_corto=request.POST.get('nombre_corto', '').strip() or None,
                id_tipo=tipo,
                ruc=ruc,
                representante_legal=request.POST.get('representante_legal', '').strip() or None,
                cargo_representante=request.POST.get('cargo_representante', '').strip() or None,
                telefono=request.POST.get('telefono', '').strip() or None,
                correo=request.POST.get('correo', '').strip() or None,
                pagina_web=request.POST.get('pagina_web', '').strip() or None,
                provincia=request.POST.get('provincia', '').strip() or None,
                canton=request.POST.get('canton', '').strip() or None,
                parroquia=request.POST.get('parroquia', '').strip() or None,
                sector=request.POST.get('sector', '').strip() or None,
                direccion=request.POST.get('direccion', '').strip() or None,
                observaciones=request.POST.get('observaciones', '').strip() or None,
                activo=request.POST.get('activo') == 'on',
                creado_en=timezone.now(),
            )
            messages.success(request, f'Entidad "{nombre}" creada correctamente.')
            return redirect('entidades_lista')
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')
    return render(request, 'entidades/form.html', {
        'tipos': tipos, 'data': {}, 'accion': 'Nueva'
    })


def entidad_editar(request, id):
    entidad = get_object_or_404(EntidadCooperante, id_entidad=id)
    tipos = TipoEntidad.objects.all().order_by('nombre')
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        id_tipo = request.POST.get('id_tipo')
        if not nombre or not id_tipo:
            messages.error(request, 'Nombre y tipo son obligatorios.')
            return render(request, 'entidades/form.html', {
                'tipos': tipos, 'data': request.POST,
                'accion': 'Editar', 'entidad': entidad, 'editar': True
            })
        ruc = request.POST.get('ruc', '').strip() or None
        if ruc and EntidadCooperante.objects.filter(ruc=ruc).exclude(id_entidad=id).exists():
            messages.error(request, f'Ya existe otra entidad con el RUC {ruc}.')
            return render(request, 'entidades/form.html', {
                'tipos': tipos, 'data': request.POST,
                'accion': 'Editar', 'entidad': entidad, 'editar': True
            })
        try:
            entidad.nombre = nombre
            entidad.nombre_corto = request.POST.get('nombre_corto', '').strip() or None
            entidad.id_tipo = TipoEntidad.objects.get(id_tipo=id_tipo)
            entidad.ruc = ruc
            entidad.representante_legal = request.POST.get('representante_legal', '').strip() or None
            entidad.cargo_representante = request.POST.get('cargo_representante', '').strip() or None
            entidad.telefono = request.POST.get('telefono', '').strip() or None
            entidad.correo = request.POST.get('correo', '').strip() or None
            entidad.pagina_web = request.POST.get('pagina_web', '').strip() or None
            entidad.provincia = request.POST.get('provincia', '').strip() or None
            entidad.canton = request.POST.get('canton', '').strip() or None
            entidad.parroquia = request.POST.get('parroquia', '').strip() or None
            entidad.sector = request.POST.get('sector', '').strip() or None
            entidad.direccion = request.POST.get('direccion', '').strip() or None
            entidad.observaciones = request.POST.get('observaciones', '').strip() or None
            entidad.activo = request.POST.get('activo') == 'on'
            entidad.save()
            messages.success(request, f'Entidad "{entidad.nombre}" actualizada.')
            return redirect('entidades_lista')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')
    return render(request, 'entidades/form.html', {
        'tipos': tipos,
        'entidad': entidad,
        'accion': 'Editar',
        'editar': True,
    })


def entidad_toggle(request, id):
    entidad = get_object_or_404(EntidadCooperante, id_entidad=id)
    entidad.activo = not entidad.activo
    entidad.save(update_fields=['activo'])
    estado = 'activada' if entidad.activo else 'desactivada'
    messages.success(request, f'Entidad "{entidad.nombre}" {estado}.')
    return redirect('entidades_lista')


# ── PROYECTOS ──────────────────────────────────────────────────────

ESTADOS_PROYECTO = ['EN_EJECUCION', 'PROPUESTO', 'APROBADO', 'EN_CIERRE', 'DETENIDO', 'FINALIZADO', 'RECHAZADO']


def proyectos_lista(request):
    proyectos = Proyecto.objects.select_related(
        'id_facultad', 'id_carrera', 'id_periodo_inicio'
    ).all().order_by('-creado_en')

    filtro_estado = request.GET.get('estado', '')
    filtro_facultad = request.GET.get('facultad', '')
    busqueda = request.GET.get('q', '')

    if filtro_estado:
        proyectos = proyectos.filter(estado=filtro_estado)
    if filtro_facultad:
        proyectos = proyectos.filter(id_facultad__id_facultad=filtro_facultad)
    if busqueda:
        proyectos = proyectos.filter(
            Q(nombre__icontains=busqueda) | Q(codigo__icontains=busqueda)
        )

    facultades = Facultad.objects.filter(activo=True).order_by('nombre')

    return render(request, 'proyectos/lista.html', {
        'proyectos': proyectos,
        'facultades': facultades,
        'estados': ESTADOS_PROYECTO,
        'filtro_estado': filtro_estado,
        'filtro_facultad': filtro_facultad,
        'busqueda': busqueda,
    })


def _error_amigable(e):
    """Traduce errores técnicos de la BD a mensajes claros en español."""
    s = str(e)
    if 'chk_fechas_proyecto' in s:
        return 'La fecha de finalización debe ser posterior a la fecha de inicio.'
    if 'proyecto_estado_check' in s:
        return 'El estado del proyecto no es válido.'
    if 'proyecto_alcance_check' in s:
        return 'El alcance del proyecto no es válido.'
    if 'duplicate key' in s and 'codigo' in s:
        return 'Ya existe un proyecto con ese código.'
    return s


EXTENSIONES_IMAGEN = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
EXTENSIONES_DOCUMENTO = EXTENSIONES_IMAGEN | {'.pdf'}
TAMANIO_MAX_MB = 10


def _validar_archivo(archivo, extensiones_permitidas):
    """Valida tamaño y extensión de un archivo subido. Devuelve un mensaje de error o None si es válido."""
    ext = os.path.splitext(archivo.name)[1].lower()
    if ext not in extensiones_permitidas:
        permitidas = ', '.join(sorted(extensiones_permitidas))
        return f'Formato no permitido para "{archivo.name}". Formatos aceptados: {permitidas}.'
    if archivo.size > TAMANIO_MAX_MB * 1024 * 1024:
        return f'El archivo "{archivo.name}" supera el tamaño máximo permitido ({TAMANIO_MAX_MB}MB).'
    return None


def _guardar_fotos(request, proyecto):
    fotos = request.FILES.getlist('fotos')
    for foto in fotos:
        error = _validar_archivo(foto, EXTENSIONES_IMAGEN)
        if error:
            raise ValueError(error)
        carpeta = f'proyectos/{proyecto.id_proyecto}/'
        ruta_completa = os.path.join(settings.MEDIA_ROOT, carpeta)
        os.makedirs(ruta_completa, exist_ok=True)
        nombre_archivo = foto.name
        ruta_final = os.path.join(ruta_completa, nombre_archivo)
        with open(ruta_final, 'wb+') as f:
            for chunk in foto.chunks():
                f.write(chunk)
        FotoProyecto.objects.create(
            id_proyecto=proyecto,
            ruta_foto=f'{carpeta}{nombre_archivo}',
            titulo=nombre_archivo,
            subida_en=timezone.now(),
        )


def _guardar_ubicaciones(request, proyecto, reemplazar=False):
    """
    Crea filas ProyectoUbicacion desde el JSON 'ubicaciones' del request.
    Cada ubicación: {nombre_lugar, provincia, canton, parroquia, sector,
                     latitud, longitud, es_principal}.
    Devuelve la ubicación principal (o None) para reflejarla en el proyecto.
    """
    raw = request.POST.get('ubicaciones')
    if not raw:
        return None
    try:
        lista = json.loads(raw)
    except Exception:
        return None
    if not isinstance(lista, list) or not lista:
        return None

    if reemplazar:
        ProyectoUbicacion.objects.filter(id_proyecto=proyecto).delete()

    principal = None
    hay_principal = any(u.get('es_principal') for u in lista)
    for i, u in enumerate(lista):
        lat = str(u.get('latitud') or '').strip() or None
        lng = str(u.get('longitud') or '').strip() or None
        if lat is None or lng is None:
            continue
        es_principal = bool(u.get('es_principal')) or (not hay_principal and i == 0)
        ubic = ProyectoUbicacion.objects.create(
            id_proyecto=proyecto,
            nombre_lugar=(u.get('nombre_lugar') or '').strip() or None,
            provincia=(u.get('provincia') or '').strip() or 'N/D',
            canton=(u.get('canton') or '').strip() or None,
            parroquia=(u.get('parroquia') or '').strip() or None,
            sector=(u.get('sector') or '').strip() or None,
            latitud=lat,
            longitud=lng,
            es_principal=es_principal,
        )
        if es_principal:
            principal = ubic
    return principal


def proyecto_nuevo(request):
    facultades = Facultad.objects.filter(activo=True).order_by('nombre')
    periodos = PeriodoAcademico.objects.filter(activo=True).order_by('-fecha_inicio')
    entidades = EntidadCooperante.objects.filter(activo=True).order_by('nombre')

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        id_facultad = request.POST.get('id_facultad')
        id_carrera = request.POST.get('id_carrera')
        id_periodo_inicio = request.POST.get('id_periodo_inicio')
        estado = request.POST.get('estado', 'EN_EJECUCION')

        if not codigo or not nombre or not id_facultad or not id_carrera or not id_periodo_inicio:
            messages.error(request, 'Código, nombre, facultad, carrera y periodo son obligatorios.')
            carreras = Carrera.objects.filter(id_facultad=id_facultad, activo=True) if id_facultad else []
            return render(request, 'proyectos/form.html', {
                'facultades': facultades, 'periodos': periodos,
                'entidades': entidades, 'carreras': carreras,
                'estados': ESTADOS_PROYECTO, 'data': request.POST, 'accion': 'Nuevo'
            })

        if Proyecto.objects.filter(codigo=codigo).exists():
            messages.error(request, f'Ya existe un proyecto con el código {codigo}.')
            carreras = Carrera.objects.filter(id_facultad=id_facultad, activo=True)
            return render(request, 'proyectos/form.html', {
                'facultades': facultades, 'periodos': periodos,
                'entidades': entidades, 'carreras': carreras,
                'estados': ESTADOS_PROYECTO, 'data': request.POST, 'accion': 'Nuevo'
            })

        try:
            lat = request.POST.get('latitud', '').strip() or None
            lng = request.POST.get('longitud', '').strip() or None
            proyecto = Proyecto.objects.create(
                codigo=codigo,
                nombre=nombre,
                nombre_corto=request.POST.get('nombre_corto', '').strip() or None,
                id_facultad=Facultad.objects.get(id_facultad=id_facultad),
                id_carrera=Carrera.objects.get(id_carrera=id_carrera),
                id_periodo_inicio=PeriodoAcademico.objects.get(id_periodo=id_periodo_inicio),
                estado=estado,
                provincia=request.POST.get('provincia', '').strip() or None,
                canton=request.POST.get('canton', '').strip() or None,
                parroquia=request.POST.get('parroquia', '').strip() or None,
                sector=request.POST.get('sector', '').strip() or None,
                descripcion=request.POST.get('descripcion', '').strip() or None,
                observaciones=request.POST.get('observaciones', '').strip() or None,
                latitud=lat,
                longitud=lng,
                creado_en=timezone.now(),
                actualizado_en=timezone.now(),
            )
            _guardar_fotos(request, proyecto)
            messages.success(request, f'Proyecto "{nombre}" creado correctamente.')
            return redirect('proyectos_lista')
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')

    return render(request, 'proyectos/form.html', {
        'facultades': facultades, 'periodos': periodos,
        'entidades': entidades, 'carreras': [],
        'estados': ESTADOS_PROYECTO, 'data': {}, 'accion': 'Nuevo'
    })


def proyecto_editar(request, id):
    proyecto = get_object_or_404(Proyecto, id_proyecto=id)
    facultades = Facultad.objects.filter(activo=True).order_by('nombre')
    periodos = PeriodoAcademico.objects.filter(activo=True).order_by('-fecha_inicio')
    entidades = EntidadCooperante.objects.filter(activo=True).order_by('nombre')
    carreras = Carrera.objects.filter(id_facultad=proyecto.id_facultad, activo=True).order_by('nombre')
    fotos = FotoProyecto.objects.filter(id_proyecto=proyecto).order_by('subida_en')

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        id_facultad = request.POST.get('id_facultad')
        id_carrera = request.POST.get('id_carrera')
        id_periodo_inicio = request.POST.get('id_periodo_inicio')

        if not codigo or not nombre or not id_facultad or not id_carrera or not id_periodo_inicio:
            messages.error(request, 'Todos los campos obligatorios deben completarse.')
            return render(request, 'proyectos/form.html', {
                'facultades': facultades, 'periodos': periodos,
                'entidades': entidades, 'carreras': carreras,
                'estados': ESTADOS_PROYECTO, 'data': request.POST,
                'accion': 'Editar', 'proyecto': proyecto,
                'editar': True, 'fotos': fotos,
            })

        if Proyecto.objects.filter(codigo=codigo).exclude(id_proyecto=id).exists():
            messages.error(request, f'Ya existe otro proyecto con el código {codigo}.')
            return render(request, 'proyectos/form.html', {
                'facultades': facultades, 'periodos': periodos,
                'entidades': entidades, 'carreras': carreras,
                'estados': ESTADOS_PROYECTO, 'data': request.POST,
                'accion': 'Editar', 'proyecto': proyecto,
                'editar': True, 'fotos': fotos,
            })

        try:
            lat = request.POST.get('latitud', '').strip() or None
            lng = request.POST.get('longitud', '').strip() or None
            proyecto.codigo = codigo
            proyecto.nombre = nombre
            proyecto.nombre_corto = request.POST.get('nombre_corto', '').strip() or None
            proyecto.id_facultad = Facultad.objects.get(id_facultad=id_facultad)
            proyecto.id_carrera = Carrera.objects.get(id_carrera=id_carrera)
            proyecto.id_periodo_inicio = PeriodoAcademico.objects.get(id_periodo=id_periodo_inicio)
            proyecto.estado = request.POST.get('estado', proyecto.estado)
            proyecto.provincia = request.POST.get('provincia', '').strip() or None
            proyecto.canton = request.POST.get('canton', '').strip() or None
            proyecto.parroquia = request.POST.get('parroquia', '').strip() or None
            proyecto.sector = request.POST.get('sector', '').strip() or None
            proyecto.descripcion = request.POST.get('descripcion', '').strip() or None
            proyecto.observaciones = request.POST.get('observaciones', '').strip() or None
            proyecto.latitud = lat
            proyecto.longitud = lng
            proyecto.actualizado_en = timezone.now()
            proyecto.save()
            _guardar_fotos(request, proyecto)
            messages.success(request, f'Proyecto "{proyecto.nombre}" actualizado.')
            return redirect('proyectos_lista')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')

    return render(request, 'proyectos/form.html', {
        'facultades': facultades, 'periodos': periodos,
        'entidades': entidades, 'carreras': carreras,
        'estados': ESTADOS_PROYECTO,
        'proyecto': proyecto, 'accion': 'Editar',
        'editar': True, 'fotos': fotos,
    })


def proyecto_eliminar_foto(request, foto_id):
    foto = get_object_or_404(FotoProyecto, id_foto=foto_id)
    proyecto_id = foto.id_proyecto.id_proyecto
    ruta = os.path.join(settings.MEDIA_ROOT, foto.ruta_foto)
    if os.path.exists(ruta):
        os.remove(ruta)
    foto.delete()
    messages.success(request, 'Foto eliminada.')
    return redirect('proyecto_editar', id=proyecto_id)


def proyecto_toggle(request, id):
    proyecto = get_object_or_404(Proyecto, id_proyecto=id)
    if proyecto.estado == 'FINALIZADO':
        proyecto.estado = 'EN_EJECUCION'
        msg = f'Proyecto "{proyecto.nombre}" reactivado.'
    else:
        proyecto.estado = 'FINALIZADO'
        msg = f'Proyecto "{proyecto.nombre}" marcado como finalizado.'
    proyecto.actualizado_en = timezone.now()
    proyecto.save(update_fields=['estado', 'actualizado_en'])
    messages.success(request, msg)
    return redirect('proyectos_lista')


# ── MAPA ──────────────────────────────────────────────────────────

def mapa_view(request):
    facultades = Facultad.objects.filter(activo=True).order_by('nombre')
    periodos = PeriodoAcademico.objects.all().order_by('-fecha_inicio')
    carreras = Carrera.objects.filter(activo=True).order_by('nombre')

    return render(request, 'mapa/mapa.html', {
        'facultades': facultades,
        'periodos': periodos,
        'carreras': carreras,
        'usuario_nombre': request.session.get('usuario_nombre'),
        'usuario_rol': request.session.get('usuario_rol'),
    })


def api_capa_pobreza(request):
    """
    Devuelve el indicador NBI por canton (por defecto Censo 2022, INEC).
    Los datos viven en la tabla public.capa_indicador_canton — la geometria
    se sirve como archivo estatico en /static/geo/cantones_ec.geojson y se
    une por dpa_canton.

    Query params opcionales:
        ?tipo=NBI   (default NBI)
        ?anio=2022  (default 2022)
    """
    from .models import CapaIndicadorCanton
    tipo = request.GET.get("tipo", "NBI")
    anio = int(request.GET.get("anio", 2022))
    qs = (CapaIndicadorCanton.objects
          .filter(tipo_indicador=tipo, anio=anio)
          .values("dpa_canton", "provincia", "canton", "valor"))
    data = {
        r["dpa_canton"]: {
            "canton": r["canton"],
            "provincia": r["provincia"],
            "nbi_pct": float(r["valor"]),
        }
        for r in qs
    }
    return JsonResponse(data)


def api_inec_sectores(request):
    """
    Proxy a la capa de sectores censales del INEC (ArcGIS/MapServer).
    Evita CORS y da errores manejables al frontend.
    Query params esperados: bbox=west,south,east,north  (EPSG:4326)
    """
    import urllib.parse
    import urllib.request
    import ssl

    bbox = request.GET.get('bbox', '').strip()
    if not bbox or bbox.count(',') != 3:
        return JsonResponse({'error': 'bbox requerido: west,south,east,north'}, status=400)

    params = {
        'geometry': bbox,
        'geometryType': 'esriGeometryEnvelope',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'sec,parroquia',
        'returnGeometry': 'true',
        'f': 'geojson',
    }
    url = (
        'https://idgn.ecuadorencifras.gob.ec/server/rest/services/'
        'WMS_MGN2025/MapServer/1/query?' + urllib.parse.urlencode(params)
    )

    try:
        ctx = ssl.create_default_context()
        # Algunos servidores oficiales tienen la cadena SSL incompleta.
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': 'UTEQ-Vinculacion/1.0'})
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            data = resp.read()
        return JsonResponse(json.loads(data.decode('utf-8')), safe=False)
    except Exception as e:
        return JsonResponse(
            {'error': 'No se pudo consultar el servicio INEC', 'detail': str(e)},
            status=502,
        )


def api_mapa_proyectos(request):
    qs = Proyecto.objects.select_related(
        'id_facultad', 'id_carrera', 'id_periodo_inicio'
    ).prefetch_related('fotoproyecto_set').filter(
        latitud__isnull=False,
        longitud__isnull=False,
    )

    facultad_id = request.GET.get('facultad')
    carrera_id = request.GET.get('carrera')
    periodo_id = request.GET.get('periodo')
    estado = request.GET.get('estado')
    anio = request.GET.get('anio')
    buscar = request.GET.get('buscar', '').strip()

    if facultad_id:
        qs = qs.filter(id_facultad_id=facultad_id)
    if carrera_id:
        qs = qs.filter(id_carrera_id=carrera_id)
    if periodo_id:
        qs = qs.filter(id_periodo_inicio_id=periodo_id)
    if estado:
        qs = qs.filter(estado=estado)
    if anio:
        qs = qs.filter(fecha_inicio__year=anio)
    if buscar:
        qs = qs.filter(Q(nombre__icontains=buscar) | Q(codigo__icontains=buscar))

    COLORES = {
        'EN_EJECUCION': '#1b7505',
        'PROPUESTO':    '#dba112',
        'APROBADO':     '#0d6efd',
        'EN_CIERRE':    '#fd7e14',
        'DETENIDO':     '#dc3545',
        'FINALIZADO':   '#a8a8a7',
        'RECHAZADO':    '#6c757d',
    }

    features = []
    for p in qs:
        fotos = ['/media/' + str(f.ruta_foto) for f in p.fotoproyecto_set.all()]
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [float(p.longitud), float(p.latitud)],
            },
            'properties': {
                'id':                       p.id_proyecto,
                'codigo':                   p.codigo,
                'nombre':                   p.nombre,
                'nombre_corto':             p.nombre_corto or p.nombre[:60],
                'facultad':                 p.id_facultad.nombre,
                'carrera':                  p.id_carrera.nombre,
                'periodo':                  p.id_periodo_inicio.nombre,
                'periodo_fin':              p.id_periodo_fin.nombre if p.id_periodo_fin else '',
                'estado':                   p.estado,
                'color':                    COLORES.get(p.estado, '#1b7505'),
                'programa':                 p.programa or '',
                'linea_vinculacion':        p.linea_vinculacion or '',
                'area_conocimiento':        p.area_conocimiento or '',
                'sub_area_conocimiento':    p.sub_area_conocimiento or '',
                'alcance':                  p.alcance or '',
                'objetivo_general':         p.objetivo_general or '',
                'objetivos_especificos':    p.objetivos_especificos or '',
                'descripcion':              p.descripcion or '',
                'director_nombre':          p.director_nombre or '',
                'director_correo':          p.director_correo or '',
                'resolucion_aprobacion':    p.resolucion_aprobacion or '',
                'fecha_aprobacion':         str(p.fecha_aprobacion) if p.fecha_aprobacion else '',
                'presupuesto_planificado':  float(p.presupuesto_planificado) if p.presupuesto_planificado else None,
                'provincia':                p.provincia or '',
                'canton':                   p.canton or '',
                'parroquia':                p.parroquia or '',
                'sector':                   p.sector or '',
                'fecha_inicio':             str(p.fecha_inicio) if p.fecha_inicio else '',
                'fecha_fin_planificada':    str(p.fecha_fin_planificada) if p.fecha_fin_planificada else '',
                'fecha_fin_real':           str(p.fecha_fin_real) if p.fecha_fin_real else '',
                'ods':                      p.ods or '',
                'observaciones':            p.observaciones or '',
                'motivo_detencion':         p.motivo_detencion or '',
                'fotos':                    fotos,
                'foto_url':                 fotos[0] if fotos else None,  # compat
                'url_editar':               f'/proyectos/{p.id_proyecto}/editar/',
                'url_detalle':              f'/proyectos/{p.id_proyecto}/',
            }
        })

    return JsonResponse({'type': 'FeatureCollection', 'features': features})


def api_mapa_anios(request):
    anios = (
        Proyecto.objects
        .filter(latitud__isnull=False, fecha_inicio__isnull=False)
        .annotate(anio=ExtractYear('fecha_inicio'))
        .values_list('anio', flat=True)
        .distinct()
        .order_by('-anio')
    )
    return JsonResponse({'anios': list(anios)})


# ── CONVENIOS ──────────────────────────────────────────────────────

def convenios_lista(request):
    if not request.session.get('usuario_id'):
        return redirect('login')

    query = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    id_periodo = request.GET.get('periodo', '')

    convenios = Convenio.objects.select_related(
        'id_proyecto', 'id_entidad', 'id_periodo'
    ).order_by('-creado_en')

    if query:
        convenios = convenios.filter(
            Q(numero_memorando__icontains=query) |
            Q(id_entidad__nombre__icontains=query) |
            Q(id_proyecto__nombre__icontains=query)
        )
    if estado:
        convenios = convenios.filter(estado=estado)
    if id_periodo:
        convenios = convenios.filter(id_periodo=id_periodo)

    periodos = PeriodoAcademico.objects.order_by('-fecha_inicio')

    return render(request, 'convenios/lista.html', {
        'convenios': convenios,
        'periodos': periodos,
        'query': query,
        'estado_filtro': estado,
        'periodo_filtro': id_periodo,
        'estados': ['VIGENTE', 'VENCIDO', 'RENOVADO', 'CANCELADO'],
    })


def convenio_crear(request):
    if not request.session.get('usuario_id'):
        return redirect('login')

    if request.method == 'POST':
        try:
            convenio = Convenio(
                id_proyecto=Proyecto.objects.get(pk=request.POST['id_proyecto']),
                id_entidad=EntidadCooperante.objects.get(pk=request.POST['id_entidad']),
                id_periodo=PeriodoAcademico.objects.get(pk=request.POST['id_periodo']),
                numero_memorando=request.POST.get('numero_memorando') or None,
                fecha_firma=request.POST.get('fecha_firma') or None,
                fecha_inicio=request.POST.get('fecha_inicio') or None,
                fecha_fin=request.POST.get('fecha_fin') or None,
                duracion_anios=request.POST.get('duracion_anios') or 2,
                estado=request.POST.get('estado', 'VIGENTE'),
                estudiantes_asignados=request.POST.get('estudiantes_asignados') or None,
                observaciones=request.POST.get('observaciones') or None,
            )
            convenio.save()
            messages.success(request, 'Convenio registrado correctamente.')
            return redirect('convenio_detalle', id=convenio.pk)
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')

    proyectos = Proyecto.objects.filter(estado__in=['APROBADO', 'EN_EJECUCION']).order_by('nombre')
    entidades = EntidadCooperante.objects.filter(activo=True).order_by('nombre')
    periodos = PeriodoAcademico.objects.order_by('-fecha_inicio')

    return render(request, 'convenios/form.html', {
        'proyectos': proyectos,
        'entidades': entidades,
        'periodos': periodos,
        'estados': ['VIGENTE', 'VENCIDO', 'RENOVADO', 'CANCELADO'],
        'accion': 'Registrar',
    })


def convenio_editar(request, id):
    if not request.session.get('usuario_id'):
        return redirect('login')

    convenio = get_object_or_404(Convenio, pk=id)

    if request.method == 'POST':
        try:
            convenio.id_proyecto = Proyecto.objects.get(pk=request.POST['id_proyecto'])
            convenio.id_entidad = EntidadCooperante.objects.get(pk=request.POST['id_entidad'])
            convenio.id_periodo = PeriodoAcademico.objects.get(pk=request.POST['id_periodo'])
            convenio.numero_memorando = request.POST.get('numero_memorando') or None
            convenio.fecha_firma = request.POST.get('fecha_firma') or None
            convenio.fecha_inicio = request.POST.get('fecha_inicio') or None
            convenio.fecha_fin = request.POST.get('fecha_fin') or None
            convenio.duracion_anios = request.POST.get('duracion_anios') or 2
            convenio.estado = request.POST.get('estado', 'VIGENTE')
            convenio.estudiantes_asignados = request.POST.get('estudiantes_asignados') or None
            convenio.observaciones = request.POST.get('observaciones') or None
            convenio.save()
            messages.success(request, 'Convenio actualizado correctamente.')
            return redirect('convenio_detalle', id=convenio.pk)
        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')

    proyectos = Proyecto.objects.filter(estado__in=['APROBADO', 'EN_EJECUCION']).order_by('nombre')
    entidades = EntidadCooperante.objects.filter(activo=True).order_by('nombre')
    periodos = PeriodoAcademico.objects.order_by('-fecha_inicio')

    return render(request, 'convenios/form.html', {
        'convenio': convenio,
        'proyectos': proyectos,
        'entidades': entidades,
        'periodos': periodos,
        'estados': ['VIGENTE', 'VENCIDO', 'RENOVADO', 'CANCELADO'],
        'accion': 'Editar',
    })


def convenio_eliminar(request, id):
    if not request.session.get('usuario_id'):
        return redirect('login')

    if request.method == 'POST':
        convenio = get_object_or_404(Convenio, pk=id)
        for anexo in convenio.anexos.all():
            ruta = os.path.join(settings.MEDIA_ROOT, anexo.ruta_archivo)
            if os.path.exists(ruta):
                os.remove(ruta)
        convenio.delete()
        messages.success(request, 'Convenio eliminado correctamente.')
    return redirect('convenios_lista')


def convenio_detalle(request, id):
    if not request.session.get('usuario_id'):
        return redirect('login')

    convenio = get_object_or_404(
        Convenio.objects.select_related('id_proyecto', 'id_entidad', 'id_periodo'),
        pk=id
    )
    anexos = convenio.anexos.all().order_by('-subido_en')

    return render(request, 'convenios/detalle.html', {
        'convenio': convenio,
        'anexos': anexos,
    })


# ── ANEXOS ────────────────────────────────────────────────────────

def anexo_subir(request, id_convenio):
    if not request.session.get('usuario_id'):
        return redirect('login')

    if request.method == 'POST' and request.FILES.get('archivo'):
        convenio = get_object_or_404(Convenio, pk=id_convenio)
        archivo = request.FILES['archivo']

        carpeta = os.path.join(settings.MEDIA_ROOT, 'convenios', str(id_convenio))
        os.makedirs(carpeta, exist_ok=True)

        ext = os.path.splitext(archivo.name)[1].lower()
        nombre_unico = f"{uuid.uuid4().hex}{ext}"
        ruta_completa = os.path.join(carpeta, nombre_unico)

        with open(ruta_completa, 'wb+') as f:
            for chunk in archivo.chunks():
                f.write(chunk)

        tamanio_kb = archivo.size // 1024

        AnexoConvenio.objects.create(
            id_convenio=convenio,
            nombre_archivo=archivo.name,
            ruta_archivo=f'convenios/{id_convenio}/{nombre_unico}',
            tipo_documento=request.POST.get('tipo_documento') or None,
            tamanio_kb=tamanio_kb,
            descripcion=request.POST.get('descripcion') or None,
        )
        messages.success(request, 'Anexo subido correctamente.')

    return redirect('convenio_detalle', id=id_convenio)


def anexo_eliminar(request, id_anexo):
    if not request.session.get('usuario_id'):
        return redirect('login')

    if request.method == 'POST':
        anexo = get_object_or_404(AnexoConvenio, pk=id_anexo)
        id_convenio = anexo.id_convenio.pk
        ruta = os.path.join(settings.MEDIA_ROOT, anexo.ruta_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)
        anexo.delete()
        messages.success(request, 'Anexo eliminado.')
        return redirect('convenio_detalle', id=id_convenio)

    return redirect('convenios_lista')


# ── DETALLE DE PROYECTO ───────────────────────────────────────────

def proyecto_detalle(request, id):
    proyecto = get_object_or_404(
        Proyecto.objects.select_related('id_facultad', 'id_carrera', 'id_periodo_inicio'),
        id_proyecto=id,
    )
    fotos = FotoProyecto.objects.filter(id_proyecto=proyecto).order_by('subida_en')
    convenios = Convenio.objects.filter(id_proyecto=proyecto).select_related('id_entidad', 'id_periodo').order_by('-creado_en')
    return render(request, 'proyectos/detalle.html', {
        'proyecto': proyecto,
        'fotos': fotos,
        'convenios': convenios,
    })


def api_proyecto_detalle(request, id):
    """JSON para el modal del mapa."""
    proyecto = get_object_or_404(
        Proyecto.objects.select_related('id_facultad', 'id_carrera', 'id_periodo_inicio'),
        id_proyecto=id,
    )
    fotos = list(FotoProyecto.objects.filter(id_proyecto=proyecto).values('ruta_foto', 'titulo'))
    fotos_urls = [{'url': '/media/' + f['ruta_foto'], 'titulo': f['titulo']} for f in fotos]
    convenios_count = Convenio.objects.filter(id_proyecto=proyecto).count()

    COLORES = {
        'EN_EJECUCION': '#1b7505', 'PROPUESTO': '#dba112', 'APROBADO': '#0d6efd',
        'EN_CIERRE': '#fd7e14', 'DETENIDO': '#dc3545', 'FINALIZADO': '#a8a8a7', 'RECHAZADO': '#6c757d',
    }
    ESTADO_LABEL = {
        'EN_EJECUCION': 'En ejecución', 'PROPUESTO': 'Propuesto', 'APROBADO': 'Aprobado',
        'EN_CIERRE': 'En cierre', 'DETENIDO': 'Detenido', 'FINALIZADO': 'Finalizado', 'RECHAZADO': 'Rechazado',
    }

    return JsonResponse({
        'id': proyecto.id_proyecto,
        'codigo': proyecto.codigo,
        'nombre': proyecto.nombre,
        'nombre_corto': proyecto.nombre_corto or '',
        'facultad': proyecto.id_facultad.nombre,
        'carrera': proyecto.id_carrera.nombre,
        'periodo': proyecto.id_periodo_inicio.nombre,
        'estado': proyecto.estado,
        'estado_label': ESTADO_LABEL.get(proyecto.estado, proyecto.estado),
        'color': COLORES.get(proyecto.estado, '#1b7505'),
        'provincia': proyecto.provincia or '',
        'canton': proyecto.canton or '',
        'parroquia': proyecto.parroquia or '',
        'sector': proyecto.sector or '',
        'descripcion': proyecto.descripcion or '',
        'objetivo_general': proyecto.objetivo_general or '',
        'ods': proyecto.ods or '',
        'alcance': proyecto.alcance or '',
        'linea_vinculacion': proyecto.linea_vinculacion or '',
        'fecha_inicio': str(proyecto.fecha_inicio) if proyecto.fecha_inicio else '',
        'fecha_fin_planificada': str(proyecto.fecha_fin_planificada) if proyecto.fecha_fin_planificada else '',
        'presupuesto_planificado': str(proyecto.presupuesto_planificado) if proyecto.presupuesto_planificado is not None else '',
        'terminos_negociacion': proyecto.terminos_negociacion or '',
        'resolucion_aprobacion': proyecto.resolucion_aprobacion or '',
        'fecha_aprobacion': str(proyecto.fecha_aprobacion) if proyecto.fecha_aprobacion else '',
        'fotos': fotos_urls,
        'convenios_count': convenios_count,
        'url_detalle': f'/proyectos/{proyecto.id_proyecto}/detalle/',
        'url_editar': f'/proyectos/{proyecto.id_proyecto}/editar/',
    })


# ── EDICIÓN RÁPIDA (modal mapa) ───────────────────────────────────

def api_proyecto_editar_rapido(request, id):
    if not request.session.get('usuario_id'):
        return JsonResponse({'ok': False, 'error': 'No autenticado'}, status=401)

    proyecto = get_object_or_404(Proyecto, id_proyecto=id)

    if request.method == 'GET':
        fotos = list(FotoProyecto.objects.filter(id_proyecto=proyecto).values('id_foto', 'ruta_foto', 'titulo'))
        return JsonResponse({
            'ok': True,
            'proyecto': {
                'id': proyecto.id_proyecto,
                'codigo': proyecto.codigo,
                'nombre': proyecto.nombre,
                'nombre_corto': proyecto.nombre_corto or '',
                'estado': proyecto.estado,
                'descripcion': proyecto.descripcion or '',
                'objetivo_general': proyecto.objetivo_general or '',
                'provincia': proyecto.provincia or '',
                'canton': proyecto.canton or '',
                'parroquia': proyecto.parroquia or '',
                'sector': proyecto.sector or '',
                'latitud': str(proyecto.latitud) if proyecto.latitud else '',
                'longitud': str(proyecto.longitud) if proyecto.longitud else '',
                'ods': proyecto.ods or '',
                'linea_vinculacion': proyecto.linea_vinculacion or '',
                'observaciones': proyecto.observaciones or '',
                'fotos': [{'id': f['id_foto'], 'url': '/media/' + f['ruta_foto'], 'titulo': f['titulo']} for f in fotos],
            }
        })

    if request.method == 'POST':
        try:
            proyecto.estado = request.POST.get('estado', proyecto.estado)
            proyecto.nombre = request.POST.get('nombre', proyecto.nombre).strip() or proyecto.nombre
            proyecto.nombre_corto = request.POST.get('nombre_corto', '').strip() or None
            proyecto.descripcion = request.POST.get('descripcion', '').strip() or None
            proyecto.objetivo_general = request.POST.get('objetivo_general', '').strip() or None
            proyecto.provincia = request.POST.get('provincia', '').strip() or None
            proyecto.canton = request.POST.get('canton', '').strip() or None
            proyecto.parroquia = request.POST.get('parroquia', '').strip() or None
            proyecto.sector = request.POST.get('sector', '').strip() or None
            lat = request.POST.get('latitud', '').strip()
            lng = request.POST.get('longitud', '').strip()
            proyecto.latitud = lat if lat else None
            proyecto.longitud = lng if lng else None
            proyecto.ods = request.POST.get('ods', '').strip() or None
            proyecto.linea_vinculacion = request.POST.get('linea_vinculacion', '').strip() or None
            proyecto.observaciones = request.POST.get('observaciones', '').strip() or None
            proyecto.actualizado_en = timezone.now()
            proyecto.save()
            # Fotos nuevas
            for foto in request.FILES.getlist('fotos'):
                carpeta = f'proyectos/{proyecto.id_proyecto}/'
                ruta_completa = os.path.join(settings.MEDIA_ROOT, carpeta)
                os.makedirs(ruta_completa, exist_ok=True)
                ruta_final = os.path.join(ruta_completa, foto.name)
                with open(ruta_final, 'wb+') as fh:
                    for chunk in foto.chunks():
                        fh.write(chunk)
                FotoProyecto.objects.create(
                    id_proyecto=proyecto,
                    ruta_foto=f'{carpeta}{foto.name}',
                    titulo=foto.name,
                    subida_en=timezone.now(),
                )
            # Eliminar fotos marcadas
            for foto_id in request.POST.getlist('eliminar_foto'):
                try:
                    foto = FotoProyecto.objects.get(id_foto=foto_id, id_proyecto=proyecto)
                    ruta = os.path.join(settings.MEDIA_ROOT, foto.ruta_foto)
                    if os.path.exists(ruta):
                        os.remove(ruta)
                    foto.delete()
                except FotoProyecto.DoesNotExist:
                    pass
            return JsonResponse({'ok': True, 'mensaje': 'Proyecto actualizado correctamente.'})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


# ── REPORTES ─────────────────────────────────────────────────────

def reportes_view(request):
    # KPIs principales
    total_proyectos = Proyecto.objects.count()
    proyectos_activos = Proyecto.objects.filter(estado='EN_EJECUCION').count()
    total_entidades = EntidadCooperante.objects.filter(activo=True).count()
    total_convenios = Convenio.objects.count()
    convenios_vigentes = Convenio.objects.filter(estado='VIGENTE').count()

    # Proyectos por estado
    por_estado_qs = (
        Proyecto.objects
        .values('estado')
        .annotate(total=Count('id_proyecto'))
        .order_by('-total')
    )
    ESTADO_LABEL = {
        'EN_EJECUCION': 'En ejecución', 'PROPUESTO': 'Propuesto', 'APROBADO': 'Aprobado',
        'EN_CIERRE': 'En cierre', 'DETENIDO': 'Detenido', 'FINALIZADO': 'Finalizado', 'RECHAZADO': 'Rechazado',
    }
    ESTADO_COLOR = {
        'EN_EJECUCION': '#1b7505', 'PROPUESTO': '#dba112', 'APROBADO': '#0d6efd',
        'EN_CIERRE': '#fd7e14', 'DETENIDO': '#dc3545', 'FINALIZADO': '#a8a8a7', 'RECHAZADO': '#6c757d',
    }
    por_estado = [
        {
            'estado': x['estado'],
            'label': ESTADO_LABEL.get(x['estado'], x['estado']),
            'total': x['total'],
            'color': ESTADO_COLOR.get(x['estado'], '#a8a8a7'),
            'pct': round(x['total'] / total_proyectos * 100) if total_proyectos else 0,
        }
        for x in por_estado_qs
    ]

    # Proyectos por facultad
    por_facultad = (
        Proyecto.objects
        .values('id_facultad__nombre', 'id_facultad__nombre_corto')
        .annotate(total=Count('id_proyecto'))
        .order_by('-total')[:8]
    )

    # Proyectos por período (top 8)
    por_periodo = (
        Proyecto.objects
        .values('id_periodo_inicio__nombre', 'id_periodo_inicio__codigo')
        .annotate(total=Count('id_proyecto'))
        .order_by('-total')[:8]
    )

    # Convenios por estado
    convenios_por_estado = (
        Convenio.objects
        .values('estado')
        .annotate(total=Count('id_convenio'))
        .order_by('-total')
    )
    CONV_COLOR = {
        'VIGENTE': '#1b7505', 'VENCIDO': '#dc3545',
        'RENOVADO': '#0d6efd', 'CANCELADO': '#a8a8a7',
    }
    convenios_estado_list = [
        {'estado': x['estado'], 'total': x['total'], 'color': CONV_COLOR.get(x['estado'], '#a8a8a7')}
        for x in convenios_por_estado
    ]

    # Entidades por tipo
    entidades_por_tipo = (
        EntidadCooperante.objects
        .filter(activo=True)
        .values('id_tipo__nombre')
        .annotate(total=Count('id_entidad'))
        .order_by('-total')[:6]
    )

    # Proyectos con geolocalización
    proyectos_geo = Proyecto.objects.filter(latitud__isnull=False, longitud__isnull=False).count()

    # Proyectos por provincia (top 10)
    por_provincia = list(
        Proyecto.objects
        .exclude(provincia__isnull=True).exclude(provincia='')
        .values('provincia')
        .annotate(total=Count('id_proyecto'))
        .order_by('-total')[:10]
    )

    # Proyectos por canton (top 8)
    por_canton = list(
        Proyecto.objects
        .exclude(canton__isnull=True).exclude(canton='')
        .values('canton', 'provincia')
        .annotate(total=Count('id_proyecto'))
        .order_by('-total')[:8]
    )

    # Últimos proyectos registrados
    ultimos_proyectos = Proyecto.objects.select_related(
        'id_facultad', 'id_periodo_inicio'
    ).order_by('-creado_en')[:5]

    return render(request, 'reportes/dashboard.html', {
        'total_proyectos': total_proyectos,
        'proyectos_activos': proyectos_activos,
        'total_entidades': total_entidades,
        'total_convenios': total_convenios,
        'convenios_vigentes': convenios_vigentes,
        'proyectos_geo': proyectos_geo,
        'por_estado': por_estado,
        'por_facultad': por_facultad,
        'por_periodo': por_periodo,
        'convenios_estado_list': convenios_estado_list,
        'entidades_por_tipo': entidades_por_tipo,
        'ultimos_proyectos': ultimos_proyectos,
        'por_provincia': por_provincia,
        'por_canton': por_canton,
        'ESTADO_COLOR': ESTADO_COLOR,
        'ESTADO_LABEL': ESTADO_LABEL,
    })


# ─────────────────────────────────────────────
#  API REST para Svelte
# ─────────────────────────────────────────────

@csrf_exempt
def api_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return JsonResponse({'error': 'Credenciales requeridas'}, status=400)
    try:
        usuario = Usuario.objects.select_related('id_rol').get(username=username, activo=True)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario o contraseña incorrectos'}, status=401)
    from vinculacion.utils import verificar_password
    if not verificar_password(password, usuario.password):
        return JsonResponse({'error': 'Usuario o contraseña incorrectos'}, status=401)
    request.session['usuario_id'] = usuario.id_usuario
    request.session['usuario_nombre'] = usuario.nombres or username
    request.session['usuario_rol'] = usuario.id_rol.nombre
    usuario.ultimo_acceso = timezone.now()
    usuario.save(update_fields=['ultimo_acceso'])
    return JsonResponse({
        'id': usuario.id_usuario,
        'nombre': usuario.nombres or username,
        'username': usuario.username,
        'rol': usuario.id_rol.nombre,
        'debe_cambiar_clave': usuario.debe_cambiar_clave,
    })


def api_logout(request):
    request.session.flush()
    return JsonResponse({'ok': True})


def api_me(request):
    uid = request.session.get('usuario_id')
    if not uid:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    try:
        u = Usuario.objects.select_related('id_rol').get(id_usuario=uid)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    periodo = PeriodoAcademico.objects.filter(activo=True).first()
    return JsonResponse({
        'id': u.id_usuario,
        'nombre': u.nombres or u.username,
        'username': u.username,
        'rol': u.id_rol.nombre,
        'periodo': {'nombre': periodo.nombre, 'codigo': periodo.codigo} if periodo else None,
    })


@api_view(['GET'])
def api_dashboard_stats(request):
    if not request.session.get('usuario_id'):
        return Response({'error': 'No autenticado'}, status=401)
    return Response({
        'proyectos': Proyecto.objects.count(),
        'entidades': EntidadCooperante.objects.filter(activo=True).count(),
        'convenios': Convenio.objects.count(),
        'facultades': Facultad.objects.filter(activo=True).count(),
        'periodos': PeriodoAcademico.objects.count(),
        'proyectos_activos': Proyecto.objects.filter(estado='EN_EJECUCION').count(),
    })


@api_view(['GET'])
def api_periodos(request):
    if not request.session.get('usuario_id'):
        return Response({'error': 'No autenticado'}, status=401)
    qs = PeriodoAcademico.objects.all().order_by('-fecha_inicio')
    return Response(PeriodoSerializer(qs, many=True).data)


@api_view(['GET'])
def api_tipos_documento(request):
    if not request.session.get('usuario_id'):
        return Response({'error': 'No autenticado'}, status=401)
    qs = TipoDocumento.objects.all().order_by('numero_carpeta')
    return Response([
        {'codigo': t.codigo, 'nombre': t.nombre, 'numero_carpeta': t.numero_carpeta}
        for t in qs
    ])


@api_view(['GET'])
def api_facultades(request):
    if not request.session.get('usuario_id'):
        return Response({'error': 'No autenticado'}, status=401)
    qs = Facultad.objects.all().order_by('nombre')
    return Response(FacultadSerializer(qs, many=True).data)


@api_view(['GET'])
def api_carreras(request):
    if not request.session.get('usuario_id'):
        return Response({'error': 'No autenticado'}, status=401)
    qs = Carrera.objects.select_related('id_facultad').all().order_by('nombre')
    return Response(CarreraSerializer(qs, many=True).data)


@api_view(['GET'])
def api_entidades(request):
    if not request.session.get('usuario_id'):
        return Response({'error': 'No autenticado'}, status=401)
    q = request.GET.get('q', '')
    qs = EntidadCooperante.objects.select_related('id_tipo').all().order_by('nombre')
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(ruc__icontains=q))
    return Response(EntidadSerializer(qs, many=True).data)


@api_view(['GET'])
def api_proyectos(request):
    if not request.session.get('usuario_id'):
        return Response({'error': 'No autenticado'}, status=401)
    q = request.GET.get('q', '')
    qs = Proyecto.objects.select_related(
        'id_facultad', 'id_carrera', 'id_periodo_inicio'
    ).all().order_by('-creado_en')
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
    return Response(ProyectoSerializer(qs, many=True).data)


@api_view(['GET'])
def api_convenios(request):
    if not request.session.get('usuario_id'):
        return Response({'error': 'No autenticado'}, status=401)
    qs = Convenio.objects.select_related(
        'id_proyecto', 'id_entidad', 'id_periodo'
    ).all().order_by('-creado_en')
    return Response(ConvenioSerializer(qs, many=True).data)


@api_view(['GET'])
def api_docentes(request):
    if not request.session.get('usuario_id'):
        return Response({'error': 'No autenticado'}, status=401)
    qs = Docente.objects.all().order_by('apellidos')
    return Response(DocenteSerializer(qs, many=True).data)


def _require_auth(request):
    return request.session.get('usuario_id')


# ── PERIODOS CRUD ──────────────────────────────────────────────────

@csrf_exempt
def api_periodo_detail(request, id):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    periodo = get_object_or_404(PeriodoAcademico, id_periodo=id)
    if request.method == 'GET':
        return JsonResponse(PeriodoSerializer(periodo).data)
    if request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
        for field in ['codigo', 'nombre', 'tipo', 'fecha_inicio', 'fecha_fin']:
            if field in data and data[field]:
                setattr(periodo, field, data[field])
        if 'activo' in data:
            periodo.activo = bool(data['activo'])
        periodo.save()
        return JsonResponse(PeriodoSerializer(periodo).data)
    if request.method == 'DELETE':
        periodo.delete()
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'method'}, status=405)


@csrf_exempt
def api_periodos_post(request):
    """POST para crear periodo (GET ya lo maneja api_periodos)."""
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    try:
        if PeriodoAcademico.objects.filter(codigo=data['codigo']).exists():
            return JsonResponse({'error': f"Ya existe un periodo con el código {data['codigo']}"}, status=400)
        periodo = PeriodoAcademico.objects.create(
            codigo=data['codigo'],
            nombre=data['nombre'],
            tipo=data['tipo'],
            fecha_inicio=data['fecha_inicio'],
            fecha_fin=data['fecha_fin'],
            activo=data.get('activo', True),
            creado_en=timezone.now(),
        )
        return JsonResponse(PeriodoSerializer(periodo).data, status=201)
    except Exception as e:
        return JsonResponse({'error': _error_amigable(e)}, status=400)


# ── FACULTADES CRUD ──────────────────────────────────────────────────

@csrf_exempt
def api_facultad_detail(request, id):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    facultad = get_object_or_404(Facultad, id_facultad=id)
    if request.method == 'GET':
        return JsonResponse(FacultadSerializer(facultad).data)
    if request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
        for field in ['codigo', 'nombre', 'nombre_corto', 'campus']:
            if field in data:
                setattr(facultad, field, data[field])
        if 'activo' in data:
            facultad.activo = bool(data['activo'])
        facultad.save()
        return JsonResponse(FacultadSerializer(facultad).data)
    return JsonResponse({'error': 'method'}, status=405)


# ── CARRERAS CRUD ──────────────────────────────────────────────────

@csrf_exempt
def api_carreras_post(request):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    try:
        fac = Facultad.objects.get(id_facultad=data['id_facultad'])
        carrera = Carrera.objects.create(
            nombre=data['nombre'],
            codigo=data.get('codigo', ''),
            id_facultad=fac,
            horas_vinculacion=data.get('horas_vinculacion', 160),
            area_conocimiento=data.get('area_conocimiento', '') or None,
            activo=data.get('activo', True),
        )
        return JsonResponse(CarreraSerializer(carrera).data, status=201)
    except Exception as e:
        return JsonResponse({'error': _error_amigable(e)}, status=400)


@csrf_exempt
def api_carrera_detail(request, id):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    carrera = get_object_or_404(Carrera, id_carrera=id)
    if request.method == 'GET':
        return JsonResponse(CarreraSerializer(carrera).data)
    if request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
        for field in ['nombre', 'codigo', 'horas_vinculacion', 'area_conocimiento']:
            if field in data:
                setattr(carrera, field, data[field])
        if 'id_facultad' in data:
            carrera.id_facultad = get_object_or_404(Facultad, id_facultad=data['id_facultad'])
        if 'activo' in data:
            carrera.activo = bool(data['activo'])
        carrera.save()
        return JsonResponse(CarreraSerializer(carrera).data)
    if request.method == 'DELETE':
        carrera.delete()
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'method'}, status=405)


# ── ENTIDADES CRUD ─────────────────────────────────────────────────

@csrf_exempt
def api_entidades_post(request):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method == 'GET':
        qs = TipoEntidad.objects.all().order_by('nombre')
        return JsonResponse({'tipos': TipoEntidadSerializer(qs, many=True).data})
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    try:
        tipo = TipoEntidad.objects.get(id_tipo=data['id_tipo'])
        ruc = data.get('ruc', '').strip() or None
        if ruc and EntidadCooperante.objects.filter(ruc=ruc).exists():
            return JsonResponse({'error': f'Ya existe una entidad con el RUC {ruc}'}, status=400)
        entidad = EntidadCooperante.objects.create(
            nombre=data['nombre'],
            nombre_corto=data.get('nombre_corto', '') or None,
            id_tipo=tipo,
            ruc=ruc,
            representante_legal=data.get('representante_legal', '') or None,
            cargo_representante=data.get('cargo_representante', '') or None,
            telefono=data.get('telefono', '') or None,
            correo=data.get('correo', '') or None,
            pagina_web=data.get('pagina_web', '') or None,
            provincia=data.get('provincia', '') or None,
            canton=data.get('canton', '') or None,
            parroquia=data.get('parroquia', '') or None,
            direccion=data.get('direccion', '') or None,
            sector=data.get('sector', '') or None,
            observaciones=data.get('observaciones', '') or None,
            activo=data.get('activo', True),
            creado_en=timezone.now(),
        )
        return JsonResponse(EntidadSerializer(entidad).data, status=201)
    except Exception as e:
        return JsonResponse({'error': _error_amigable(e)}, status=400)


@csrf_exempt
def api_entidad_detail(request, id):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    entidad = get_object_or_404(EntidadCooperante, id_entidad=id)
    if request.method == 'GET':
        return JsonResponse(EntidadSerializer(entidad).data)
    if request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
        for field in ['nombre', 'nombre_corto', 'ruc', 'representante_legal', 'cargo_representante',
                      'telefono', 'correo', 'pagina_web', 'provincia', 'canton', 'parroquia',
                      'direccion', 'sector', 'observaciones']:
            if field in data:
                setattr(entidad, field, data[field] or None)
        if 'id_tipo' in data:
            entidad.id_tipo = get_object_or_404(TipoEntidad, id_tipo=data['id_tipo'])
        if 'activo' in data:
            entidad.activo = bool(data['activo'])
        entidad.save()
        return JsonResponse(EntidadSerializer(entidad).data)
    return JsonResponse({'error': 'method'}, status=405)


# ── PROYECTOS CRUD ─────────────────────────────────────────────────

@csrf_exempt
def api_proyecto_create(request):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    try:
        codigo = request.POST.get('codigo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        if not codigo or not nombre:
            return JsonResponse({'error': 'Código y nombre son obligatorios'}, status=400)
        if Proyecto.objects.filter(codigo=codigo).exists():
            return JsonResponse({'error': f'Ya existe un proyecto con el código {codigo}'}, status=400)
        lat = request.POST.get('latitud', '').strip() or None
        lng = request.POST.get('longitud', '').strip() or None
        # nombre_corto se autogenera del título (se quitó como campo redundante)
        nombre_corto = request.POST.get('nombre_corto', '').strip() or (nombre[:120] if nombre else None)
        proyecto = Proyecto.objects.create(
            codigo=codigo,
            nombre=nombre,
            nombre_corto=nombre_corto,
            id_facultad=Facultad.objects.get(id_facultad=request.POST['id_facultad']),
            id_carrera=Carrera.objects.get(id_carrera=request.POST['id_carrera']),
            id_periodo_inicio=PeriodoAcademico.objects.get(id_periodo=request.POST['id_periodo_inicio']),
            estado=request.POST.get('estado', 'EN_EJECUCION'),
            programa=request.POST.get('programa', '').strip() or None,
            linea_vinculacion=request.POST.get('linea_vinculacion', '').strip() or None,
            area_conocimiento=request.POST.get('area_conocimiento', '').strip() or None,
            sub_area_conocimiento=request.POST.get('sub_area_conocimiento', '').strip() or None,
            director_nombre=request.POST.get('director_nombre', '').strip() or None,
            director_correo=request.POST.get('director_correo', '').strip() or None,
            provincia=request.POST.get('provincia', '').strip() or None,
            canton=request.POST.get('canton', '').strip() or None,
            parroquia=request.POST.get('parroquia', '').strip() or None,
            sector=request.POST.get('sector', '').strip() or None,
            descripcion=request.POST.get('descripcion', '').strip() or None,
            objetivo_general=request.POST.get('objetivo_general', '').strip() or None,
            fecha_inicio=request.POST.get('fecha_inicio', '').strip() or None,
            fecha_fin_planificada=request.POST.get('fecha_fin_planificada', '').strip() or None,
            ods=request.POST.get('ods', '').strip() or None,
            observaciones=request.POST.get('observaciones', '').strip() or None,
            presupuesto_planificado=request.POST.get('presupuesto_planificado', '').strip() or None,
            terminos_negociacion=request.POST.get('terminos_negociacion', '').strip() or None,
            latitud=lat,
            longitud=lng,
            creado_en=timezone.now(),
            actualizado_en=timezone.now(),
        )
        # Multi-ubicación: guardar puntos y reflejar el principal en el proyecto
        principal = _guardar_ubicaciones(request, proyecto)
        if principal:
            proyecto.latitud = principal.latitud
            proyecto.longitud = principal.longitud
            proyecto.provincia = principal.provincia if principal.provincia != 'N/D' else proyecto.provincia
            proyecto.canton = principal.canton or proyecto.canton
            proyecto.parroquia = principal.parroquia or proyecto.parroquia
            proyecto.sector = principal.sector or proyecto.sector
            proyecto.save(update_fields=['latitud', 'longitud', 'provincia', 'canton', 'parroquia', 'sector'])
        _guardar_fotos(request, proyecto)
        return JsonResponse(ProyectoSerializer(proyecto).data, status=201)
    except Exception as e:
        return JsonResponse({'error': _error_amigable(e)}, status=400)


from vinculacion.models import TipoDocumento


@csrf_exempt
def api_documento_subir(request, id):
    """
    Sube un documento del portafolio a un proyecto (por código de tipo, ej DOC_01).
    Opcional: si vienen datos de aprobación (paso 2), actualiza el proyecto.
    """
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    proyecto = get_object_or_404(Proyecto, id_proyecto=id)
    codigo_tipo = request.POST.get('codigo_tipo', '').strip()
    tipo = TipoDocumento.objects.filter(codigo=codigo_tipo).first()
    if not tipo:
        return JsonResponse({'error': f'Tipo de documento {codigo_tipo} no existe'}, status=400)

    archivo = request.FILES.get('archivo')
    creado = None
    if archivo:
        error = _validar_archivo(archivo, EXTENSIONES_DOCUMENTO)
        if error:
            return JsonResponse({'error': error}, status=400)
        carpeta = f'proyectos/{proyecto.id_proyecto}/documentos/'
        ruta_completa = os.path.join(settings.MEDIA_ROOT, carpeta)
        os.makedirs(ruta_completa, exist_ok=True)
        nombre_archivo = f'{codigo_tipo}_{archivo.name}'
        with open(os.path.join(ruta_completa, nombre_archivo), 'wb+') as f:
            for chunk in archivo.chunks():
                f.write(chunk)
        ext = (archivo.name.rsplit('.', 1)[-1] if '.' in archivo.name else '')[:10]
        creado = DocumentoProyecto.objects.create(
            id_proyecto=proyecto,
            id_tipo_doc=tipo,
            id_periodo=proyecto.id_periodo_inicio,
            nombre_archivo=archivo.name,
            ruta_archivo=f'{carpeta}{nombre_archivo}',
            tamanio_kb=int(archivo.size / 1024),
            extension=ext,
            descripcion=request.POST.get('descripcion', '').strip() or None,
            subido_por_id=_require_auth(request),
            subido_en=timezone.now(),
        )

    # Datos de aprobación (solo para DOC_01)
    if codigo_tipo == 'DOC_01':
        fa = request.POST.get('fecha_aprobacion', '').strip()
        ra = request.POST.get('resolucion_aprobacion', '').strip()
        cambios = False
        if fa: proyecto.fecha_aprobacion = fa; cambios = True
        if ra: proyecto.resolucion_aprobacion = ra; cambios = True
        if cambios:
            proyecto.actualizado_en = timezone.now()
            proyecto.save(update_fields=['fecha_aprobacion', 'resolucion_aprobacion', 'actualizado_en'])

    return JsonResponse({
        'ok': True,
        'documento': None if not creado else {
            'id': creado.id_documento, 'nombre': creado.nombre_archivo,
            'url': '/media/' + creado.ruta_archivo, 'tipo': tipo.nombre,
        }
    }, status=201)


@csrf_exempt
def api_proyecto_documentos(request, id):
    """Lista los documentos del portafolio subidos a un proyecto."""
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    docs = (DocumentoProyecto.objects
            .filter(id_proyecto_id=id)
            .select_related('id_tipo_doc')
            .order_by('id_tipo_doc__numero_carpeta', 'subido_en'))
    data = [{
        'id': d.id_documento,
        'codigo_tipo': d.id_tipo_doc.codigo,
        'tipo': d.id_tipo_doc.nombre,
        'numero_carpeta': d.id_tipo_doc.numero_carpeta,
        'nombre': d.nombre_archivo,
        'url': '/media/' + d.ruta_archivo,
        'tamanio_kb': d.tamanio_kb,
        'subido_en': d.subido_en.isoformat() if d.subido_en else None,
    } for d in docs]
    return JsonResponse(data, safe=False)


@csrf_exempt
def api_documento_eliminar(request, id_documento):
    """Elimina un documento del portafolio."""
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method != 'DELETE':
        return JsonResponse({'error': 'method'}, status=405)
    doc = get_object_or_404(DocumentoProyecto, id_documento=id_documento)
    try:
        ruta = os.path.join(settings.MEDIA_ROOT, doc.ruta_archivo)
        if os.path.exists(ruta):
            os.remove(ruta)
    except Exception:
        pass
    doc.delete()
    return JsonResponse({'ok': True})


@csrf_exempt
def api_proyecto_delete(request, id):
    """Elimina un proyecto y todos sus registros dependientes."""
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method not in ('DELETE', 'POST'):
        return JsonResponse({'error': 'method'}, status=405)
    proyecto = get_object_or_404(Proyecto, id_proyecto=id)
    try:
        with transaction.atomic():
            # Hijos que referencian al proyecto (se borran primero por las FK)
            AnexoConvenio.objects.filter(id_convenio__id_proyecto=proyecto).delete()
            Convenio.objects.filter(id_proyecto=proyecto).delete()
            ProyectoUbicacion.objects.filter(id_proyecto=proyecto).delete()
            FotoProyecto.objects.filter(id_proyecto=proyecto).delete()
            DocumentoProyecto.objects.filter(id_proyecto=proyecto).delete()
            ProyectoDocente.objects.filter(id_proyecto=proyecto).delete()
            ProyectoEstudiante.objects.filter(id_proyecto=proyecto).delete()
            ProyectoBeneficiario.objects.filter(id_proyecto=proyecto).delete()
            InformeSemestral.objects.filter(id_proyecto=proyecto).delete()
            EvaluacionImpacto.objects.filter(id_proyecto=proyecto).delete()
            ActividadSemanal.objects.filter(id_proyecto=proyecto).delete()
            proyecto.delete()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': _error_amigable(e)}, status=400)


@csrf_exempt
def api_proyecto_update(request, id):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    proyecto = get_object_or_404(Proyecto, id_proyecto=id)
    if request.method == 'GET':
        fotos = list(FotoProyecto.objects.filter(id_proyecto=proyecto).values('id_foto', 'ruta_foto', 'titulo'))
        data = ProyectoSerializer(proyecto).data
        data['id_facultad'] = proyecto.id_facultad_id
        data['id_carrera'] = proyecto.id_carrera_id
        data['id_periodo_inicio'] = proyecto.id_periodo_inicio_id
        data['latitud'] = str(proyecto.latitud) if proyecto.latitud else ''
        data['longitud'] = str(proyecto.longitud) if proyecto.longitud else ''
        data['descripcion'] = proyecto.descripcion or ''
        data['objetivo_general'] = proyecto.objetivo_general or ''
        data['ods'] = proyecto.ods or ''
        data['linea_vinculacion'] = proyecto.linea_vinculacion or ''
        data['observaciones'] = proyecto.observaciones or ''
        data['director_nombre'] = proyecto.director_nombre or ''
        data['director_correo'] = proyecto.director_correo or ''
        data['area_conocimiento'] = proyecto.area_conocimiento or ''
        data['sub_area_conocimiento'] = proyecto.sub_area_conocimiento or ''
        data['programa'] = proyecto.programa or ''
        data['fecha_inicio'] = str(proyecto.fecha_inicio) if proyecto.fecha_inicio else ''
        data['fecha_fin_planificada'] = str(proyecto.fecha_fin_planificada) if proyecto.fecha_fin_planificada else ''
        data['fecha_aprobacion'] = str(proyecto.fecha_aprobacion) if proyecto.fecha_aprobacion else ''
        data['resolucion_aprobacion'] = proyecto.resolucion_aprobacion or ''
        data['presupuesto_planificado'] = str(proyecto.presupuesto_planificado) if proyecto.presupuesto_planificado is not None else ''
        data['terminos_negociacion'] = proyecto.terminos_negociacion or ''
        data['fotos'] = [{'id': f['id_foto'], 'url': '/media/' + f['ruta_foto'], 'titulo': f['titulo']} for f in fotos]
        ubis = ProyectoUbicacion.objects.filter(id_proyecto=proyecto).order_by('-es_principal', 'id_ubicacion')
        data['ubicaciones'] = [{
            'nombre_lugar': x.nombre_lugar or '',
            'provincia': x.provincia if x.provincia != 'N/D' else '',
            'canton': x.canton or '',
            'parroquia': x.parroquia or '',
            'sector': x.sector or '',
            'latitud': str(x.latitud) if x.latitud is not None else '',
            'longitud': str(x.longitud) if x.longitud is not None else '',
            'es_principal': x.es_principal,
        } for x in ubis]
        return JsonResponse(data)
    if request.method == 'POST':
        try:
            codigo = request.POST.get('codigo', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            if not codigo or not nombre:
                return JsonResponse({'error': 'Código y nombre son obligatorios'}, status=400)
            if Proyecto.objects.filter(codigo=codigo).exclude(id_proyecto=id).exists():
                return JsonResponse({'error': f'Ya existe otro proyecto con el código {codigo}'}, status=400)
            proyecto.codigo = codigo
            proyecto.nombre = nombre
            proyecto.nombre_corto = request.POST.get('nombre_corto', '').strip() or (nombre[:120] if nombre else None)
            proyecto.id_facultad = Facultad.objects.get(id_facultad=request.POST['id_facultad'])
            proyecto.id_carrera = Carrera.objects.get(id_carrera=request.POST['id_carrera'])
            proyecto.id_periodo_inicio = PeriodoAcademico.objects.get(id_periodo=request.POST['id_periodo_inicio'])
            proyecto.estado = request.POST.get('estado', proyecto.estado)
            proyecto.director_nombre = request.POST.get('director_nombre', '').strip() or None
            proyecto.director_correo = request.POST.get('director_correo', '').strip() or None
            proyecto.linea_vinculacion = request.POST.get('linea_vinculacion', '').strip() or None
            proyecto.programa = request.POST.get('programa', '').strip() or None
            proyecto.area_conocimiento = request.POST.get('area_conocimiento', '').strip() or None
            proyecto.sub_area_conocimiento = request.POST.get('sub_area_conocimiento', '').strip() or None
            proyecto.provincia = request.POST.get('provincia', '').strip() or None
            proyecto.canton = request.POST.get('canton', '').strip() or None
            proyecto.parroquia = request.POST.get('parroquia', '').strip() or None
            proyecto.sector = request.POST.get('sector', '').strip() or None
            proyecto.descripcion = request.POST.get('descripcion', '').strip() or None
            proyecto.objetivo_general = request.POST.get('objetivo_general', '').strip() or None
            proyecto.ods = request.POST.get('ods', '').strip() or None
            proyecto.fecha_inicio = request.POST.get('fecha_inicio', '').strip() or None
            proyecto.fecha_fin_planificada = request.POST.get('fecha_fin_planificada', '').strip() or None
            proyecto.observaciones = request.POST.get('observaciones', '').strip() or None
            proyecto.presupuesto_planificado = request.POST.get('presupuesto_planificado', '').strip() or None
            proyecto.terminos_negociacion = request.POST.get('terminos_negociacion', '').strip() or None
            lat = request.POST.get('latitud', '').strip()
            lng = request.POST.get('longitud', '').strip()
            proyecto.latitud = lat or None
            proyecto.longitud = lng or None
            proyecto.actualizado_en = timezone.now()
            proyecto.save()
            # Multi-ubicación: reemplazar el conjunto de puntos y reflejar el principal
            if request.POST.get('ubicaciones'):
                principal = _guardar_ubicaciones(request, proyecto, reemplazar=True)
                if principal:
                    proyecto.latitud = principal.latitud
                    proyecto.longitud = principal.longitud
                    proyecto.provincia = principal.provincia if principal.provincia != 'N/D' else proyecto.provincia
                    proyecto.canton = principal.canton or proyecto.canton
                    proyecto.parroquia = principal.parroquia or proyecto.parroquia
                    proyecto.sector = principal.sector or proyecto.sector
                    proyecto.save(update_fields=['latitud', 'longitud', 'provincia', 'canton', 'parroquia', 'sector'])
            _guardar_fotos(request, proyecto)
            return JsonResponse(ProyectoSerializer(proyecto).data)
        except Exception as e:
            return JsonResponse({'error': _error_amigable(e)}, status=400)
    return JsonResponse({'error': 'method'}, status=405)


@csrf_exempt
def api_proyecto_eliminar_foto(request, id_foto):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method == 'DELETE':
        foto = get_object_or_404(FotoProyecto, id_foto=id_foto)
        ruta = os.path.join(settings.MEDIA_ROOT, str(foto.ruta_foto))
        if os.path.exists(ruta):
            os.remove(ruta)
        foto.delete()
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'method'}, status=405)


# ── CONVENIOS CRUD ─────────────────────────────────────────────────

@csrf_exempt
def api_convenios_post(request):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method == 'GET':
        # Lista completa con filtros
        q = request.GET.get('q', '')
        estado = request.GET.get('estado', '')
        periodo_id = request.GET.get('periodo', '')
        qs = Convenio.objects.select_related('id_proyecto', 'id_entidad', 'id_periodo').all().order_by('-creado_en')
        if q:
            qs = qs.filter(
                Q(numero_memorando__icontains=q) |
                Q(id_entidad__nombre__icontains=q) |
                Q(id_proyecto__nombre__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        if periodo_id:
            qs = qs.filter(id_periodo_id=periodo_id)
        data = []
        for c in qs:
            data.append({
                'id_convenio': c.pk,
                'numero_memorando': c.numero_memorando or '',
                'proyecto_nombre': c.id_proyecto.nombre_corto or c.id_proyecto.nombre,
                'entidad_nombre': c.id_entidad.nombre,
                'periodo_nombre': c.id_periodo.nombre if c.id_periodo else '',
                'fecha_firma': str(c.fecha_firma) if c.fecha_firma else '',
                'estudiantes_asignados': c.estudiantes_asignados or 0,
                'estado': c.estado,
                'id_proyecto': c.id_proyecto_id,
                'id_entidad': c.id_entidad_id,
                'id_periodo': c.id_periodo_id if c.id_periodo else None,
            })
        return JsonResponse({'results': data})
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    try:
        convenio = Convenio.objects.create(
            id_proyecto=Proyecto.objects.get(pk=data['id_proyecto']),
            id_entidad=EntidadCooperante.objects.get(pk=data['id_entidad']),
            id_periodo=PeriodoAcademico.objects.get(pk=data['id_periodo']) if data.get('id_periodo') else None,
            numero_memorando=data.get('numero_memorando', '') or None,
            fecha_firma=data.get('fecha_firma') or None,
            fecha_inicio=data.get('fecha_inicio') or None,
            fecha_fin=data.get('fecha_fin') or None,
            duracion_anios=data.get('duracion_anios') or 2,
            estudiantes_asignados=data.get('estudiantes_asignados') or None,
            estado=data.get('estado', 'VIGENTE'),
            observaciones=data.get('observaciones', '') or None,
        )
        return JsonResponse({'id_convenio': convenio.pk, 'ok': True}, status=201)
    except Exception as e:
        return JsonResponse({'error': _error_amigable(e)}, status=400)


@csrf_exempt
def api_convenio_detail(request, id):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    convenio = get_object_or_404(
        Convenio.objects.select_related('id_proyecto', 'id_entidad', 'id_periodo'), pk=id
    )
    if request.method == 'GET':
        anexos = list(convenio.anexos.all().values(
            'id_anexo', 'nombre_archivo', 'tipo_documento', 'tamanio_kb', 'descripcion', 'ruta_archivo', 'subido_en'
        ))
        for a in anexos:
            a['url'] = '/media/' + a['ruta_archivo']
            a['subido_en'] = str(a['subido_en'])
        return JsonResponse({
            'id_convenio': convenio.pk,
            'numero_memorando': convenio.numero_memorando or '',
            'estado': convenio.estado,
            'fecha_firma': str(convenio.fecha_firma) if convenio.fecha_firma else '',
            'fecha_inicio': str(convenio.fecha_inicio) if convenio.fecha_inicio else '',
            'fecha_fin': str(convenio.fecha_fin) if convenio.fecha_fin else '',
            'duracion_anios': convenio.duracion_anios,
            'estudiantes_asignados': convenio.estudiantes_asignados or 0,
            'observaciones': convenio.observaciones or '',
            'id_proyecto': convenio.id_proyecto_id,
            'proyecto_nombre': convenio.id_proyecto.nombre,
            'proyecto_corto': convenio.id_proyecto.nombre_corto or '',
            'id_entidad': convenio.id_entidad_id,
            'entidad_nombre': convenio.id_entidad.nombre,
            'entidad_siglas': convenio.id_entidad.nombre_corto or '',
            'entidad_representante': convenio.id_entidad.representante_legal or '',
            'entidad_cargo': convenio.id_entidad.cargo_representante or '',
            'entidad_provincia': convenio.id_entidad.provincia or '',
            'entidad_canton': convenio.id_entidad.canton or '',
            'entidad_telefono': convenio.id_entidad.telefono or '',
            'entidad_correo': convenio.id_entidad.correo or '',
            'id_periodo': convenio.id_periodo_id,
            'periodo_nombre': convenio.id_periodo.nombre if convenio.id_periodo else '',
            'anexos': anexos,
        })
    if request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
        for field in ['numero_memorando', 'fecha_firma', 'fecha_inicio', 'fecha_fin',
                      'duracion_anios', 'estudiantes_asignados', 'estado', 'observaciones']:
            if field in data:
                setattr(convenio, field, data[field] or None)
        if 'id_periodo' in data and data['id_periodo']:
            convenio.id_periodo = get_object_or_404(PeriodoAcademico, pk=data['id_periodo'])
        if 'estado' in data:
            convenio.estado = data['estado']
        convenio.save()
        return JsonResponse({'ok': True})
    if request.method == 'DELETE':
        for anexo in convenio.anexos.all():
            ruta = os.path.join(settings.MEDIA_ROOT, anexo.ruta_archivo)
            if os.path.exists(ruta):
                os.remove(ruta)
        convenio.delete()
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'method'}, status=405)


@csrf_exempt
def api_convenio_anexo_subir(request, id):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    convenio = get_object_or_404(Convenio, pk=id)
    archivo = request.FILES.get('archivo')
    if not archivo:
        return JsonResponse({'error': 'No se recibió archivo'}, status=400)
    error = _validar_archivo(archivo, EXTENSIONES_DOCUMENTO)
    if error:
        return JsonResponse({'error': error}, status=400)
    carpeta = os.path.join(settings.MEDIA_ROOT, 'convenios', str(id))
    os.makedirs(carpeta, exist_ok=True)
    ext = os.path.splitext(archivo.name)[1].lower()
    nombre_unico = f"{uuid.uuid4().hex}{ext}"
    ruta_completa = os.path.join(carpeta, nombre_unico)
    with open(ruta_completa, 'wb+') as f:
        for chunk in archivo.chunks():
            f.write(chunk)
    tamanio_kb = archivo.size // 1024
    anexo = AnexoConvenio.objects.create(
        id_convenio=convenio,
        nombre_archivo=archivo.name,
        ruta_archivo=f'convenios/{id}/{nombre_unico}',
        tipo_documento=request.POST.get('tipo_documento', '') or None,
        tamanio_kb=tamanio_kb,
        descripcion=request.POST.get('descripcion', '') or None,
    )
    return JsonResponse({
        'id_anexo': anexo.pk,
        'nombre_archivo': anexo.nombre_archivo,
        'tipo_documento': anexo.tipo_documento or '',
        'tamanio_kb': anexo.tamanio_kb,
        'url': '/media/' + anexo.ruta_archivo,
    }, status=201)


@csrf_exempt
def api_anexo_eliminar(request, id_anexo):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method != 'DELETE':
        return JsonResponse({'error': 'method'}, status=405)
    anexo = get_object_or_404(AnexoConvenio, pk=id_anexo)
    ruta = os.path.join(settings.MEDIA_ROOT, anexo.ruta_archivo)
    if os.path.exists(ruta):
        os.remove(ruta)
    anexo.delete()
    return JsonResponse({'ok': True})


# ── REPORTES ───────────────────────────────────────────────────────

def api_reportes_stats(request):
    if not _require_auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)

    periodo_id = request.GET.get('periodo')
    qs_proyectos = Proyecto.objects.all()
    if periodo_id:
        qs_proyectos = qs_proyectos.filter(id_periodo_inicio_id=periodo_id)

    total_proyectos = qs_proyectos.count()
    total_entidades = EntidadCooperante.objects.filter(activo=True).count()
    total_convenios = Convenio.objects.count()
    con_geo = qs_proyectos.filter(latitud__isnull=False, longitud__isnull=False).count()

    # Presupuesto acumulado
    presupuesto_total = float(qs_proyectos.aggregate(total=Sum('presupuesto_planificado'))['total'] or 0)

    # Estados
    estados_count = {}
    for e in qs_proyectos.values('estado').annotate(c=Count('estado')):
        estados_count[e['estado']] = e['c']

    # Facultades
    por_facultad = list(
        qs_proyectos.values('id_facultad__nombre_corto', 'id_facultad__nombre')
        .annotate(c=Count('id_proyecto'))
        .order_by('-c')[:10]
    )
    por_facultad_data = {
        'labels': [(x['id_facultad__nombre_corto'] or x['id_facultad__nombre'] or 'Sin facultad') for x in por_facultad],
        'values': [x['c'] for x in por_facultad],
    }

    # Carreras
    por_carrera = list(
        qs_proyectos.values('id_carrera__nombre')
        .annotate(c=Count('id_proyecto'))
        .order_by('-c')[:8]
    )
    por_carrera_data = {
        'labels': [x['id_carrera__nombre'] or 'Sin carrera' for x in por_carrera],
        'values': [x['c'] for x in por_carrera],
    }

    # Provincias (Proyectos + ProyectoUbicacion)
    provs_dict = {}
    for p in qs_proyectos.prefetch_related('proyectoubicacion_set'):
        prov = p.provincia
        if prov and prov != 'N/D':
            provs_dict[prov] = provs_dict.get(prov, 0) + 1
        for u in p.proyectoubicacion_set.all():
            if u.provincia and u.provincia != 'N/D' and u.provincia != prov:
                provs_dict[u.provincia] = provs_dict.get(u.provincia, 0) + 1

    provs_sorted = sorted(provs_dict.items(), key=lambda x: x[1], reverse=True)[:10]

    # Cantones
    cantons_dict = {}
    for p in qs_proyectos.prefetch_related('proyectoubicacion_set'):
        c = p.canton
        if c:
            cantons_dict[c] = cantons_dict.get(c, 0) + 1
        for u in p.proyectoubicacion_set.all():
            if u.canton and u.canton != c:
                cantons_dict[u.canton] = cantons_dict.get(u.canton, 0) + 1

    cantons_sorted = sorted(cantons_dict.items(), key=lambda x: x[1], reverse=True)[:8]

    # ODS Stats
    ods_dict = {}
    for p in qs_proyectos:
        if p.ods:
            tags = [t.strip() for t in p.ods.split(',') if t.strip()]
            for t in tags:
                ods_dict[t] = ods_dict.get(t, 0) + 1

    ods_sorted = sorted(ods_dict.items(), key=lambda x: x[1], reverse=True)[:10]

    convenios_estados = {}
    for e in Convenio.objects.values('estado').annotate(c=Count('id_convenio')):
        convenios_estados[e['estado']] = e['c']

    entidades_tipos = list(
        EntidadCooperante.objects.values('id_tipo__nombre').annotate(c=Count('id_entidad')).order_by('-c')
    )

    por_periodo = list(
        qs_proyectos.values('id_periodo_inicio__nombre', 'id_periodo_inicio__codigo')
        .annotate(c=Count('id_proyecto')).order_by('-c')[:8]
    )

    ultimos = list(
        qs_proyectos.select_related('id_facultad', 'id_periodo_inicio')
        .order_by('-creado_en')[:10]
        .values('id_proyecto', 'codigo', 'nombre', 'id_facultad__nombre_corto', 'id_facultad__nombre', 'id_periodo_inicio__nombre', 'estado')
    )

    en_ejecucion = estados_count.get('EN_EJECUCION', 0)
    finalizado = estados_count.get('FINALIZADO', 0)

    return JsonResponse({
        'kpis': {
            'total_proyectos': total_proyectos,
            'en_ejecucion': en_ejecucion,
            'total_entidades': total_entidades,
            'total_convenios': total_convenios,
            'con_geo': con_geo,
            'finalizado': finalizado,
            'presupuesto_total': presupuesto_total,
            'cantones_cobertura': len(cantons_dict),
            'provincias_cobertura': len(provs_dict),
            'pct_ejecucion': round(en_ejecucion * 100 / total_proyectos, 1) if total_proyectos else 0,
            'pct_finalizado': round(finalizado * 100 / total_proyectos, 1) if total_proyectos else 0,
        },
        'estados': estados_count,
        'por_facultad': por_facultad_data,
        'por_carrera': por_carrera_data,
        'por_provincia': {
            'labels': [x[0] for x in provs_sorted],
            'values': [x[1] for x in provs_sorted],
        },
        'por_canton': {
            'labels': [x[0] for x in cantons_sorted],
            'values': [x[1] for x in cantons_sorted],
        },
        'por_ods': {
            'labels': [x[0] for x in ods_sorted],
            'values': [x[1] for x in ods_sorted],
        },
        'convenios_estados': convenios_estados,
        'entidades_tipos': {
            'labels': [x['id_tipo__nombre'] or 'Sin tipo' for x in entidades_tipos],
            'values': [x['c'] for x in entidades_tipos],
        },
        'por_periodo': {
            'labels': [x['id_periodo_inicio__codigo'] or x['id_periodo_inicio__nombre'] or 'Período' for x in por_periodo],
            'values': [x['c'] for x in por_periodo],
        },
        'ultimos_proyectos': [
            {
                'id': x['id_proyecto'],
                'codigo': x['codigo'],
                'nombre': x['nombre'],
                'facultad': x['id_facultad__nombre_corto'] or x['id_facultad__nombre'] or 'N/A',
                'periodo': x['id_periodo_inicio__nombre'] or 'N/A',
                'estado': x['estado'],
            } for x in ultimos
        ],
    })

# ═══════════════════════════════════════════════════════════════════
# CAPAS TEMÁTICAS DEL MAPA (indicadores por cantón)
# Tabla: public.capa_indicador_canton  (modelo CapaIndicadorCanton)
# La geometría vive en /static/geo/cantones_ec.geojson y se une por dpa_canton.
# ═══════════════════════════════════════════════════════════════════

def api_capas_indicador_list(request):
    """Lista de capas cargadas, agrupadas por (tipo_indicador, anio)."""
    from .models import CapaIndicadorCanton
    from django.db.models import Min, Max, Count
    qs = (CapaIndicadorCanton.objects
          .values('tipo_indicador', 'anio', 'unidad', 'fuente')
          .annotate(total=Count('id_indicador'), min=Min('valor'), max=Max('valor'))
          .order_by('tipo_indicador', '-anio'))
    return JsonResponse([
        {
            'tipo_indicador': r['tipo_indicador'],
            'anio':   r['anio'],
            'unidad': r['unidad'],
            'fuente': r['fuente'],
            'total':  r['total'],
            'min':    float(r['min']) if r['min'] is not None else None,
            'max':    float(r['max']) if r['max'] is not None else None,
        } for r in qs
    ], safe=False)


@csrf_exempt
def api_capas_indicador_upload(request):
    """Carga masiva de valores desde CSV con columnas dpa_canton,valor.
    Form-data: tipo_indicador, anio, unidad, fuente, archivo.
    Reemplaza la capa (tipo, anio) si ya existe.
    """
    from .models import CapaIndicadorCanton
    from django.db import transaction
    import csv, io, re

    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    tipo   = (request.POST.get('tipo_indicador') or '').strip().upper()
    anio   = request.POST.get('anio')
    unidad = (request.POST.get('unidad') or '%').strip()
    fuente = (request.POST.get('fuente') or '').strip()
    f = request.FILES.get('archivo')

    if not tipo or not anio or not fuente or not f:
        return JsonResponse({'error': 'Faltan campos requeridos (tipo, anio, fuente, archivo)'}, status=400)
    try:
        anio = int(anio)
    except ValueError:
        return JsonResponse({'error': 'Año inválido'}, status=400)

    # Índice DPA→(provincia,canton) tomado de cualquier capa ya cargada
    dpa_index = {
        r['dpa_canton']: (r['provincia'], r['canton'])
        for r in CapaIndicadorCanton.objects.values('dpa_canton', 'provincia', 'canton').distinct()
    }

    # Leer CSV
    try:
        data = f.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        data = f.read().decode('latin-1')
    reader = csv.DictReader(io.StringIO(data))
    header = [h.strip().lower() for h in (reader.fieldnames or [])]
    if 'dpa_canton' not in header or 'valor' not in header:
        return JsonResponse({'error': 'CSV debe tener columnas dpa_canton y valor'}, status=400)

    filas, errores = [], []
    for i, row in enumerate(reader, start=2):
        rowl = {k.strip().lower(): (v or '').strip() for k, v in row.items()}
        dpa = rowl.get('dpa_canton', '')
        val = rowl.get('valor', '')
        if not re.fullmatch(r'\d{4}', dpa):
            errores.append(f'Fila {i}: dpa_canton inválido "{dpa}"'); continue
        try:
            valf = float(val)
        except ValueError:
            errores.append(f'Fila {i}: valor inválido "{val}"'); continue
        prov, cant = dpa_index.get(dpa, (rowl.get('provincia', ''), rowl.get('canton', '')))
        filas.append(CapaIndicadorCanton(
            tipo_indicador=tipo, dpa_canton=dpa,
            provincia=prov[:80], canton=cant[:80],
            valor=valf, unidad=unidad[:20], fuente=fuente[:160], anio=anio,
        ))

    if not filas:
        return JsonResponse({'error': 'No hay filas válidas', 'detalles': errores[:20]}, status=400)

    with transaction.atomic():
        CapaIndicadorCanton.objects.filter(tipo_indicador=tipo, anio=anio).delete()
        CapaIndicadorCanton.objects.bulk_create(filas, batch_size=500)

    return JsonResponse({
        'ok': True,
        'tipo_indicador': tipo, 'anio': anio,
        'insertados': len(filas),
        'errores_omitidos': len(errores),
        'detalles': errores[:20],
    })


@csrf_exempt
def api_capas_indicador_delete(request, tipo, anio):
    """Elimina una capa completa (tipo_indicador + anio)."""
    from .models import CapaIndicadorCanton
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    n, _ = CapaIndicadorCanton.objects.filter(tipo_indicador=tipo.upper(), anio=int(anio)).delete()
    return JsonResponse({'ok': True, 'eliminados': n})
