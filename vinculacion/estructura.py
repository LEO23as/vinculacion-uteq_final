"""
Versionado temporal de la estructura académica (facultades y carreras).

Responsabilidad única de este módulo: mantener un snapshot inmutable de cómo
lucía la estructura académica en cada período, más una bitácora de auditoría
de los cambios confirmados al crear un período nuevo.

Flujo de datos:
    facultad / carrera            -> identidad canónica (id estable)
    facultad_periodo / carrera_periodo -> foto histórica por período
    estructura_cambio             -> bitácora de la reconciliación

Puntos de entrada (endpoints al final del archivo):
    GET  /api/estructura/periodo/<id>/        -> snapshot de un período
    GET  /api/estructura/comparar/?ref=<id>   -> diff para el wizard
    POST /api/estructura/periodo/<id>/confirmar/ -> persistir snapshot + auditoría
    GET  /api/facultades-periodo/?periodo=<id>   -> facultades vigentes en el período
    GET  /api/carreras-periodo/?periodo=<id>&facultad=<id>
    GET  /api/estructura/historial/           -> bitácora de cambios
"""
import json

from django.db import connection, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import (
    Facultad, Carrera, PeriodoAcademico,
    FacultadPeriodo, CarreraPeriodo, EstructuraCambio,
)


# ── Utilidades ──────────────────────────────────────────────────────────────

def _auth(request):
    return request.session.get('usuario_id')


def _periodo_referencia(periodo_nuevo):
    """
    Devuelve el período con snapshot más reciente que precede al período dado
    (por fecha de inicio). Es la base contra la que se reconcilian los cambios.
    """
    con_snapshot = (
        FacultadPeriodo.objects
        .values_list('id_periodo', flat=True)
        .distinct()
    )
    qs = (
        PeriodoAcademico.objects
        .filter(id_periodo__in=list(con_snapshot))
        .exclude(id_periodo=periodo_nuevo.id_periodo)
        .filter(fecha_inicio__lte=periodo_nuevo.fecha_inicio)
        .order_by('-fecha_inicio')
    )
    return qs.first()


def _snapshot_periodo(periodo_id):
    """Estructura anidada facultad->carreras del snapshot de un período."""
    facs = (
        FacultadPeriodo.objects
        .filter(id_periodo=periodo_id)
        .order_by('nombre')
    )
    carreras = (
        CarreraPeriodo.objects
        .filter(id_periodo=periodo_id)
        .order_by('nombre')
    )
    car_por_fac = {}
    for c in carreras:
        car_por_fac.setdefault(c.id_facultad_periodo_id, []).append({
            'id_carrera_periodo': c.id_carrera_periodo,
            'id_carrera': c.id_carrera_id,
            'codigo': c.codigo,
            'nombre': c.nombre,
            'horas_vinculacion': c.horas_vinculacion,
            'vigente': c.vigente,
        })
    out = []
    for f in facs:
        out.append({
            'id_facultad_periodo': f.id_facultad_periodo,
            'id_facultad': f.id_facultad_id,
            'codigo': f.codigo,
            'nombre': f.nombre,
            'nombre_corto': f.nombre_corto,
            'campus': f.campus,
            'vigente': f.vigente,
            'carreras': car_por_fac.get(f.id_facultad_periodo, []),
        })
    return out


# ── Comparación / diff para el wizard ───────────────────────────────────────

