'''Adapt routine definitions and persisted occurrences for monthly analysis.'''

from calendar import monthrange
from datetime import date, timedelta
from math import cos, pi, sin

from .models import RoutineOccurrence


MONTH_NAMES = (
    '',
    'Janeiro',
    'Fevereiro',
    'Março',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro',
)
WEEKDAY_INITIALS = ('S', 'T', 'Q', 'Q', 'S', 'S', 'D')
WEEKDAY_NAMES = (
    'Segunda-feira',
    'Terça-feira',
    'Quarta-feira',
    'Quinta-feira',
    'Sexta-feira',
    'Sábado',
    'Domingo',
)


def parse_month(value, *, fallback):
    '''Return the first day of a YYYY-MM value or the fallback month.'''

    try:
        selected = date.fromisoformat(f'{value}-01') if value else fallback
    except ValueError:
        selected = fallback
    return selected.replace(day=1)


def month_bounds(month):
    last_day = monthrange(month.year, month.month)[1]
    return month, month.replace(day=last_day)


def _shift_month(month, offset):
    if offset < 0 and month == date.min.replace(day=1):
        return month
    if offset > 0 and month.year == date.max.year and month.month == 12:
        return month
    month_index = month.year * 12 + month.month - 1 + offset
    year, zero_based_month = divmod(month_index, 12)
    return date(year, zero_based_month + 1, 1)


def _month_value(month):
    return f'{month.year:04d}-{month.month:02d}'


def _is_definition_scheduled(item, current_date):
    if current_date < item.starts_on:
        return False
    if item.ends_on and current_date > item.ends_on:
        return False
    if item.deleted_at is not None:
        deleted_month = item.deleted_at.date().replace(day=1)
        return current_date < deleted_month
    return item.is_active


def _chart_geometry(days):
    top, baseline, width = 6, 104, 1000
    step = width / max(len(days) - 1, 1)
    points = []
    for index, day in enumerate(days):
        x = step * index
        y = top + (100 - day['percentage']) * (baseline - top) / 100
        points.append({**day, 'x': round(x, 2), 'y': round(y, 2)})
    commands = [f"M {points[0]['x']},{points[0]['y']}"]
    for index in range(len(points) - 1):
        previous = points[max(0, index - 1)]
        current = points[index]
        following = points[index + 1]
        after = points[min(len(points) - 1, index + 2)]
        control_1_x = current['x'] + (following['x'] - previous['x']) / 6
        control_1_y = max(
            top,
            min(baseline, current['y'] + (following['y'] - previous['y']) / 6),
        )
        control_2_x = following['x'] - (after['x'] - current['x']) / 6
        control_2_y = max(
            top,
            min(baseline, following['y'] - (after['y'] - current['y']) / 6),
        )
        commands.append(
            'C '
            f'{round(control_1_x, 2)},{round(control_1_y, 2)} '
            f'{round(control_2_x, 2)},{round(control_2_y, 2)} '
            f"{following['x']},{following['y']}",
        )
    line_path = ' '.join(commands)
    area_path = f'{line_path} L {width},{baseline} L 0,{baseline} Z'
    return points, line_path, area_path


def _radar_geometry(rows):
    radar_rows = sorted(
        (row for row in rows if row['total']),
        key=lambda row: (-row['percentage'], row['item'].title.lower()),
    )[:5]
    if len(radar_rows) < 3:
        return None

    center_x, center_y, radius = 80, 62, 52

    def coordinates(index, scale):
        angle = -pi / 2 + 2 * pi * index / len(radar_rows)
        return (
            round(center_x + cos(angle) * radius * scale, 2),
            round(center_y + sin(angle) * radius * scale, 2),
        )

    rings = [
        ' '.join(
            f'{x},{y}'
            for index in range(len(radar_rows))
            for x, y in [coordinates(index, scale)]
        )
        for scale in (0.25, 0.5, 0.75, 1)
    ]
    axes = [
        {'x2': x, 'y2': y}
        for index in range(len(radar_rows))
        for x, y in [coordinates(index, 1)]
    ]
    values = []
    for index, row in enumerate(radar_rows):
        x, y = coordinates(index, row['percentage'] / 100)
        values.append(
            {
                'x': x,
                'y': y,
                'title': row['item'].title,
                'percentage': row['percentage'],
            },
        )
    return {
        'center_x': center_x,
        'center_y': center_y,
        'rings': rings,
        'axes': axes,
        'values': values,
        'value_points': ' '.join(
            f"{point['x']},{point['y']}" for point in values
        ),
    }


def _streaks(daily_totals):
    tracked_days = [day for day in daily_totals if day['total']]
    best = running = 0
    for day in tracked_days:
        if day['completed'] == day['total']:
            running += 1
            best = max(best, running)
        else:
            running = 0

    current = 0
    for day in reversed(tracked_days):
        if day['completed'] != day['total']:
            break
        current += 1
    return current, best


