from vinculacion.models import PeriodoAcademico


def periodo_activo(request):
    if not request.session.get('usuario_id'):
        return {}
    try:
        periodo = PeriodoAcademico.objects.filter(activo=True).order_by('-fecha_inicio').first()
        todos = list(PeriodoAcademico.objects.order_by('-fecha_inicio').values(
            'id_periodo', 'codigo', 'nombre', 'activo', 'fecha_inicio', 'fecha_fin'
        ))
        return {'periodo_activo': periodo, 'todos_periodos': todos}
    except Exception:
        return {'periodo_activo': None, 'todos_periodos': []}