def _construir_diff(periodo_nuevo):
    """
    Compara la estructura canónica ACTUAL contra el snapshot del período de
    referencia y produce la propuesta de reconciliación que consume el wizard.

    estado_sugerido por facultad/carrera:
        NUEVA       -> no existía snapshot en el período de referencia
        RENOMBRADA  -> el nombre canónico difiere del histórico
        SIN_CAMBIO  -> el nombre coincide
    """
    ref = _periodo_referencia(periodo_nuevo)

    # Snapshot de referencia indexado por identidad canónica
    ref_fac = {}
    ref_car = {}
    if ref:
        for f in FacultadPeriodo.objects.filter(id_periodo=ref.id_periodo):
            ref_fac[f.id_facultad_id] = f
        for c in CarreraPeriodo.objects.filter(id_periodo=ref.id_periodo):
            ref_car[c.id_carrera_id] = c

    carreras_por_fac = {}
    for c in Carrera.objects.filter(activo=True).select_related('id_facultad'):
        carreras_por_fac.setdefault(c.id_facultad_id, []).append(c)

    facultades = []
    for f in Facultad.objects.filter(activo=True).order_by('nombre'):
        rf = ref_fac.get(f.id_facultad)
        nombre_ref = rf.nombre if rf else None
        if rf is None:
            estado = 'NUEVA'
        elif rf.nombre != f.nombre or rf.codigo != f.codigo:
            estado = 'RENOMBRADA'
        else:
            estado = 'SIN_CAMBIO'

        carreras = []
        for c in carreras_por_fac.get(f.id_facultad, []):
            rc = ref_car.get(c.id_carrera)
            nombre_ref_c = rc.nombre if rc else None
            if rc is None:
                estado_c = 'NUEVA'
            elif rc.nombre != c.nombre:
                estado_c = 'RENOMBRADA'
            else:
                estado_c = 'SIN_CAMBIO'
            carreras.append({
                'id_carrera': c.id_carrera,
                'codigo': c.codigo,
                'nombre_referencia': nombre_ref_c,
                'nombre_actual': c.nombre,
                'nombre_sugerido': c.nombre,
                'horas_vinculacion': c.horas_vinculacion,
                'estado_sugerido': estado_c,
                'vigente': True,
            })

        facultades.append({
            'id_facultad': f.id_facultad,
            'codigo': f.codigo,
            'nombre_referencia': nombre_ref,
            'nombre_actual': f.nombre,
            'nombre_sugerido': f.nombre,
            'nombre_corto': f.nombre_corto,
            'campus': f.campus,
            'estado_sugerido': estado,
            'vigente': True,
            'carreras': carreras,
        })

    # Facultades que existían en referencia pero ya no están activas -> desaparecidas
    desaparecidas = []
    for id_fac, rf in ref_fac.items():
        if not Facultad.objects.filter(id_facultad=id_fac, activo=True).exists():
            desaparecidas.append({
                'id_facultad': id_fac,
                'codigo': rf.codigo,
                'nombre_referencia': rf.nombre,
                'nombre_actual': None,
                'nombre_sugerido': rf.nombre,
                'nombre_corto': rf.nombre_corto,
                'campus': rf.campus,
                'estado_sugerido': 'DESACTIVADA',
                'vigente': False,
                'carreras': [],
            })

    return {
        'periodo_referencia': None if not ref else {
            'id_periodo': ref.id_periodo,
            'codigo': ref.codigo,
            'nombre': ref.nombre,
        },
        'facultades': facultades + desaparecidas,
    }


# ── Persistencia del snapshot + auditoría ───────────────────────────────────

