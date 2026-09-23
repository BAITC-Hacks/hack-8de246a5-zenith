import csv
import io
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

def parse_csv(raw: bytes):
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            text = raw.decode('cp1251')
        except UnicodeDecodeError:
            raise ValueError('Сохраните CSV в кодировке UTF-8.')
    if not text.strip():
        raise ValueError('Файл пуст. Добавьте транзакции и заголовки.')
    delimiter = ';' if text.splitlines()[0].count(';') > text.splitlines()[0].count(',') else ','
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    aliases = {'дата': 'date', 'описание': 'description', 'сумма': 'amount', 'тип': 'type'}
    headers = [aliases.get(h.strip().lower(), h.strip().lower()) for h in (reader.fieldnames or [])]
    if len(set(headers)) != len(headers) or not {'date', 'description', 'amount'} <= set(headers):
        raise ValueError('Нужны уникальные колонки: дата, описание, сумма (или date, description, amount).')
    reader.fieldnames = headers
    rows = []
    for n, row in enumerate(reader, 2):
        try:
            if None in row or any(v is None for v in row.values()):
                raise ValueError('число полей не совпадает с заголовком')
            day = None
            for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
                try:
                    day = datetime.strptime(row['date'].strip(), fmt).date()
                    break
                except ValueError:
                    pass
            if day is None or day > date.today():
                raise ValueError('некорректная дата или дата в будущем')
            description = row['description'].strip()
            if not description or len(description) > 500:
                raise ValueError('описание должно содержать от 1 до 500 символов')
            amount = Decimal(row['amount'].replace(' ', '').replace('\xa0', '').replace(',', '.'))
            if not amount.is_finite() or amount == 0 or abs(amount) > 10**10 or amount != amount.quantize(Decimal('.01')):
                raise ValueError('сумма должна быть ненулевой, не более 10 млрд, до 2 знаков после запятой')
            kind = row.get('type', '').strip().lower()
            kinds = {'доход': 'income', 'расход': 'expense', 'income': 'income', 'expense': 'expense'}
            if kind and kind not in kinds:
                raise ValueError('тип: доход/расход или income/expense')
            # Явный тип имеет приоритет; без типа минус — расход, плюс — доход.
            kind = kinds[kind] if kind else ('expense' if amount < 0 else 'income')
            rows.append(dict(date=day, description=description, amount_minor=int(abs(amount) * 100), kind=kind))
            if len(rows) > 1000:
                raise ValueError('максимум 1000 транзакций за загрузку')
        except (ValueError, InvalidOperation) as exc:
            raise ValueError(f'Строка {n}: {exc}') from exc
    if not rows:
        raise ValueError('В файле есть заголовки, но нет транзакций.')
    return rows
