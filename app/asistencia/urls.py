from django.urls import path

from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Empleados
    path('empleados/', views.empleados_lista, name='empleados_lista'),
    path('empleados/crear/', views.empleados_crear, name='empleados_crear'),
    path('empleados/<int:pk>/editar/', views.empleados_editar, name='empleados_editar'),
    path('empleados/<int:pk>/eliminar/', views.empleados_eliminar, name='empleados_eliminar'),
    path('empleados/<int:pk>/activar/', views.empleados_activar, name='empleados_activar'),

    # Estados de Asistencia
    path('estados/', views.estados_lista, name='estados_lista'),
    path('estados/crear/', views.estados_crear, name='estados_crear'),
    path('estados/<int:pk>/editar/', views.estados_editar, name='estados_editar'),
    path('estados/<int:pk>/eliminar/', views.estados_eliminar, name='estados_eliminar'),

    # Asistencia
    path('asistencia/', views.asistencia_redirigir, name='asistencia'),
    path('asistencia/guardar/', views.asistencia_guardar, name='asistencia_guardar'),
    path('asistencia/<int:anio>/<int:mes>/', views.asistencia_grilla, name='asistencia_grilla'),
]
