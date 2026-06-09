from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from vinculacion import views

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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)