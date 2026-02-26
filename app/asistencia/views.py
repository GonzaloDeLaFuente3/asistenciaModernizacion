import calendar
import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Min
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

@login_required
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

@login_required
def empleados_lista(request):
    empleados = Empleado.objects.all()
    return render(request, 'asistencia/empleados/lista.html', {'empleados': empleados})


@login_required
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


@login_required
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


@login_required
@require_POST
def empleados_eliminar(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    empleado.activo = False
    empleado.save()
    messages.success(request, f'Empleado "{empleado}" desactivado.')
    return redirect('empleados_lista')


@login_required
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

@login_required
def estados_lista(request):
    estados = EstadoAsistencia.objects.all()
    return render(request, 'asistencia/estados/lista.html', {'estados': estados})


@login_required
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


@login_required
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


@login_required
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

@login_required
def asistencia_redirigir(request):
    hoy = date.today()
    return redirect('asistencia_grilla', anio=hoy.year, mes=hoy.month)


@login_required
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

@login_required
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


# ─────────────────────────────────────────
# Estadísticas
# ─────────────────────────────────────────

@login_required
def estadisticas(request):
    hoy = date.today()

    # ── Parámetros del filtro ──────────────────────────────
    periodo = request.GET.get('periodo', 'mensual')
    try:
        anio = int(request.GET.get('anio', hoy.year))
    except ValueError:
        anio = hoy.year

    mes_param = hoy.month
    trimestre_param = (hoy.month - 1) // 3 + 1
    semestre_param = 1 if hoy.month <= 6 else 2

    # ── Calcular rango de fechas ───────────────────────────
    try:
        if periodo == 'trimestral':
            trimestre_param = int(request.GET.get('trimestre', trimestre_param))
            trimestre_param = max(1, min(4, trimestre_param))
            mes_inicio = (trimestre_param - 1) * 3 + 1
            fecha_inicio = date(anio, mes_inicio, 1)
            mes_fin = mes_inicio + 2
            fecha_fin = date(anio, mes_fin, calendar.monthrange(anio, mes_fin)[1])
            titulo_periodo = f"T{trimestre_param} – {anio}"

        elif periodo == 'semestral':
            semestre_param = int(request.GET.get('semestre', semestre_param))
            semestre_param = max(1, min(2, semestre_param))
            if semestre_param == 1:
                fecha_inicio = date(anio, 1, 1)
                fecha_fin = date(anio, 6, 30)
            else:
                fecha_inicio = date(anio, 7, 1)
                fecha_fin = date(anio, 12, 31)
            titulo_periodo = f"S{semestre_param} – {anio}"

        elif periodo == 'anual':
            fecha_inicio = date(anio, 1, 1)
            fecha_fin = date(anio, 12, 31)
            titulo_periodo = str(anio)

        else:  # mensual (default)
            periodo = 'mensual'
            mes_param = int(request.GET.get('mes', mes_param))
            mes_param = max(1, min(12, mes_param))
            fecha_inicio = date(anio, mes_param, 1)
            fecha_fin = date(anio, mes_param, calendar.monthrange(anio, mes_param)[1])
            titulo_periodo = f"{MESES_ES[mes_param]} {anio}"

    except (ValueError, TypeError):
        return redirect('estadisticas')

    # Límite real: nunca más allá de hoy
    fecha_fin_real = min(fecha_fin, hoy)

    # ── Días hábiles en el período (hasta hoy) ─────────────
    dias_habiles = []
    d = fecha_inicio
    while d <= fecha_fin_real:
        if d.weekday() < 5:
            dias_habiles.append(d)
        d += timedelta(days=1)
    total_dias_habiles = len(dias_habiles)

    # ── Empleados y estados activos ────────────────────────
    empleados = list(Empleado.objects.filter(activo=True))
    estados = list(EstadoAsistencia.objects.filter(activo=True))
    total_empleados = len(empleados)

    # ── Registros del período ──────────────────────────────
    registros_qs = RegistroAsistencia.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin_real,
        empleado__activo=True,
    ).select_related('estado', 'empleado')

    total_registros = registros_qs.count()
    total_posibles = total_dias_habiles * total_empleados
    cobertura_global = round(total_registros / total_posibles * 100, 1) if total_posibles > 0 else 0

    # ── Distribución global por estado ────────────────────
    dist_raw = (
        registros_qs
        .values('estado__id', 'estado__codigo', 'estado__descripcion',
                'estado__color_fondo', 'estado__color_texto', 'estado__orden')
        .annotate(total=Count('id'))
        .order_by('estado__orden')
    )
    dist_estados = []
    for item in dist_raw:
        pct = round(item['total'] / total_registros * 100, 1) if total_registros > 0 else 0
        dist_estados.append({**item, 'pct': pct})

    # ── Estadísticas por empleado (sin N+1) ────────────────
    registros_por_emp = {}
    for r in registros_qs:
        registros_por_emp.setdefault(r.empleado_id, []).append(r)

    stats_por_empleado = []
    for emp in empleados:
        regs = registros_por_emp.get(emp.id, [])
        conteo = {e.codigo: 0 for e in estados}
        for r in regs:
            if r.estado.codigo in conteo:
                conteo[r.estado.codigo] += 1
        # Lista ordenada igual que `estados` para iterar en template
        conteo_lista = [
            {'estado': e, 'cantidad': conteo.get(e.codigo, 0)}
            for e in estados
        ]
        total_marcados = len(regs)
        sin_registro = max(total_dias_habiles - total_marcados, 0)
        cobertura = round(total_marcados / total_dias_habiles * 100, 1) if total_dias_habiles > 0 else 0
        stats_por_empleado.append({
            'empleado': emp,
            'conteo_lista': conteo_lista,
            'total_marcados': total_marcados,
            'sin_registro': sin_registro,
            'cobertura': cobertura,
        })

    stats_por_empleado.sort(key=lambda x: x['cobertura'], reverse=True)
    sin_registro_total = sum(s['sin_registro'] for s in stats_por_empleado)

    # ── Tendencia mensual (períodos > 1 mes) ───────────────
    tendencia_mensual = []
    if periodo in ('trimestral', 'semestral', 'anual'):
        cur = date(fecha_inicio.year, fecha_inicio.month, 1)
        while cur <= fecha_fin and cur <= hoy:
            dias_h_mes = sum(
                1 for i in range(1, calendar.monthrange(cur.year, cur.month)[1] + 1)
                if date(cur.year, cur.month, i).weekday() < 5
                and date(cur.year, cur.month, i) <= hoy
            )
            regs_mes = registros_qs.filter(
                fecha__year=cur.year,
                fecha__month=cur.month,
            ).count()
            posibles_mes = dias_h_mes * total_empleados
            pct_mes = round(regs_mes / posibles_mes * 100, 1) if posibles_mes > 0 else 0
            tendencia_mensual.append({
                'etiqueta': f"{MESES_ES[cur.month][:3]} {str(cur.year)[2:]}",
                'pct': pct_mes,
                'registros': regs_mes,
            })
            cur = date(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1)

    # ── Años disponibles ───────────────────────────────────
    primera_fecha = RegistroAsistencia.objects.aggregate(primera=Min('fecha'))['primera']
    min_year = primera_fecha.year if primera_fecha else hoy.year
    anios_disponibles = list(range(min_year, hoy.year + 1))

    return render(request, 'asistencia/estadisticas.html', {
        'periodo': periodo,
        'anio': anio,
        'titulo_periodo': titulo_periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin_real': fecha_fin_real,
        'total_dias_habiles': total_dias_habiles,
        'total_empleados': total_empleados,
        'total_registros': total_registros,
        'total_posibles': total_posibles,
        'cobertura_global': cobertura_global,
        'dist_estados': dist_estados,
        'stats_por_empleado': stats_por_empleado,
        'estados': estados,
        'tendencia_mensual': tendencia_mensual,
        'sin_registro_total': sin_registro_total,
        'anios_disponibles': anios_disponibles,
        'MESES_ES': MESES_ES,
        'hoy': hoy,
        # Params para re-render del form
        'mes_param': mes_param,
        'trimestre_param': trimestre_param,
        'semestre_param': semestre_param,
    })