@transaction.atomic
def _guardar_snapshot(periodo, facultades_data, usuario_id):
    """
    Persiste (idempotente) el snapshot reconciliado del período y registra la
    bitácora de cambios. Actualiza el nombre canónico cuando hubo renombre,
    de modo que la identidad refleje siempre su denominación más reciente.
    """
    # Snapshot de referencia previo (para comparar y auditar)
    ref = _periodo_referencia(periodo)
    ref_fac = {}
    ref_car = {}
    if ref:
        for f in FacultadPeriodo.objects.filter(id_periodo=ref.id_periodo):
            ref_fac[f.id_facultad_id] = f.nombre
        for c in CarreraPeriodo.objects.filter(id_periodo=ref.id_periodo):
            ref_car[c.id_carrera_id] = c.nombre

    # Idempotencia: re-generar limpia el snapshot previo de ESTE período
    CarreraPeriodo.objects.filter(id_periodo=periodo.id_periodo).delete()
    FacultadPeriodo.objects.filter(id_periodo=periodo.id_periodo).delete()
    EstructuraCambio.objects.filter(id_periodo=periodo.id_periodo).delete()

    cambios = []
    total_fac = total_car = 0

    for fd in facultades_data:
        id_facultad = fd['id_facultad']
        nombre = (fd.get('nombre_sugerido') or fd.get('nombre') or '').strip()
        codigo = (fd.get('codigo') or '').strip()
        tipo_cambio = fd.get('tipo_cambio') or fd.get('estado_sugerido') or 'SIN_CAMBIO'
        vigente = bool(fd.get('vigente', True))

        fac_snap = FacultadPeriodo.objects.create(
            id_facultad_id=id_facultad,
            id_periodo=periodo,
            codigo=codigo,
            nombre=nombre,
            nombre_corto=fd.get('nombre_corto') or None,
            campus=fd.get('campus') or None,
            vigente=vigente,
        )
        total_fac += 1

        # Auditoría facultad
        nombre_ant = ref_fac.get(id_facultad)
        if tipo_cambio != 'SIN_CAMBIO' or (nombre_ant and nombre_ant != nombre):
            cambios.append(EstructuraCambio(
                id_periodo=periodo,
                entidad_tipo='FACULTAD',
                entidad_id=id_facultad,
                tipo_cambio=tipo_cambio,
                valor_anterior=nombre_ant,
                valor_nuevo=nombre,
                id_usuario_id=usuario_id,
            ))

        # Actualizar identidad canónica cuando hubo renombre
        if tipo_cambio == 'RENOMBRADA' and nombre:
            Facultad.objects.filter(id_facultad=id_facultad).update(nombre=nombre)

        for cd in fd.get('carreras', []):
            id_carrera = cd['id_carrera']
            nombre_c = (cd.get('nombre_sugerido') or cd.get('nombre') or '').strip()
            tipo_c = cd.get('tipo_cambio') or cd.get('estado_sugerido') or 'SIN_CAMBIO'
            vigente_c = bool(cd.get('vigente', True))

            CarreraPeriodo.objects.create(
                id_carrera_id=id_carrera,
                id_facultad_periodo=fac_snap,
                id_periodo=periodo,
                codigo=cd.get('codigo') or None,
                nombre=nombre_c,
                horas_vinculacion=cd.get('horas_vinculacion') or 160,
                vigente=vigente_c,
            )
            total_car += 1

            nombre_ant_c = ref_car.get(id_carrera)
            if tipo_c != 'SIN_CAMBIO' or (nombre_ant_c and nombre_ant_c != nombre_c):
                cambios.append(EstructuraCambio(
                    id_periodo=periodo,
                    entidad_tipo='CARRERA',
                    entidad_id=id_carrera,
                    tipo_cambio=tipo_c,
                    valor_anterior=nombre_ant_c,
                    valor_nuevo=nombre_c,
                    id_usuario_id=usuario_id,
                ))
            if tipo_c == 'RENOMBRADA' and nombre_c:
                Carrera.objects.filter(id_carrera=id_carrera).update(nombre=nombre_c)

    if cambios:
        EstructuraCambio.objects.bulk_create(cambios)

    return {'facultades': total_fac, 'carreras': total_car, 'cambios': len(cambios)}


def _snapshot_desde_canonico(periodo, usuario_id=None):
    """
    Genera el snapshot de un período directamente desde la estructura canónica
    actual (sin reconciliación). Se usa para el backfill del período existente.
    """
    facultades_data = []
    carreras_por_fac = {}
    for c in Carrera.objects.filter(activo=True):
        carreras_por_fac.setdefault(c.id_facultad_id, []).append({
            'id_carrera': c.id_carrera,
            'codigo': c.codigo,
            'nombre': c.nombre,
            'horas_vinculacion': c.horas_vinculacion,
            'vigente': True,
            'tipo_cambio': 'SIN_CAMBIO',
        })
    for f in Facultad.objects.filter(activo=True):
        facultades_data.append({
            'id_facultad': f.id_facultad,
            'codigo': f.codigo,
            'nombre': f.nombre,
            'nombre_corto': f.nombre_corto,
            'campus': f.campus,
            'vigente': True,
            'tipo_cambio': 'SIN_CAMBIO',
            'carreras': carreras_por_fac.get(f.id_facultad, []),
        })
    return _guardar_snapshot(periodo, facultades_data, usuario_id)


# ── ENDPOINTS ───────────────────────────────────────────────────────────────

@csrf_exempt
def api_estructura_periodo(request, id):
    """GET: snapshot completo (facultades + carreras) de un período."""
    if not _auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    periodo = PeriodoAcademico.objects.filter(id_periodo=id).first()
    if not periodo:
        return JsonResponse({'error': 'Período no encontrado'}, status=404)
    return JsonResponse({
        'periodo': {'id_periodo': periodo.id_periodo, 'codigo': periodo.codigo, 'nombre': periodo.nombre},
        'tiene_snapshot': FacultadPeriodo.objects.filter(id_periodo=id).exists(),
        'facultades': _snapshot_periodo(id),
    })


