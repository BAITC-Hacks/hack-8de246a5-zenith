import calendar
from datetime import date, timedelta
from .schemas import CATEGORIES

def month_bounds(month):
    try:
        start = date.fromisoformat(month + '-01')
        return start, date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
    except ValueError:
        raise ValueError('Укажите месяц в формате YYYY-MM.')

def dashboard(rows, month):
    start, end = month_bounds(month)
    previous_end = start - timedelta(days=1)
    previous_start = previous_end.replace(day=1)
    current = [r for r in rows if start <= r.date <= end]
    previous = [r for r in rows if previous_start <= r.date <= previous_end]
    def total(items, kind):
        return sum(r.amount_minor for r in items if r.kind == kind) / 100
    income, expense = total(current, 'income'), total(current, 'expense')
    previous_expense = total(previous, 'expense')
    elapsed = min(end.day, max(0, (date.today() - start).days + 1))
    average = expense / elapsed if elapsed else 0
    # Остаток — денежный поток месяца при нулевом начальном балансе.
    projected = average * end.day
    categories = []
    for i, name in enumerate(CATEGORIES, 1):
        amount = sum(r.amount_minor for r in current if r.kind == 'expense' and r.category_id == i) / 100
        if amount:
            categories.append({'name': name, 'amount': amount})
    uncategorized = sum(r.amount_minor for r in current if r.kind == 'expense' and r.category_id is None) / 100
    if uncategorized:
        categories.append({'name': 'Без категории', 'amount': uncategorized})
    days = [{'day': n, 'income': total([r for r in current if r.date.day == n], 'income'), 'expense': total([r for r in current if r.date.day == n], 'expense')} for n in range(1, elapsed + 1)]
    top = sorted([r for r in current if r.kind == 'expense'], key=lambda r: r.amount_minor, reverse=True)[:5]
    return {'month': month, 'count': len(current), 'income': income, 'expense': expense, 'balance': income - expense,
        'previous_expense': previous_expense, 'change_percent': round((expense - previous_expense) / previous_expense * 100, 1) if previous_expense else None,
        'comparison_note': 'Выбранный месяц против полного предыдущего месяца',
        'categories': sorted(categories, key=lambda c: c['amount'], reverse=True), 'days': days,
        'top': [{'id': r.id, 'date': r.date.isoformat(), 'description': r.description, 'amount': r.amount_minor / 100, 'category': CATEGORIES[r.category_id - 1] if r.category_id else 'Без категории'} for r in top],
        'forecast': {'daily_average': round(average, 2), 'projected_expense': round(projected, 2), 'remaining': round(income - projected, 2), 'days_left': end.day - elapsed},
        'local_count': sum(r.source != 'claude' for r in current if r.kind == 'expense')}
