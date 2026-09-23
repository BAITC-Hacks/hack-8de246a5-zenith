import csv
import io
import random
from datetime import date, timedelta

def demo_csv():
    today = date.today()
    previous = today.replace(day=1) - timedelta(days=1)
    rng = random.Random(42)
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(['дата', 'описание', 'сумма', 'тип'])
    merchants = [('Magnum · продукты', 6400), ('Yandex Go · такси', 1800), ('Кофейня у дома', 2100), ('Кино · билеты', 4200), ('Аптека', 3500), ('Книги', 5500), ('Wildberries · одежда', 12000), ('Small · продукты', 4800)]
    for year, month, last_day in [(previous.year, previous.month, previous.day), (today.year, today.month, today.day)]:
        writer.writerow([date(year, month, 1), 'Зарплата', 480000, 'доход'])
        writer.writerow([date(year, month, min(3, last_day)), 'Аренда квартиры', 145000, 'расход'])
        writer.writerow([date(year, month, min(5, last_day)), 'Коммунальные услуги', 18500, 'расход'])
        writer.writerow([date(year, month, min(10, last_day)), 'Фриланс · проект', 75000, 'доход'])
        for _ in range(36):
            description, base = rng.choice(merchants)
            writer.writerow([date(year, month, rng.randint(1, last_day)), description, round(base * rng.uniform(.6, 1.5)), 'расход'])
    return stream.getvalue().encode('utf-8-sig')
