from django.db import migrations


EMPLEADOS_INICIALES = [
    {'nombre': 'Lautaro',   'apellido': 'Lobo'},
    {'nombre': 'Robert',    'apellido': 'Esteba'},
    {'nombre': 'Franco',    'apellido': 'Leiva'},
    {'nombre': 'Maxi',      'apellido': 'Aluzugaray'},
    {'nombre': 'Carlos',    'apellido': 'Isasmendi'},
    {'nombre': 'Lucio',     'apellido': 'Cruces'},
    {'nombre': 'Luciano',   'apellido': 'Reguera'},
    {'nombre': 'Alejandro', 'apellido': 'Gabriel'},
    {'nombre': 'Matias',    'apellido': 'Borquez'},
    {'nombre': 'Nahuel',    'apellido': 'Soria'},
    {'nombre': 'Gonzalo',   'apellido': 'De La Fuente'},
    {'nombre': 'Diego',     'apellido': 'Robert'},
    {'nombre': 'Lorena',    'apellido': 'Carrizo'},
]


def crear_empleados(apps, schema_editor):
    Empleado = apps.get_model('asistencia', 'Empleado')
    for datos in EMPLEADOS_INICIALES:
        Empleado.objects.create(**datos)


def eliminar_empleados(apps, schema_editor):
    Empleado = apps.get_model('asistencia', 'Empleado')
    # Eliminamos solo si no existen registros de asistencia (para reversión segura)
    for datos in EMPLEADOS_INICIALES:
        Empleado.objects.filter(
            nombre=datos['nombre'], apellido=datos['apellido']
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('asistencia', '0002_initial_estados'),
    ]

    operations = [
        migrations.RunPython(crear_empleados, eliminar_empleados),
    ]
