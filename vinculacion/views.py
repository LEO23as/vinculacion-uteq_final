from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from vinculacion.models import Usuario, PeriodoAcademico
from vinculacion.utils import verificar_password
from django.conf import settings

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
    return render(request, 'dashboard.html', {
        'usuario_nombre': request.session.get('usuario_nombre'),
        'usuario_rol': request.session.get('usuario_rol'),
    })


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

from vinculacion.models import Facultad, Carrera

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

# ── ENTIDADES COOPERANTES ──────────────────────────────────────────

from vinculacion.models import EntidadCooperante, TipoEntidad

def entidades_lista(request):
    entidades = EntidadCooperante.objects.select_related('id_tipo').all().order_by('nombre')
    tipos = TipoEntidad.objects.all().order_by('nombre')
    
    # Filtros
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

from vinculacion.models import Proyecto, FotoProyecto

ESTADOS_PROYECTO = ['EN_EJECUCION', 'PROPUESTO', 'APROBADO', 'EN_CIERRE', 'DETENIDO', 'FINALIZADO', 'RECHAZADO', 'SUSPENDIDO']

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
        proyectos = proyectos.filter(nombre__icontains=busqueda) | \
                    proyectos.filter(codigo__icontains=busqueda)

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
    """Guarda las fotos subidas asociadas a un proyecto."""
    fotos = request.FILES.getlist('fotos')
    for foto in fotos:
        import os
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
    import os
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


def carrera_por_facultad(request):
    from django.http import JsonResponse
    id_facultad = request.GET.get('facultad_id')
    carreras = Carrera.objects.filter(
        id_facultad=id_facultad, activo=True
    ).order_by('nombre').values('id_carrera', 'nombre')
    return JsonResponse(list(carreras), safe=False)