def build_month_analysis(*, items, occurrences, month, today):
    '''Build template-ready monthly statistics without creating fake records.'''

    start_date, end_date = month_bounds(month)
    dates = [
        start_date + timedelta(days=offset)
        for offset in range((end_date - start_date).days + 1)
    ]
    occurrence_map = {
        (occurrence.routine_item_id, occurrence.occurrence_date): occurrence
        for occurrence in occurrences
    }
    occurrence_item_ids = {occurrence.routine_item_id for occurrence in occurrences}
    relevant_items = []
    for item in items:
        if item.starts_on > end_date:
            continue
        if item.deleted_at is not None:
            deleted_month = item.deleted_at.date().replace(day=1)
            if start_date >= deleted_month:
                continue
        if item.deleted_at is not None or item.is_active or item.pk in occurrence_item_ids:
            relevant_items.append(item)

    daily_counts = {
        current_date: {'completed': 0, 'total': 0}
        for current_date in dates
    }
    rows = []
    for item in relevant_items:
        cells = []
        completed_count = 0
        tracked_count = 0
        for current_date in dates:
            occurrence = occurrence_map.get((item.pk, current_date))
            scheduled = occurrence is not None or _is_definition_scheduled(
                item,
                current_date,
            )
            status = 'unavailable'
            status_label = 'Não agendado'
            can_toggle = False

            if scheduled:
                tracked_count += 1
                daily_counts[current_date]['total'] += 1
                can_toggle = item.deleted_at is None
                if occurrence is None and current_date > today:
                    status = 'future'
                    status_label = 'Dia futuro sem registro'
                elif occurrence is None:
                    status = 'missing'
                    status_label = 'Sem registro'
                elif occurrence.status == RoutineOccurrence.Status.COMPLETED:
                    status = 'completed'
                    status_label = 'Concluído'
                    completed_count += 1
                    daily_counts[current_date]['completed'] += 1
                elif occurrence.status == RoutineOccurrence.Status.SKIPPED:
                    status = 'skipped'
                    status_label = 'Pulado'
                else:
                    status = 'pending'
                    status_label = 'Não concluído'

            cells.append(
                {
                    'date': current_date,
                    'date_iso': current_date.isoformat(),
                    'date_label': current_date.strftime('%d/%m/%Y'),
                    'status': status,
                    'status_label': status_label,
                    'can_toggle': can_toggle,
                    'is_today': current_date == today,
                },
            )

        percentage = round(completed_count * 100 / tracked_count) if tracked_count else 0
        rows.append(
            {
                'item': item,
                'cells': cells,
                'completed': completed_count,
                'total': tracked_count,
                'percentage': percentage,
            },
        )

    daily_totals = []
    for current_date, counts in daily_counts.items():
        percentage = (
            round(counts['completed'] * 100 / counts['total'])
            if counts['total']
            else 0
        )
        daily_totals.append(
            {
                'date': current_date,
                'date_label': current_date.strftime('%d/%m/%Y'),
                'day': current_date.day,
                'completed': counts['completed'],
                'total': counts['total'],
                'percentage': percentage,
                'heat_level': (
                    0
                    if not counts['completed']
                    else min(4, max(1, (percentage + 24) // 25))
                ),
                'is_today': current_date == today,
            },
        )

    total_completed = sum(day['completed'] for day in daily_totals)
    total_tracked = sum(day['total'] for day in daily_totals)
    average = round(total_completed * 100 / total_tracked) if total_tracked else 0
    current_streak, best_streak = _streaks(daily_totals)
    chart_points, chart_line_path, chart_area_path = _chart_geometry(daily_totals)
    weekly_summaries = []
    for index in range(5):
        week_days = daily_totals[index * 7 : (index + 1) * 7]
        if not week_days:
            continue
        completed = sum(day['completed'] for day in week_days)
        total = sum(day['total'] for day in week_days)
        percentage = round(completed * 100 / total) if total else 0
        weekly_summaries.append(
            {
                'label': f'S{index + 1}',
                'completed': completed,
                'total': total,
                'percentage': percentage,
            },
        )
    weeks = [
        {
            'label': f'S{index + 1}',
            'days': [
                {
                    'date': current_date,
                    'number': current_date.day,
                    'weekday_initial': WEEKDAY_INITIALS[current_date.weekday()],
                    'weekday_name': WEEKDAY_NAMES[current_date.weekday()],
                    'is_today': current_date == today,
                }
                for current_date in dates[index * 7 : (index + 1) * 7]
            ],
        }
        for index in range(5)
        if dates[index * 7 : (index + 1) * 7]
    ]
    previous_month = _shift_month(month, -1)
    next_month = _shift_month(month, 1)
    return {
        'month': month,
        'month_value': _month_value(month),
        'month_label': f'{MONTH_NAMES[month.month]} de {month.year}',
        'previous_month': _month_value(previous_month),
        'next_month': _month_value(next_month),
        'weeks': weeks,
        'rows': rows,
        'chart_points': chart_points,
        'chart_line_path': chart_line_path,
        'chart_area_path': chart_area_path,
        'weekly_summaries': weekly_summaries,
        'radar': _radar_geometry(rows),
        'metrics': {
            'habit_count': len(rows),
            'average': average,
            'current_streak': current_streak,
            'best_streak': best_streak,
        },
    }
