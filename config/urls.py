from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from vinculacion import views


def svelte_redirect(request):
    return JsonResponse({'detail': 'Use the Svelte frontend at http://localhost:5173'}, status=200)


urlpatterns = [
    path('admin/', admin.site.urls),

    # Rutas de la API Svelte
    path('api/auth/login/',          views.api_login,             name='api_login'),
    path('api/auth/logout/',         views.api_logout,            name='api_logout'),
    path('api/auth/me/',             views.api_me,                name='api_me'),
    path('api/dashboard/stats/',     views.api_dashboard_stats,   name='api_dashboard_stats'),
    path('api/periodos/',            views.api_periodos,          name='api_periodos'),
    path('api/facultades/',          views.api_facultades,        name='api_facultades'),
    path('api/carreras/',            views.api_carreras,          name='api_carreras'),
    path('api/entidades/',           views.api_entidades,         name='api_entidades'),
    path('api/proyectos/',           views.api_proyectos,         name='api_proyectos'),
    path('api/convenios/',           views.api_convenios,         name='api_convenios'),
    path('api/docentes/',            views.api_docentes,          name='api_docentes'),
    path('api/mapa/proyectos/',      views.api_mapa_proyectos,    name='api_mapa_proyectos'),
    path('api/mapa/anios/',          views.api_mapa_anios,        name='api_mapa_anios'),
    path('api/carreras-por-facultad/', views.carrera_por_facultad, name='carrera_por_facultad'),
    path('api/proyectos/<int:id>/detalle/', views.api_proyecto_detalle, name='api_proyecto_detalle'),
    path('api/capa-pobreza/',        views.api_capa_pobreza,      name='api_capa_pobreza'),

    # CRUD
    path('api/periodos/create/',        views.api_periodos_post,          name='api_periodos_post'),
    path('api/periodos/<int:id>/',      views.api_periodo_detail,          name='api_periodo_detail'),
    path('api/facultades/<int:id>/',    views.api_facultad_detail,         name='api_facultad_detail'),
    path('api/carreras/create/',        views.api_carreras_post,           name='api_carreras_post'),
    path('api/carreras/<int:id>/',      views.api_carrera_detail,          name='api_carrera_detail'),
    path('api/entidades/create/',       views.api_entidades_post,          name='api_entidades_post'),
    path('api/entidades/<int:id>/',     views.api_entidad_detail,          name='api_entidad_detail'),
    path('api/proyectos/create/',       views.api_proyecto_create,         name='api_proyecto_create'),
    path('api/proyectos/<int:id>/edit/', views.api_proyecto_update,        name='api_proyecto_update'),
    path('api/proyectos/fotos/<int:id_foto>/', views.api_proyecto_eliminar_foto, name='api_foto_eliminar'),
    path('api/convenios/list/',         views.api_convenios_post,          name='api_convenios_post'),
    path('api/convenios/create/',       views.api_convenios_post,          name='api_convenio_create'),
    path('api/convenios/<int:id>/',     views.api_convenio_detail,         name='api_convenio_detail'),
    path('api/convenios/<int:id>/anexos/', views.api_convenio_anexo_subir, name='api_convenio_anexo'),
    path('api/anexos/<int:id_anexo>/', views.api_anexo_eliminar,           name='api_anexo_eliminar'),
    path('api/reportes/stats/',         views.api_reportes_stats,          name='api_reportes_stats'),

    # Cualquier otra ruta → mensaje amigable
    path('',        svelte_redirect),
    path('login/',  svelte_redirect, name='login'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
