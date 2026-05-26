import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "economic_data.db")

ECONOMIC_DATA = {
    (2024, 1): {
        'inflation': 7.42, 'retail_trade': 105.3, 'unemployment': 2.8,
        'usd_rate': 89.54, 'car_sales': 95243, 'car_growth': 15.2,
        'assessment': 'Российская экономика демонстрирует устойчивый рост в начале 2024 года. Основные факторы роста — высокий потребительский спрос, увеличение промышленного производства и благоприятная конъюнктура внешнего рынка.'
    },
    (2024, 2): {
        'inflation': 7.67, 'retail_trade': 106.1, 'unemployment': 2.7,
        'usd_rate': 91.23, 'car_sales': 87456, 'car_growth': 12.8,
        'assessment': 'Экономика России продолжает развитие при поддержке внутреннего спроса. Наблюдается рост промышленного производства и сохранение высоких реальных доходов населения.'
    },
    (2024, 3): {
        'inflation': 7.70, 'retail_trade': 105.8, 'unemployment': 2.6,
        'usd_rate': 92.45, 'car_sales': 102345, 'car_growth': 14.5,
        'assessment': 'По состоянию на конец марта 2024 года российская экономика показывает уверенный рост. Ключевые показатели остаются на стабильном уровне.'
    },
    (2024, 4): {
        'inflation': 7.82, 'retail_trade': 104.9, 'unemployment': 2.5,
        'usd_rate': 91.87, 'car_sales': 98234, 'car_growth': 11.3,
        'assessment': 'Экономика России сохраняет положительную динамику развития. Рост потребительского спроса и промышленного производства обеспечивают устойчивое развитие.'
    },
    (2024, 5): {
        'inflation': 7.95, 'retail_trade': 104.2, 'unemployment': 2.4,  
        'usd_rate': 89.34, 'car_sales': 95678, 'car_growth': 9.7,
        'assessment': 'Российская экономика продолжает рост на фоне стабильного потребительского спроса и увеличения инвестиций в основной капитал.'
    },
    (2024, 6): {
        'inflation': 8.12, 'retail_trade': 103.8, 'unemployment': 2.3,
        'usd_rate': 87.65, 'car_sales': 101234, 'car_growth': 10.2,
        'assessment': 'В первом полугодии 2024 года экономика России продемонстрировала уверенный рост по всем основным показателям.'
    },
    (2024, 7): {
        'inflation': 8.34, 'retail_trade': 103.5, 'unemployment': 2.3,
        'usd_rate': 88.23, 'car_sales': 97845, 'car_growth': 8.9,
        'assessment': 'Экономика России сохраняет устойчивые темпы роста. Промышленное производство и потребительский спрос находятся на высоком уровне.'
    },
    (2024, 8): {
        'inflation': 8.56, 'retail_trade': 103.2, 'unemployment': 2.2,
        'usd_rate': 90.12, 'car_sales': 94567, 'car_growth': 7.8,
        'assessment': 'Российская экономика демонстрирует стабильное развитие при сохранении низкого уровня безработицы и роста реальных доходов.'
    },
    (2024, 9): {
        'inflation': 8.78, 'retail_trade': 102.9, 'unemployment': 2.2,
        'usd_rate': 93.45, 'car_sales': 99123, 'car_growth': 6.5,
        'assessment': 'По состоянию на конец сентября 2024 года экономика России сохраняет положительную динамику развития.'
    },
    (2024, 10): {
        'inflation': 8.92, 'retail_trade': 102.6, 'unemployment': 2.1,
        'usd_rate': 95.67, 'car_sales': 100234, 'car_growth': 5.8,
        'assessment': 'Экономика России продолжает развитие в условиях стабильного потребительского спроса и промышленного роста.'
    },
    (2024, 11): {
        'inflation': 9.12, 'retail_trade': 102.3, 'unemployment': 2.1,
        'usd_rate': 96.23, 'car_sales': 98765, 'car_growth': 4.9,
        'assessment': 'Российская экономика сохраняет устойчивость перед вызовами внешнего рынка. Внутренний спрос остается высоким.'
    },
    (2024, 12): {
        'inflation': 9.52, 'retail_trade': 102.0, 'unemployment': 2.0,
        'usd_rate': 97.89, 'car_sales': 105432, 'car_growth': 4.2,
        'assessment': 'По итогам 2024 года российская экономика показала уверенный рост. Основные макроэкономические показатели остаются на стабильном уровне.'
    },
    (2025, 1): {
        'inflation': 9.87, 'retail_trade': 101.5, 'unemployment': 2.1,
        'usd_rate': 98.45, 'car_sales': 92345, 'car_growth': 3.5,
        'assessment': 'Российская экономика вступает в 2025 год с сохранением устойчивых темпов развития. Потребительский спрос остается высоким.'
    },
    (2025, 2): {
        'inflation': 9.65, 'retail_trade': 101.2, 'unemployment': 2.2,
        'usd_rate': 96.78, 'car_sales': 85678, 'car_growth': 2.8,
        'assessment': 'Экономика России продолжает развитие при некотором замедлении темпов роста. Наблюдается стабилизация ключевых показателей.'
    },
    (2025, 3): {
        'inflation': 9.34, 'retail_trade': 100.9, 'unemployment': 2.2,
        'usd_rate': 94.23, 'car_sales': 95432, 'car_growth': 2.1,
        'assessment': 'По состоянию на конец марта 2025 года российская экономика демонстрирует умеренное замедление роста.'
    },
    (2025, 4): {
        'inflation': 8.98, 'retail_trade': 100.6, 'unemployment': 2.3,
        'usd_rate': 91.56, 'car_sales': 91234, 'car_growth': 1.5,
        'assessment': 'Экономика России переходит к фазе умеренной стабилизации. Замедление инфляции создает предпосылки для восстановления роста.'
    },
    (2025, 5): {
        'inflation': 8.56, 'retail_trade': 100.4, 'unemployment': 2.3,
        'usd_rate': 89.12, 'car_sales': 89876, 'car_growth': 0.9,
        'assessment': 'Российская экономика показывает признаки стабилизации. Инфляционное давление постепенно снижается.'
    },
    (2025, 6): {
        'inflation': 8.12, 'retail_trade': 100.2, 'unemployment': 2.4,
        'usd_rate': 87.45, 'car_sales': 93456, 'car_growth': 0.4,
        'assessment': 'В первом полугодии 2025 года экономика России перешла к фазе умеренной стабилизации после активного роста 2024 года.'
    },
    (2025, 7): {
        'inflation': 7.78, 'retail_trade': 100.1, 'unemployment': 2.4,
        'usd_rate': 85.67, 'car_sales': 90123, 'car_growth': 0.2,
        'assessment': 'Экономика России сохраняет стабильность при снижении инфляционного давления. Рынок труда остается напряженным.'
    },
    (2025, 8): {
        'inflation': 7.45, 'retail_trade': 99.9, 'unemployment': 2.5,
        'usd_rate': 84.23, 'car_sales': 88765, 'car_growth': -0.3,
        'assessment': 'Российская экономика демонстрирует стагнацию в отдельных секторах. При этом сохраняются реальные доходы населения.'
    },
    (2025, 9): {
        'inflation': 7.12, 'retail_trade': 99.7, 'unemployment': 2.5,
        'usd_rate': 83.56, 'car_sales': 91234, 'car_growth': -0.8,
        'assessment': 'По состоянию на конец сентября 2025 года экономика России находится в фазе стагнации с признаками умеренного восстановления.'
    },
    (2025, 10): {
        'inflation': 6.89, 'retail_trade': 99.5, 'unemployment': 2.6,
        'usd_rate': 82.89, 'car_sales': 89567, 'car_growth': -1.2,
        'assessment': 'Экономика России показывает замедление роста. Высокая ключевая ставка сдерживает инвестиционную активность.'
    },
    (2025, 11): {
        'inflation': 6.56, 'retail_trade': 99.3, 'unemployment': 2.6,
        'usd_rate': 81.45, 'car_sales': 87890, 'car_growth': -1.8,
        'assessment': 'Российская экономика переходит к умеренной стабилизации. Продолжается снижение инфляции.'
    },
    (2025, 12): {
        'inflation': 6.23, 'retail_trade': 99.1, 'unemployment': 2.7,
        'usd_rate': 80.12, 'car_sales': 94567, 'car_growth': -2.3,
        'assessment': 'По итогам 2025 года экономика России показала замедление роста. Основные вызовы — высокая ключевая ставка и снижение инвестиций.'
    },
    (2026, 1): {
        'inflation': 5.91, 'retail_trade': 100.7, 'unemployment': 2.2,
        'usd_rate': 80.96, 'car_sales': 80604, 'car_growth': 3.9,
        'assessment': 'По состоянию на конец января 2026 года российская экономика демонстрирует умеренную стабилизацию. Динамика показывает переход от спада к слабому восстановлению.'
    },
    (2026, 2): {
        'inflation': 5.91, 'retail_trade': 100.7, 'unemployment': 2.2,
        'usd_rate': 80.96, 'car_sales': 80027, 'car_growth': 2.5,
        'assessment': 'По состоянию на конец февраля 2026 года российская экономика находится в фазе умеренной стабилизации после замедления роста в 2025 году.'
    },
    (2026, 3): {
        'inflation': 5.91, 'retail_trade': 100.7, 'unemployment': 2.2,
        'usd_rate': 80.96, 'car_sales': 80027, 'car_growth': 2.5,
        'assessment': 'По состоянию на конец марта 2026 года российская экономика находится в фазе умеренной стабилизации после замедления роста в 2025 году. Основные вызовы — высокая ключевая ставка Банка России, снижение инвестиционной активности и стагнация в отдельных отраслях реального сектора. При этом экономика демонстрирует устойчивость благодаря низкой безработице, сохранению реальных доходов населения и постепенному укреплению рубля. Динамика января–февраля 2026 года показывает переход от спада к слабому восстановлению в потребительском и промышленном секторах.'
    },
    (2026, 4): {
        'inflation': 5.75, 'retail_trade': 100.9, 'unemployment': 2.1,
        'usd_rate': 79.45, 'car_sales': 85123, 'car_growth': 3.2,
        'assessment': 'По состоянию на конец апреля 2026 года российская экономика укрепляет тенденцию к восстановлению. Наблюдается постепенное снижение инфляции и укрепление рубля.'
    },
    (2026, 5): {
        'inflation': 5.58, 'retail_trade': 101.2, 'unemployment': 2.1,
        'usd_rate': 78.23, 'car_sales': 87456, 'car_growth': 3.8,
        'assessment': 'Российская экономика демонстрирует уверенное восстановление. Рост потребительского спроса и промышленного производства усиливаются.'
    },
    (2026, 6): {
        'inflation': 5.42, 'retail_trade': 101.5, 'unemployment': 2.0,
        'usd_rate': 77.56, 'car_sales': 90234, 'car_growth': 4.5,
        'assessment': 'В первом полугодии 2026 года экономика России перешла к устойчивому восстановлению после стагнации 2025 года.'
    },
    (2026, 7): {
        'inflation': 5.25, 'retail_trade': 101.8, 'unemployment': 2.0,
        'usd_rate': 76.89, 'car_sales': 88765, 'car_growth': 5.1,
        'assessment': 'Экономика России продолжает восстановление. Снижение ключевой ставки способствует росту инвестиционной активности.'
    },
    (2026, 8): {
        'inflation': 5.12, 'retail_trade': 102.1, 'unemployment': 1.9,
        'usd_rate': 76.12, 'car_sales': 86543, 'car_growth': 5.8,
        'assessment': 'Российская экономика показывает устойчивый рост. Рынок труда остается напряженным с исторически низким уровнем безработицы.'
    },
    (2026, 9): {
        'inflation': 4.98, 'retail_trade': 102.4, 'unemployment': 1.9,
        'usd_rate': 75.45, 'car_sales': 89876, 'car_growth': 6.2,
        'assessment': 'По состоянию на конец сентября 2026 года экономика России укрепляет тенденции восстановления. Инфляция приближается к целевому уровню.'
    },
    (2026, 10): {
        'inflation': 4.85, 'retail_trade': 102.7, 'unemployment': 1.8,
        'usd_rate': 74.78, 'car_sales': 91234, 'car_growth': 6.8,
        'assessment': 'Экономика России демонстрирует уверенный рост. Потребительский спрос и промышленное производство находятся на высоком уровне.'
    },
    (2026, 11): {
        'inflation': 4.72, 'retail_trade': 103.0, 'unemployment': 1.8,
        'usd_rate': 74.12, 'car_sales': 93456, 'car_growth': 7.5,
        'assessment': 'Российская экономика продолжает развитие при стабильных темпах роста. Реальные доходы населения увеличиваются.'
    },
    (2026, 12): {
        'inflation': 4.60, 'retail_trade': 103.3, 'unemployment': 1.7,
        'usd_rate': 73.56, 'car_sales': 98765, 'car_growth': 8.2,
        'assessment': 'По итогам 2026 года экономика России показала уверенное восстановление. Основные макроэкономические показатели значительно улучшились.'
    }
}