@csrf_exempt
def api_estructura_comparar(request, id):
    """GET: diff de reconciliación entre la estructura actual y el período de referencia."""
    if not _auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    periodo = PeriodoAcademico.objects.filter(id_periodo=id).first()
    if not periodo:
        return JsonResponse({'error': 'Período no encontrado'}, status=404)
    return JsonResponse(_construir_diff(periodo))


@csrf_exempt
def api_estructura_confirmar(request, id):
    """POST: persiste el snapshot reconciliado del período + bitácora."""
    if not _auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    periodo = PeriodoAcademico.objects.filter(id_periodo=id).first()
    if not periodo:
        return JsonResponse({'error': 'Período no encontrado'}, status=404)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    facultades = data.get('facultades')
    if not isinstance(facultades, list) or not facultades:
        return JsonResponse({'error': 'Debe enviar la lista de facultades'}, status=400)
    try:
        resumen = _guardar_snapshot(periodo, facultades, _auth(request))
        return JsonResponse({'ok': True, 'resumen': resumen}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def api_facultades_periodo(request):
    """GET ?periodo=<id>: facultades vigentes en el período (para formularios)."""
    if not _auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    periodo_id = request.GET.get('periodo')
    if not periodo_id:
        return JsonResponse({'error': 'Falta parámetro periodo'}, status=400)
    qs = (
        FacultadPeriodo.objects
        .filter(id_periodo=periodo_id, vigente=True)
        .order_by('nombre')
    )
    data = [{
        'id_facultad': f.id_facultad_id,
        'id_facultad_periodo': f.id_facultad_periodo,
        'codigo': f.codigo,
        'nombre': f.nombre,
        'nombre_corto': f.nombre_corto,
    } for f in qs]
    # Fallback: si el período no tiene snapshot, devolver estructura canónica
    if not data:
        data = [{
            'id_facultad': f.id_facultad,
            'id_facultad_periodo': None,
            'codigo': f.codigo,
            'nombre': f.nombre,
            'nombre_corto': f.nombre_corto,
        } for f in Facultad.objects.filter(activo=True).order_by('nombre')]
    return JsonResponse(data, safe=False)


@csrf_exempt
def api_carreras_periodo(request):
    """GET ?periodo=<id>&facultad=<id>: carreras vigentes en el período."""
    if not _auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    periodo_id = request.GET.get('periodo')
    facultad_id = request.GET.get('facultad')
    if not periodo_id:
        return JsonResponse({'error': 'Falta parámetro periodo'}, status=400)
    qs = CarreraPeriodo.objects.filter(id_periodo=periodo_id, vigente=True)
    if facultad_id:
        qs = qs.filter(id_facultad_periodo__id_facultad=facultad_id)
    qs = qs.order_by('nombre')
    data = [{
        'id_carrera': c.id_carrera_id,
        'id_carrera_periodo': c.id_carrera_periodo,
        'codigo': c.codigo,
        'nombre': c.nombre,
        'horas_vinculacion': c.horas_vinculacion,
    } for c in qs]
    if not data:
        cq = Carrera.objects.filter(activo=True)
        if facultad_id:
            cq = cq.filter(id_facultad=facultad_id)
        data = [{
            'id_carrera': c.id_carrera,
            'id_carrera_periodo': None,
            'codigo': c.codigo,
            'nombre': c.nombre,
            'horas_vinculacion': c.horas_vinculacion,
        } for c in cq.order_by('nombre')]
    return JsonResponse(data, safe=False)


@csrf_exempt
def api_estructura_historial(request):
    """GET: bitácora de cambios estructurales, agrupada por período."""
    if not _auth(request):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    rows = []
    sql = """
        SELECT ec.id_cambio, ec.entidad_tipo, ec.entidad_id, ec.tipo_cambio,
               ec.valor_anterior, ec.valor_nuevo, ec.creado_en,
               p.id_periodo, p.codigo, p.nombre AS periodo_nombre,
               u.nombres AS usuario_nombre
        FROM estructura_cambio ec
        JOIN periodo_academico p ON p.id_periodo = ec.id_periodo
        LEFT JOIN usuario u ON u.id_usuario = ec.id_usuario
        ORDER BY ec.creado_en DESC, ec.id_cambio DESC
    """
    with connection.cursor() as cur:
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        for r in cur.fetchall():
            rows.append(dict(zip(cols, r)))
    for r in rows:
        if r.get('creado_en') is not None:
            r['creado_en'] = r['creado_en'].isoformat()
    return JsonResponse(rows, safe=False)
