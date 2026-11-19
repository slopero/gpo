import os
import glob
import re

RU_MONTHS = {
    'январь': 1, 'января': 1, 'январе': 1,
    'февраль': 2, 'февраля': 2, 'феврале': 2,
    'март': 3, 'марта': 3, 'марте': 3,
    'апрель': 4, 'апреля': 4, 'апреле': 4,
    'май': 5, 'мая': 5, 'мае': 5,
    'июнь': 6, 'июня': 6, 'июне': 6,
    'июль': 7, 'июля': 7, 'июле': 7,
    'август': 8, 'августа': 8, 'августе': 8,
    'сентябрь': 9, 'сентября': 9, 'сентябре': 9,
    'октябрь': 10, 'октября': 10, 'октябре': 10,
    'ноябрь': 11, 'ноября': 11, 'ноябре': 11,
    'декабрь': 12, 'декабря': 12, 'декабре': 12
}

EN_MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'octover': 10,
    'november': 11, 'december': 12
}

KNOWN_BRANDS = [
    "Lada", "Avtovaz", "KIA", "Kia", "Hyundai", "Renault", "Toyota", "VW", "Volkswagen",
    "Škoda", "Skoda", "ГАЗ", "Nissan", "УАЗ", "UAZ", "Mercedes-Benz", "BMW", "Mazda",
    "Mitsubishi", "Lexus", "Haval", "Datsun", "Audi", "Ford", "Chevrolet", "Geely",
    "Chery", "Changan", "Peugeot", "Citroën", "Citroen", "Subaru", "Exeed", "Omoda",
    "Tank", "Jaecoo", "GAC", "FAW", "Sollers", "Great Wall", "Evolute", "Livan"
]

def extract_auto_stats(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    
    total_sales = None
    brands = []
    models = []
    
    # 1. Total sales
    for line in lines:
        if any(w in line.lower() for w in ['итого (амс)', 'итого (ао «ппк»)', 'итого']) and not total_sales:
            nums = re.findall(r'\b\d[\d\s,.]*\b', line)
            for n in nums:
                clean = int(re.sub(r'[^\d]', '', n) or 0)
                if 10000 <= clean <= 3000000:
                    total_sales = clean
                    break

    # 2. Models table (Top 10)
    # Looking for lines like: "1 Granta Lada 19 899" or rank pattern
    for i, line in enumerate(lines):
        if "САМЫХ ПРОДАВАЕМЫХ" in line.upper() or ("МОДЕЛЬ" in line.upper() and "МАРКА" in line.upper()):
            # Table follows
            for j in range(i + 1, min(i + 80, len(lines))):
                row = lines[j]
                m = re.match(r'^(\d{1,2})\s+([A-Za-z0-9А-Яа-я\-\.\s\/\'\"]+?)\s+([A-Za-zА-Яа-я\-\s]+?)\s+(\d[\d\s]*\d|\d)', row)
                if m:
                    rank = int(m.group(1))
                    model_name = m.group(2).strip()
                    brand_name = m.group(3).strip()
                    sales_str = re.sub(r'[^\d]', '', m.group(4))
                    if sales_str:
                        sales_val = int(sales_str)
                        if 1 <= rank <= 10 and sales_val > 50:
                            models.append((rank, f"{brand_name} {model_name}", sales_val))
            if models:
                break

    models.sort(key=lambda x: x[0])
    top_models = [(name, val) for rank, name, val in models[:10]]

    # 3. Brands table (Top 5)
    for line in lines:
        for b in KNOWN_BRANDS:
            if line.startswith(b) or f" {b} " in f" {line} ":
                # line like "Lada 35 572 188 645 87%" or "KIA 18 007 18 081"
                parts = line.split()
                # find numbers in line
                num_vals = []
                for p in parts[1:]:
                    val_str = re.sub(r'[^\d]', '', p)
                    if val_str and val_str.isdigit():
                        v = int(val_str)
                        if 100 <= v <= 1000000:
                            num_vals.append(v)
                if num_vals:
                    # check brand not already added
                    if not any(b_name.lower() == b.lower() for b_name, _ in brands):
                        brands.append((b, num_vals[0]))
                break

    brands.sort(key=lambda x: x[1], reverse=True)
    top_brands = brands[:5]

    return total_sales, top_brands, top_models

def main():
    base_dir = os.path.dirname(__file__)
    sample_file = os.path.join(base_dir, "aeb_rus_sales_data", "text", "RUS-Car-Sales-in-April-2023.txt")
    total, brands, models = extract_auto_stats(sample_file)
    print("TOTAL SALES:", total)
    print("TOP BRANDS:", brands)
    print("TOP MODELS:", models)

if __name__ == "__main__":
    main()
