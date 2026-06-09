from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from vinculacion.models import Usuario, PeriodoAcademico
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