def init_database():
    """Create and populate the economic data database"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Удалена существующая база данных: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_reports (
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                inflation REAL NOT NULL,
                retail_trade REAL NOT NULL,
                unemployment REAL NOT NULL,
                usd_rate REAL NOT NULL,
                car_sales INTEGER NOT NULL,
                car_growth REAL NOT NULL,
                assessment TEXT NOT NULL,
                PRIMARY KEY (year, month),
                CHECK (month >= 1 AND month <= 12)
            )
        """)

        records = []
        for (year, month), data in ECONOMIC_DATA.items():
            records.append((
                year, month,
                data['inflation'], data['retail_trade'], data['unemployment'],
                data['usd_rate'], data['car_sales'], data['car_growth'],
                data['assessment']
            ))

        cursor.executemany("""
            INSERT INTO monthly_reports
            (year, month, inflation, retail_trade, unemployment, usd_rate, car_sales, car_growth, assessment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM monthly_reports")
        count = cursor.fetchone()[0]
        print(f"✓ База данных создана: {DB_PATH}")
        print(f"✓ Записей добавлено: {count}")
        print(f"\nДоступные периоды:")
        cursor.execute("SELECT DISTINCT year FROM monthly_reports ORDER BY year")
        years = [row[0] for row in cursor.fetchall()]
        for year in years:
            cursor.execute("SELECT COUNT(*) FROM monthly_reports WHERE year=?", (year,))
            months_count = cursor.fetchone()[0]
            print(f"  {year}: {months_count} месяцев")


if __name__ == "__main__":
    init_database()
