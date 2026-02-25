from django.db import models


class EstadoAsistencia(models.Model):
    codigo = models.CharField(max_length=5, unique=True)
    descripcion = models.CharField(max_length=100)
    color_fondo = models.CharField(max_length=7, default="#FFFFFF")
    color_texto = models.CharField(max_length=7, default="#000000")
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['orden', 'codigo']
        verbose_name = "Estado de Asistencia"
        verbose_name_plural = "Estados de Asistencia"

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateField(auto_now_add=True)
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['apellido', 'nombre']
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class RegistroAsistencia(models.Model):
    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name='asistencias'
    )
    fecha = models.DateField()
    estado = models.ForeignKey(
        EstadoAsistencia, on_delete=models.PROTECT, related_name='registros'
    )
    observaciones = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('empleado', 'fecha')
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"

    def __str__(self):
        return (
            f"{self.empleado.apellido}, {self.empleado.nombre} - "
            f"{self.fecha} - {self.estado.codigo}"
        )
