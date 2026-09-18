import os
from report_generator import ReportGenerator

def main():
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    years = ReportGenerator.get_available_years()
    for year in years:
        months = ReportGenerator.get_available_months(year)
        for month in months:
            print(f"Generating report for {year}-{month:02d}...")
            report = ReportGenerator.generate_report(year, month)
            filename = f"report_{year}_{month:02d}.txt"
            filepath = os.path.join(reports_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Saved {filepath}")

if __name__ == "__main__":
    main()
