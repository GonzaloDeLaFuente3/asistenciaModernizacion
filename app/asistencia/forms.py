from django import forms

from .models import Empleado, EstadoAsistencia


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['nombre', 'apellido', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'notas': 'Notas / Observaciones',
        }


class EstadoAsistenciaForm(forms.ModelForm):
    class Meta:
        model = EstadoAsistencia
        fields = ['codigo', 'descripcion', 'color_fondo', 'color_texto', 'orden', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: P, TA, AS'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Presente'}),
            'color_fondo': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_texto': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'codigo': 'Código',
            'descripcion': 'Descripción',
            'color_fondo': 'Color de fondo',
            'color_texto': 'Color de texto',
            'orden': 'Orden',
            'activo': 'Activo',
        }
