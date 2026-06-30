from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Count
from django.db.models.functions import ExtractYear
from django.conf import settings
import os
import uuid

from vinculacion.models import (
    Usuario, PeriodoAcademico, Facultad, Carrera,
    EntidadCooperante, TipoEntidad, Proyecto, FotoProyecto,
    Convenio, AnexoConvenio, ProyectoDocente, ProyectoEstudiante
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


def _guardar_fotos(request, proyecto):
    fotos = request.FILES.getlist('fotos')
    for foto in fotos:
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
    Devuelve el índice NBI por cantón (Censo 2022, INEC).
    Fuente: INEC, Documento_NBI_24.09.25.pdf, Anexo 1.
    Keyed by DPA canton code (4 dígitos).
    """
    NBI_DATA = {
        "0101":{"canton":"Cuenca","provincia":"Azuay","nbi_pct":19.8},
        "0102":{"canton":"Girón","provincia":"Azuay","nbi_pct":33.1},
        "0103":{"canton":"Gualaceo","provincia":"Azuay","nbi_pct":42.6},
        "0104":{"canton":"Nabón","provincia":"Azuay","nbi_pct":72.3},
        "0105":{"canton":"Paute","provincia":"Azuay","nbi_pct":32.5},
        "0106":{"canton":"Pucará","provincia":"Azuay","nbi_pct":64.5},
        "0107":{"canton":"San Fernando","provincia":"Azuay","nbi_pct":31.3},
        "0108":{"canton":"Santa Isabel","provincia":"Azuay","nbi_pct":37.4},
        "0109":{"canton":"Sígsig","provincia":"Azuay","nbi_pct":52.4},
        "0110":{"canton":"Oña","provincia":"Azuay","nbi_pct":56.4},
        "0111":{"canton":"Chordeleg","provincia":"Azuay","nbi_pct":33.0},
        "0112":{"canton":"El Pan","provincia":"Azuay","nbi_pct":25.6},
        "0113":{"canton":"Sevilla de Oro","provincia":"Azuay","nbi_pct":26.8},
        "0114":{"canton":"Guachapala","provincia":"Azuay","nbi_pct":31.9},
        "0115":{"canton":"Camilo Ponce Enríquez","provincia":"Azuay","nbi_pct":39.2},
        "0201":{"canton":"Guaranda","provincia":"Bolívar","nbi_pct":61.5},
        "0202":{"canton":"Chillanes","provincia":"Bolívar","nbi_pct":71.8},
        "0203":{"canton":"Chimbo","provincia":"Bolívar","nbi_pct":58.5},
        "0204":{"canton":"Echeandía","provincia":"Bolívar","nbi_pct":43.6},
        "0205":{"canton":"San Miguel","provincia":"Bolívar","nbi_pct":57.7},
        "0206":{"canton":"Caluma","provincia":"Bolívar","nbi_pct":40.4},
        "0207":{"canton":"Las Naves","provincia":"Bolívar","nbi_pct":54.9},
        "0301":{"canton":"Azogues","provincia":"Cañar","nbi_pct":26.5},
        "0302":{"canton":"Biblián","provincia":"Cañar","nbi_pct":43.3},
        "0303":{"canton":"Cañar","provincia":"Cañar","nbi_pct":46.7},
        "0304":{"canton":"La Troncal","provincia":"Cañar","nbi_pct":45.4},
        "0305":{"canton":"El Tambo","provincia":"Cañar","nbi_pct":34.6},
        "0306":{"canton":"Déleg","provincia":"Cañar","nbi_pct":43.5},
        "0307":{"canton":"Suscal","provincia":"Cañar","nbi_pct":61.5},
        "0401":{"canton":"Tulcán","provincia":"Carchi","nbi_pct":29.6},
        "0402":{"canton":"Bolívar","provincia":"Carchi","nbi_pct":40.4},
        "0403":{"canton":"Espejo","provincia":"Carchi","nbi_pct":37.6},
        "0404":{"canton":"Mira","provincia":"Carchi","nbi_pct":44.9},
        "0405":{"canton":"Montúfar","provincia":"Carchi","nbi_pct":34.7},
        "0406":{"canton":"San Pedro de Huaca","provincia":"Carchi","nbi_pct":31.3},
        "0501":{"canton":"Latacunga","provincia":"Cotopaxi","nbi_pct":38.1},
        "0502":{"canton":"La Maná","provincia":"Cotopaxi","nbi_pct":46.2},
        "0503":{"canton":"Pangua","provincia":"Cotopaxi","nbi_pct":69.0},
        "0504":{"canton":"Pujilí","provincia":"Cotopaxi","nbi_pct":64.5},
        "0505":{"canton":"Salcedo","provincia":"Cotopaxi","nbi_pct":48.8},
        "0506":{"canton":"Saquisilí","provincia":"Cotopaxi","nbi_pct":56.6},
        "0507":{"canton":"Sigchos","provincia":"Cotopaxi","nbi_pct":82.5},
        "0601":{"canton":"Riobamba","provincia":"Chimborazo","nbi_pct":25.3},
        "0602":{"canton":"Alausí","provincia":"Chimborazo","nbi_pct":74.2},
        "0603":{"canton":"Colta","provincia":"Chimborazo","nbi_pct":81.3},
        "0604":{"canton":"Chambo","provincia":"Chimborazo","nbi_pct":37.3},
        "0605":{"canton":"Chunchi","provincia":"Chimborazo","nbi_pct":53.9},
        "0606":{"canton":"Guamote","provincia":"Chimborazo","nbi_pct":88.5},
        "0607":{"canton":"Guano","provincia":"Chimborazo","nbi_pct":49.4},
        "0608":{"canton":"Pallatanga","provincia":"Chimborazo","nbi_pct":64.8},
        "0609":{"canton":"Penipe","provincia":"Chimborazo","nbi_pct":49.1},
        "0610":{"canton":"Cumandá","provincia":"Chimborazo","nbi_pct":36.2},
        "0701":{"canton":"Machala","provincia":"El Oro","nbi_pct":33.5},
        "0702":{"canton":"Arenillas","provincia":"El Oro","nbi_pct":39.7},
        "0703":{"canton":"Atahualpa","provincia":"El Oro","nbi_pct":40.4},
        "0704":{"canton":"Balsas","provincia":"El Oro","nbi_pct":51.5},
        "0705":{"canton":"Chilla","provincia":"El Oro","nbi_pct":62.6},
        "0706":{"canton":"El Guabo","provincia":"El Oro","nbi_pct":52.4},
        "0707":{"canton":"Huaquillas","provincia":"El Oro","nbi_pct":41.3},
        "0708":{"canton":"Marcabelí","provincia":"El Oro","nbi_pct":29.0},
        "0709":{"canton":"Pasaje","provincia":"El Oro","nbi_pct":35.8},
        "0710":{"canton":"Piñas","provincia":"El Oro","nbi_pct":35.7},
        "0711":{"canton":"Portovelo","provincia":"El Oro","nbi_pct":31.2},
        "0712":{"canton":"Santa Rosa","provincia":"El Oro","nbi_pct":30.3},
        "0713":{"canton":"Zaruma","provincia":"El Oro","nbi_pct":43.1},
        "0714":{"canton":"Las Lajas","provincia":"El Oro","nbi_pct":37.1},
        "0801":{"canton":"Esmeraldas","provincia":"Esmeraldas","nbi_pct":38.4},
        "0802":{"canton":"Eloy Alfaro","provincia":"Esmeraldas","nbi_pct":87.6},
        "0803":{"canton":"Muisne","provincia":"Esmeraldas","nbi_pct":92.3},
        "0804":{"canton":"Quinindé","provincia":"Esmeraldas","nbi_pct":71.4},
        "0805":{"canton":"San Lorenzo","provincia":"Esmeraldas","nbi_pct":73.8},
        "0806":{"canton":"Atacames","provincia":"Esmeraldas","nbi_pct":71.0},
        "0807":{"canton":"Rioverde","provincia":"Esmeraldas","nbi_pct":92.0},
        "0808":{"canton":"La Concordia","provincia":"Esmeraldas","nbi_pct":61.0},
        "0901":{"canton":"Guayaquil","provincia":"Guayas","nbi_pct":28.7},
        "0902":{"canton":"Alfredo Baquerizo Moreno","provincia":"Guayas","nbi_pct":84.1},
        "0903":{"canton":"Balao","provincia":"Guayas","nbi_pct":46.7},
        "0904":{"canton":"Balzar","provincia":"Guayas","nbi_pct":79.3},
        "0905":{"canton":"Colimes","provincia":"Guayas","nbi_pct":80.7},
        "0906":{"canton":"Daule","provincia":"Guayas","nbi_pct":34.6},
        "0907":{"canton":"Durán","provincia":"Guayas","nbi_pct":65.4},
        "0908":{"canton":"El Empalme","provincia":"Guayas","nbi_pct":71.5},
        "0909":{"canton":"El Triunfo","provincia":"Guayas","nbi_pct":56.1},
        "0910":{"canton":"Milagro","provincia":"Guayas","nbi_pct":45.5},
        "0911":{"canton":"Naranjal","provincia":"Guayas","nbi_pct":53.5},
        "0912":{"canton":"Naranjito","provincia":"Guayas","nbi_pct":45.1},
        "0913":{"canton":"Palestina","provincia":"Guayas","nbi_pct":67.4},
        "0914":{"canton":"Pedro Carbo","provincia":"Guayas","nbi_pct":72.2},
        "0915":{"canton":"Samborondón","provincia":"Guayas","nbi_pct":32.1},
        "0916":{"canton":"Santa Lucía","provincia":"Guayas","nbi_pct":74.2},
        "0917":{"canton":"Salitre","provincia":"Guayas","nbi_pct":88.9},
        "0918":{"canton":"San Jacinto de Yaguachi","provincia":"Guayas","nbi_pct":58.1},
        "0919":{"canton":"Playas","provincia":"Guayas","nbi_pct":48.1},
        "0920":{"canton":"Simón Bolívar","provincia":"Guayas","nbi_pct":72.0},
        "0921":{"canton":"Coronel Marcelino Maridueña","provincia":"Guayas","nbi_pct":39.8},
        "0922":{"canton":"Lomas de Sargentillo","provincia":"Guayas","nbi_pct":58.2},
        "0923":{"canton":"Nobol","provincia":"Guayas","nbi_pct":48.6},
        "0924":{"canton":"General Antonio Elizalde","provincia":"Guayas","nbi_pct":46.5},
        "0925":{"canton":"Isidro Ayora","provincia":"Guayas","nbi_pct":77.5},
        "0926":{"canton":"Balzar","provincia":"Guayas","nbi_pct":79.3},
        "0927":{"canton":"General Antonio Elizalde","provincia":"Guayas","nbi_pct":46.5},
        "1001":{"canton":"Ibarra","provincia":"Imbabura","nbi_pct":20.7},
        "1002":{"canton":"Antonio Ante","provincia":"Imbabura","nbi_pct":27.3},
        "1003":{"canton":"Cotacachi","provincia":"Imbabura","nbi_pct":54.8},
        "1004":{"canton":"Otavalo","provincia":"Imbabura","nbi_pct":44.5},
        "1005":{"canton":"Pimampiro","provincia":"Imbabura","nbi_pct":42.5},
        "1006":{"canton":"San Miguel de Urcuquí","provincia":"Imbabura","nbi_pct":45.4},
        "1101":{"canton":"Loja","provincia":"Loja","nbi_pct":24.4},
        "1102":{"canton":"Calvas","provincia":"Loja","nbi_pct":49.7},
        "1103":{"canton":"Catamayo","provincia":"Loja","nbi_pct":34.6},
        "1104":{"canton":"Celica","provincia":"Loja","nbi_pct":59.6},
        "1105":{"canton":"Chaguarpamba","provincia":"Loja","nbi_pct":57.4},
        "1106":{"canton":"Espíndola","provincia":"Loja","nbi_pct":71.3},
        "1107":{"canton":"Gonzanamá","provincia":"Loja","nbi_pct":63.2},
        "1108":{"canton":"Macará","provincia":"Loja","nbi_pct":45.2},
        "1109":{"canton":"Paltas","provincia":"Loja","nbi_pct":57.0},
        "1110":{"canton":"Pindal","provincia":"Loja","nbi_pct":72.4},
        "1111":{"canton":"Puyango","provincia":"Loja","nbi_pct":47.0},
        "1112":{"canton":"Saraguro","provincia":"Loja","nbi_pct":64.7},
        "1113":{"canton":"Sozoranga","provincia":"Loja","nbi_pct":78.3},
        "1114":{"canton":"Zapotillo","provincia":"Loja","nbi_pct":59.1},
        "1115":{"canton":"Olmedo","provincia":"Loja","nbi_pct":63.6},
        "1116":{"canton":"Quilanga","provincia":"Loja","nbi_pct":64.6},
        "1201":{"canton":"Babahoyo","provincia":"Los Ríos","nbi_pct":54.1},
        "1202":{"canton":"Baba","provincia":"Los Ríos","nbi_pct":77.7},
        "1203":{"canton":"Montalvo","provincia":"Los Ríos","nbi_pct":51.5},
        "1204":{"canton":"Puebloviejo","provincia":"Los Ríos","nbi_pct":63.8},
        "1205":{"canton":"Quevedo","provincia":"Los Ríos","nbi_pct":50.8},
        "1206":{"canton":"Urdaneta","provincia":"Los Ríos","nbi_pct":76.1},
        "1207":{"canton":"Ventanas","provincia":"Los Ríos","nbi_pct":64.6},
        "1208":{"canton":"Vinces","provincia":"Los Ríos","nbi_pct":68.4},
        "1209":{"canton":"Palenque","provincia":"Los Ríos","nbi_pct":83.0},
        "1210":{"canton":"Buena Fe","provincia":"Los Ríos","nbi_pct":51.3},
        "1211":{"canton":"Valencia","provincia":"Los Ríos","nbi_pct":82.3},
        "1212":{"canton":"Mocache","provincia":"Los Ríos","nbi_pct":74.0},
        "1213":{"canton":"Quinsaloma","provincia":"Los Ríos","nbi_pct":72.9},
        "1301":{"canton":"Portoviejo","provincia":"Manabí","nbi_pct":43.2},
        "1302":{"canton":"Bolívar","provincia":"Manabí","nbi_pct":77.4},
        "1303":{"canton":"Chone","provincia":"Manabí","nbi_pct":68.9},
        "1304":{"canton":"El Carmen","provincia":"Manabí","nbi_pct":70.6},
        "1305":{"canton":"Flavio Alfaro","provincia":"Manabí","nbi_pct":85.2},
        "1306":{"canton":"Jipijapa","provincia":"Manabí","nbi_pct":72.8},
        "1307":{"canton":"Junín","provincia":"Manabí","nbi_pct":75.4},
        "1308":{"canton":"Manta","provincia":"Manabí","nbi_pct":32.4},
        "1309":{"canton":"Montecristi","provincia":"Manabí","nbi_pct":78.8},
        "1310":{"canton":"Paján","provincia":"Manabí","nbi_pct":89.0},
        "1311":{"canton":"Pichincha","provincia":"Manabí","nbi_pct":86.1},
        "1312":{"canton":"Rocafuerte","provincia":"Manabí","nbi_pct":51.8},
        "1313":{"canton":"Santa Ana","provincia":"Manabí","nbi_pct":72.8},
        "1314":{"canton":"Sucre","provincia":"Manabí","nbi_pct":66.0},
        "1315":{"canton":"Tosagua","provincia":"Manabí","nbi_pct":62.7},
        "1316":{"canton":"24 de Mayo","provincia":"Manabí","nbi_pct":85.4},
        "1317":{"canton":"Pedernales","provincia":"Manabí","nbi_pct":79.3},
        "1318":{"canton":"Olmedo","provincia":"Manabí","nbi_pct":93.6},
        "1319":{"canton":"Puerto López","provincia":"Manabí","nbi_pct":73.0},
        "1320":{"canton":"Jama","provincia":"Manabí","nbi_pct":67.3},
        "1321":{"canton":"Jaramijó","provincia":"Manabí","nbi_pct":56.0},
        "1322":{"canton":"San Vicente","provincia":"Manabí","nbi_pct":74.8},
        "1401":{"canton":"Morona","provincia":"Morona Santiago","nbi_pct":53.2},
        "1402":{"canton":"Gualaquiza","provincia":"Morona Santiago","nbi_pct":56.5},
        "1403":{"canton":"Limón Indanza","provincia":"Morona Santiago","nbi_pct":59.0},
        "1404":{"canton":"Palora","provincia":"Morona Santiago","nbi_pct":54.0},
        "1405":{"canton":"Santiago","provincia":"Morona Santiago","nbi_pct":60.5},
        "1406":{"canton":"Sucúa","provincia":"Morona Santiago","nbi_pct":51.6},
        "1407":{"canton":"Huamboya","provincia":"Morona Santiago","nbi_pct":87.7},
        "1408":{"canton":"San Juan Bosco","provincia":"Morona Santiago","nbi_pct":59.3},
        "1409":{"canton":"Taisha","provincia":"Morona Santiago","nbi_pct":96.9},
        "1410":{"canton":"Logroño","provincia":"Morona Santiago","nbi_pct":83.0},
        "1411":{"canton":"Pablo Sexto","provincia":"Morona Santiago","nbi_pct":57.9},
        "1412":{"canton":"Tiwintza","provincia":"Morona Santiago","nbi_pct":93.4},
        "1501":{"canton":"Tena","provincia":"Napo","nbi_pct":60.8},
        "1502":{"canton":"Archidona","provincia":"Napo","nbi_pct":77.5},
        "1503":{"canton":"El Chaco","provincia":"Napo","nbi_pct":37.8},
        "1504":{"canton":"Quijos","provincia":"Napo","nbi_pct":39.8},
        "1505":{"canton":"Carlos Julio Arosemena Tola","provincia":"Napo","nbi_pct":53.8},
        "1601":{"canton":"Pastaza","provincia":"Pastaza","nbi_pct":49.5},
        "1602":{"canton":"Mera","provincia":"Pastaza","nbi_pct":51.2},
        "1603":{"canton":"Santa Clara","provincia":"Pastaza","nbi_pct":49.1},
        "1604":{"canton":"Arajuno","provincia":"Pastaza","nbi_pct":87.4},
        "1701":{"canton":"Quito","provincia":"Pichincha","nbi_pct":13.7},
        "1702":{"canton":"Cayambe","provincia":"Pichincha","nbi_pct":35.4},
        "1703":{"canton":"Mejía","provincia":"Pichincha","nbi_pct":26.1},
        "1704":{"canton":"Pedro Moncayo","provincia":"Pichincha","nbi_pct":38.3},
        "1705":{"canton":"Rumiñahui","provincia":"Pichincha","nbi_pct":11.4},
        "1706":{"canton":"San Miguel de los Bancos","provincia":"Pichincha","nbi_pct":42.8},
        "1707":{"canton":"Pedro Vicente Maldonado","provincia":"Pichincha","nbi_pct":52.9},
        "1709":{"canton":"Puerto Quito","provincia":"Pichincha","nbi_pct":67.1},
        "1801":{"canton":"Ambato","provincia":"Tungurahua","nbi_pct":26.1},
        "1802":{"canton":"Baños de Agua Santa","provincia":"Tungurahua","nbi_pct":22.4},
        "1803":{"canton":"Cevallos","provincia":"Tungurahua","nbi_pct":23.3},
        "1804":{"canton":"Mocha","provincia":"Tungurahua","nbi_pct":31.2},
        "1805":{"canton":"Patate","provincia":"Tungurahua","nbi_pct":53.5},
        "1806":{"canton":"Quero","provincia":"Tungurahua","nbi_pct":54.2},
        "1807":{"canton":"San Pedro de Pelileo","provincia":"Tungurahua","nbi_pct":44.4},
        "1808":{"canton":"Santiago de Píllaro","provincia":"Tungurahua","nbi_pct":45.8},
        "1809":{"canton":"Tisaleo","provincia":"Tungurahua","nbi_pct":40.7},
        "1901":{"canton":"Zamora","provincia":"Zamora Chinchipe","nbi_pct":36.2},
        "1902":{"canton":"Chinchipe","provincia":"Zamora Chinchipe","nbi_pct":59.9},
        "1903":{"canton":"Nangaritza","provincia":"Zamora Chinchipe","nbi_pct":56.5},
        "1904":{"canton":"Yacuambi","provincia":"Zamora Chinchipe","nbi_pct":68.9},
        "1905":{"canton":"Yantzaza","provincia":"Zamora Chinchipe","nbi_pct":47.2},
        "1906":{"canton":"El Pangui","provincia":"Zamora Chinchipe","nbi_pct":50.2},
        "1907":{"canton":"Centinela del Cóndor","provincia":"Zamora Chinchipe","nbi_pct":52.7},
        "1908":{"canton":"Palanda","provincia":"Zamora Chinchipe","nbi_pct":66.0},
        "1909":{"canton":"Paquisha","provincia":"Zamora Chinchipe","nbi_pct":62.9},
        "2001":{"canton":"San Cristóbal","provincia":"Galápagos","nbi_pct":21.2},
        "2002":{"canton":"Isabela","provincia":"Galápagos","nbi_pct":30.1},
        "2003":{"canton":"Santa Cruz","provincia":"Galápagos","nbi_pct":36.5},
        "2101":{"canton":"Lago Agrio","provincia":"Sucumbíos","nbi_pct":54.9},
        "2102":{"canton":"Gonzalo Pizarro","provincia":"Sucumbíos","nbi_pct":54.6},
        "2103":{"canton":"Putumayo","provincia":"Sucumbíos","nbi_pct":80.6},
        "2104":{"canton":"Shushufindi","provincia":"Sucumbíos","nbi_pct":61.5},
        "2105":{"canton":"Sucumbíos","provincia":"Sucumbíos","nbi_pct":49.7},
        "2106":{"canton":"Cascales","provincia":"Sucumbíos","nbi_pct":64.9},
        "2107":{"canton":"Cuyabeno","provincia":"Sucumbíos","nbi_pct":76.0},
        "2201":{"canton":"Francisco de Orellana","provincia":"Orellana","nbi_pct":58.2},
        "2202":{"canton":"Aguarico","provincia":"Orellana","nbi_pct":81.3},
        "2203":{"canton":"La Joya de los Sachas","provincia":"Orellana","nbi_pct":78.1},
        "2204":{"canton":"Loreto","provincia":"Orellana","nbi_pct":83.9},
        "2301":{"canton":"Santo Domingo","provincia":"Santo Domingo de los Tsáchilas","nbi_pct":45.0},
        "2302":{"canton":"La Concordia","provincia":"Santo Domingo de los Tsáchilas","nbi_pct":61.0},
        "2401":{"canton":"Santa Elena","provincia":"Santa Elena","nbi_pct":50.7},
        "2402":{"canton":"La Libertad","provincia":"Santa Elena","nbi_pct":44.6},
        "2403":{"canton":"Salinas","provincia":"Santa Elena","nbi_pct":43.5},
    }
    return JsonResponse(NBI_DATA)


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
        primera_foto = p.fotoproyecto_set.first()
        foto_url = '/media/' + str(primera_foto.ruta_foto) if primera_foto else None
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [float(p.longitud), float(p.latitud)],
            },
            'properties': {
                'id':           p.id_proyecto,
                'codigo':       p.codigo,
                'nombre':       p.nombre,
                'nombre_corto': p.nombre_corto or p.nombre[:60],
                'facultad':     p.id_facultad.nombre,
                'carrera':      p.id_carrera.nombre,
                'periodo':      p.id_periodo_inicio.nombre,
                'estado':       p.estado,
                'color':        COLORES.get(p.estado, '#1b7505'),
                'provincia':    p.provincia or '',
                'canton':       p.canton or '',
                'parroquia':    p.parroquia or '',
                'fecha_inicio': str(p.fecha_inicio) if p.fecha_inicio else '',
                'ods':          p.ods or '',
                'foto_url':     foto_url,
                'url_editar':   f'/proyectos/{p.id_proyecto}/editar/',
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