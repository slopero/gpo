import sqlite3

conn = sqlite3.connect('db/cars.db')
c = conn.cursor()

c.execute('SELECT DISTINCT substr("Название_машины", 1, instr("Название_машины" || " ", " ") - 1) FROM cars')
brands = sorted([r[0] for r in c.fetchall() if r[0]])

print(f"Total brands: {len(brands)}")
brand_models = {}
for b in brands:
    c.execute(
        'SELECT DISTINCT "Название_машины" FROM cars WHERE "Название_машины" >= ? AND "Название_машины" < ? LIMIT 5',
        (b + " ", b + chr(ord(" ") + 1)),
    )
    models = [r[0] for r in c.fetchall()]
    brand_models[b] = models
    print(f"{b!r} -> {models[:2]}")