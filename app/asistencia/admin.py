from django.contrib import admin

from .models import Empleado, EstadoAsistencia, RegistroAsistencia


@admin.register(EstadoAsistencia)
class EstadoAsistenciaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'orden', 'activo', 'color_fondo']
    list_filter = ['activo']
    ordering = ['orden', 'codigo']
    search_fields = ['codigo', 'descripcion']


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['apellido', 'nombre', 'activo', 'fecha_alta']
    list_filter = ['activo']
    ordering = ['apellido', 'nombre']
    search_fields = ['apellido', 'nombre']


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'fecha', 'estado', 'observaciones']
    list_filter = ['fecha', 'estado', 'empleado']
    ordering = ['-fecha', 'empleado']
    search_fields = ['empleado__apellido', 'empleado__nombre']
    date_hierarchy = 'fecha'
