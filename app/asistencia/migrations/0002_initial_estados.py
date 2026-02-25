from django.db import migrations


ESTADOS_INICIALES = [
    {'codigo': 'P',  'descripcion': 'Presente',            'color_fondo': '#d4edda', 'color_texto': '#155724', 'orden': 1},
    {'codigo': 'A',  'descripcion': 'Ausente',              'color_fondo': '#f8d7da', 'color_texto': '#721c24', 'orden': 2},
    {'codigo': 'AA', 'descripcion': 'Ausente con aviso',   'color_fondo': '#fff3cd', 'color_texto': '#856404', 'orden': 3},
    {'codigo': 'AS', 'descripcion': 'Ausente sin aviso',   'color_fondo': '#f8d7da', 'color_texto': '#721c24', 'orden': 4},
    {'codigo': 'TA', 'descripcion': 'Tardanza con aviso',  'color_fondo': '#fff3cd', 'color_texto': '#856404', 'orden': 5},
    {'codigo': 'TS', 'descripcion': 'Tardanza sin aviso',  'color_fondo': '#ffe0b2', 'color_texto': '#e65100', 'orden': 6},
]


def crear_estados(apps, schema_editor):
    EstadoAsistencia = apps.get_model('asistencia', 'EstadoAsistencia')
    for datos in ESTADOS_INICIALES:
        EstadoAsistencia.objects.create(**datos)


def eliminar_estados(apps, schema_editor):
    EstadoAsistencia = apps.get_model('asistencia', 'EstadoAsistencia')
    codigos = [e['codigo'] for e in ESTADOS_INICIALES]
    EstadoAsistencia.objects.filter(codigo__in=codigos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('asistencia', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_estados, eliminar_estados),
    ]
