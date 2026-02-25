import calendar
import json
from datetime import date, timedelta

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import EmpleadoForm, EstadoAsistenciaForm
from .models import Empleado, EstadoAsistencia, RegistroAsistencia

MESES_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}

DIAS_CORTOS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']


# ─────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────

def dashboard(request):
    empleados_activos = Empleado.objects.filter(activo=True).count()
    estados_activos = EstadoAsistencia.objects.filter(activo=True).count()
    hoy = date.today()
    return render(request, 'asistencia/dashboard.html', {
        'empleados_activos': empleados_activos,
        'estados_activos': estados_activos,
        'hoy': hoy,
        'mes_actual_anio': hoy.year,
        'mes_actual_mes': hoy.month,
        'mes_actual_nombre': MESES_ES[hoy.month],
    })


# ─────────────────────────────────────────
# Empleados
# ─────────────────────────────────────────

def empleados_lista(request):
    empleados = Empleado.objects.all()
    return render(request, 'asistencia/empleados/lista.html', {'empleados': empleados})


def empleados_crear(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado creado exitosamente.')
            return redirect('empleados_lista')
    else:
        form = EmpleadoForm()
    return render(request, 'asistencia/empleados/form.html', {
        'form': form,
        'titulo': 'Crear Empleado',
    })


def empleados_editar(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado actualizado exitosamente.')
            return redirect('empleados_lista')
    else:
        form = EmpleadoForm(instance=empleado)
    return render(request, 'asistencia/empleados/form.html', {
        'form': form,
        'titulo': 'Editar Empleado',
        'empleado': empleado,
    })


@require_POST
def empleados_eliminar(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    empleado.activo = False
    empleado.save()
    messages.success(request, f'Empleado "{empleado}" desactivado.')
    return redirect('empleados_lista')


@require_POST
def empleados_activar(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    empleado.activo = True
    empleado.save()
    messages.success(request, f'Empleado "{empleado}" reactivado.')
    return redirect('empleados_lista')


# ─────────────────────────────────────────
# Estados de Asistencia
# ─────────────────────────────────────────

def estados_lista(request):
    estados = EstadoAsistencia.objects.all()
    return render(request, 'asistencia/estados/lista.html', {'estados': estados})


def estados_crear(request):
    if request.method == 'POST':
        form = EstadoAsistenciaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estado creado exitosamente.')
            return redirect('estados_lista')
    else:
        form = EstadoAsistenciaForm()
    return render(request, 'asistencia/estados/form.html', {
        'form': form,
        'titulo': 'Crear Estado',
    })


def estados_editar(request, pk):
    estado = get_object_or_404(EstadoAsistencia, pk=pk)
    if request.method == 'POST':
        form = EstadoAsistenciaForm(request.POST, instance=estado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estado actualizado exitosamente.')
            return redirect('estados_lista')
    else:
        form = EstadoAsistenciaForm(instance=estado)
    return render(request, 'asistencia/estados/form.html', {
        'form': form,
        'titulo': 'Editar Estado',
        'estado': estado,
    })


@require_POST
def estados_eliminar(request, pk):
    estado = get_object_or_404(EstadoAsistencia, pk=pk)
    if estado.registros.exists():
        messages.error(
            request,
            f'No se puede eliminar el estado "{estado}" porque tiene registros de asistencia '
            f'vinculados. Considere desactivarlo desde "Editar".'
        )
        return redirect('estados_lista')
    estado.delete()
    messages.success(request, f'Estado "{estado}" eliminado.')
    return redirect('estados_lista')


# ─────────────────────────────────────────
# Asistencia – Grilla mensual
# ─────────────────────────────────────────

def asistencia_redirigir(request):
    hoy = date.today()
    return redirect('asistencia_grilla', anio=hoy.year, mes=hoy.month)


def asistencia_grilla(request, anio, mes):
    hoy = date.today()

    # Validar año y mes
    try:
        primer_dia = date(anio, mes, 1)
    except ValueError:
        return redirect('asistencia_redirigir')

    ultimo_dia_num = calendar.monthrange(anio, mes)[1]
    ultimo_dia = date(anio, mes, ultimo_dia_num)

    # Días hábiles del mes (Lun–Vie)
    dias_habiles = []
    dia = primer_dia
    while dia <= ultimo_dia:
        if dia.weekday() < 5:
            dias_habiles.append(dia)
        dia += timedelta(days=1)

    # Agrupar por semana ISO
    semanas = []
    semana_actual = []
    current_week_num = None
    for dia in dias_habiles:
        wnum = dia.isocalendar()[1]
        if current_week_num is None:
            current_week_num = wnum
        if wnum != current_week_num:
            semanas.append(semana_actual)
            semana_actual = []
            current_week_num = wnum
        semana_actual.append(dia)
    if semana_actual:
        semanas.append(semana_actual)

    # Filtro de semana
    semana_param = request.GET.get('semana', '')
    semana_idx = None
    if semana_param.isdigit():
        idx = int(semana_param)
        if 0 <= idx < len(semanas):
            semana_idx = idx
            dias_a_mostrar = semanas[idx]
        else:
            dias_a_mostrar = dias_habiles
    else:
        dias_a_mostrar = dias_habiles

    # Empleados y estados activos
    empleados = Empleado.objects.filter(activo=True)
    estados = EstadoAsistencia.objects.filter(activo=True)

    # Registros del período visible
    if dias_a_mostrar:
        registros_qs = RegistroAsistencia.objects.filter(
            fecha__gte=dias_a_mostrar[0],
            fecha__lte=dias_a_mostrar[-1],
        ).select_related('estado')
        registro_dict = {(r.empleado_id, r.fecha): r.estado for r in registros_qs}
    else:
        registro_dict = {}

    # Construir grilla
    grid = []
    for emp in empleados:
        fila = {
            'empleado': emp,
            'dias': [
                {
                    'fecha': dia,
                    'fecha_str': dia.strftime('%Y-%m-%d'),
                    'estado': registro_dict.get((emp.id, dia)),
                    'es_hoy': dia == hoy,
                }
                for dia in dias_a_mostrar
            ],
        }
        grid.append(fila)

    # Encabezados de columnas
    columnas = [
        {
            'fecha': dia,
            'fecha_str': dia.strftime('%Y-%m-%d'),
            'dia_num': dia.day,
            'dia_nombre': DIAS_CORTOS[dia.weekday()],
            'es_hoy': dia == hoy,
        }
        for dia in dias_a_mostrar
    ]

    # Información de semanas para el filtro
    semanas_info = []
    for i, s in enumerate(semanas):
        semanas_info.append({
            'idx': i,
            'label': (
                f"Sem {i + 1}: "
                f"{DIAS_CORTOS[s[0].weekday()]} {s[0].day} – "
                f"{DIAS_CORTOS[s[-1].weekday()]} {s[-1].day}"
            ),
            'activa': semana_idx == i,
        })

    # Navegación mes anterior / siguiente
    if mes == 1:
        mes_ant_anio, mes_ant_mes = anio - 1, 12
    else:
        mes_ant_anio, mes_ant_mes = anio, mes - 1

    if mes == 12:
        mes_sig_anio, mes_sig_mes = anio + 1, 1
    else:
        mes_sig_anio, mes_sig_mes = anio, mes + 1

    return render(request, 'asistencia/asistencia_grilla.html', {
        'anio': anio,
        'mes': mes,
        'mes_nombre': MESES_ES[mes],
        'hoy': hoy,
        'columnas': columnas,
        'grid': grid,
        'estados': estados,
        'semanas_info': semanas_info,
        'semana_idx': semana_idx,
        'mes_ant_anio': mes_ant_anio,
        'mes_ant_mes': mes_ant_mes,
        'mes_sig_anio': mes_sig_anio,
        'mes_sig_mes': mes_sig_mes,
    })


# ─────────────────────────────────────────
# Asistencia – Guardado AJAX
# ─────────────────────────────────────────

@require_POST
def asistencia_guardar(request):
    try:
        data = json.loads(request.body)
        registros = data.get('registros', [])

        with transaction.atomic():
            for r in registros:
                empleado_id = r.get('empleado_id')
                fecha = r.get('fecha')
                estado_id = r.get('estado_id')

                if not empleado_id or not fecha:
                    continue

                if estado_id:
                    RegistroAsistencia.objects.update_or_create(
                        empleado_id=empleado_id,
                        fecha=fecha,
                        defaults={
                            'estado_id': estado_id,
                            'observaciones': r.get('observaciones', ''),
                        },
                    )
                else:
                    RegistroAsistencia.objects.filter(
                        empleado_id=empleado_id,
                        fecha=fecha,
                    ).delete()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
