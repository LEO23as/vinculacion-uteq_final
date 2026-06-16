from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from vinculacion import views
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cambiar-clave/', views.cambiar_clave_view, name='cambiar_clave'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    # Periodos
    path('periodos/', views.periodos_lista, name='periodos_lista'),
    path('periodos/nuevo/', views.periodo_nuevo, name='periodo_nuevo'),
    path('periodos/<int:id>/editar/', views.periodo_editar, name='periodo_editar'),
    path('periodos/<int:id>/toggle/', views.periodo_toggle, name='periodo_toggle'),
    # Facultades y carreras
    path('facultades/', views.facultades_lista, name='facultades_lista'),
    path('facultades/<int:id>/editar/', views.facultad_editar, name='facultad_editar'),
    path('facultades/<int:id>/toggle/', views.facultad_toggle, name='facultad_toggle'),
    path('carreras/', views.carreras_lista, name='carreras_lista'),
    path('carreras/nueva/', views.carrera_nueva, name='carrera_nueva'),
    path('carreras/<int:id>/editar/', views.carrera_editar, name='carrera_editar'),
    path('carreras/<int:id>/toggle/', views.carrera_toggle, name='carrera_toggle'),
    # Entidades Cooperantes
    path('entidades/', views.entidades_lista, name='entidades_lista'),
    path('entidades/nueva/', views.entidad_nueva, name='entidad_nueva'),
    path('entidades/<int:id>/editar/', views.entidad_editar, name='entidad_editar'),
    path('entidades/<int:id>/toggle/', views.entidad_toggle, name='entidad_toggle'),

    # Proyectos
    path('proyectos/', views.proyectos_lista, name='proyectos_lista'),
    path('proyectos/nuevo/', views.proyecto_nuevo, name='proyecto_nuevo'),
    path('proyectos/<int:id>/editar/', views.proyecto_editar, name='proyecto_editar'),
    path('proyectos/<int:id>/toggle/', views.proyecto_toggle, name='proyecto_toggle'),
    path('api/carreras-por-facultad/', views.carrera_por_facultad, name='carrera_por_facultad'),
    path('proyectos/<int:foto_id>/eliminar-foto/', views.proyecto_eliminar_foto, name='proyecto_eliminar_foto'),


# ── Añadir estas 3 líneas en urlpatterns dentro de config/urls.py ──
# (después de las URLs de proyectos, antes del cierre de la lista)

path('mapa/', views.mapa_view, name='mapa'),
path('api/mapa/proyectos/', views.api_mapa_proyectos, name='api_mapa_proyectos'),
path('api/mapa/anios/', views.api_mapa_anios, name='api_mapa_anios'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)