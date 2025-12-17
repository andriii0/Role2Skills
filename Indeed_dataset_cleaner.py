import argparse
import html
import re

import pandas as pd
from bs4 import BeautifulSoup


def clean_html_text(text: str) -> str:
    """Убираем HTML, entity и лишние пробелы из текста."""
    if pd.isna(text):
        return ""
    text = str(text)

    # раскодируем HTML-сущности (&amp; -> &, &nbsp; -> пробел и т.п.)
    text = html.unescape(text)

    # убираем HTML-теги
    soup = BeautifulSoup(text, "lxml")
    text = soup.get_text(separator=" ")

    # сжимаем пробелы и переводы строк
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_salary_column(series: pd.Series) -> pd.Series:
    """Приводим колонку зарплаты к числам, всё лишнее в NaN."""
    # в строку
    series = series.astype(str)

    # убираем всё, кроме цифр, точки и запятой
    # если там диапазоны типа "50,000 - 70,000", мы сохраняем только первую часть
    series = series.str.replace(r"[^0-9.,]", "", regex=True)

    # если есть запятая — убираем её (50,000 -> 50000)
    series = series.str.replace(",", "", regex=False)

    # если вдруг осталась пустая строка — в NaN
    series = series.replace("", pd.NA)

    # конвертим в число, всё, что не похоже на число -> NaN
    series = pd.to_numeric(series, errors="coerce")

    return series


def main(input_path: str, output_path: str):
    print(f"[+] Loading raw dataset from: {input_path}")
    df_raw = pd.read_csv(input_path)

    # Какие колонки мы хотим использовать (если каких-то нет — просто пропустятся)
    col_map = {
        "Job Title": "title",
        "Job Description": "description",
        "Company Name": "company",
        "Location": "location_raw",
        "City": "city",
        "State": "state",
        "Country": "country",
        "Zip Code": "zip_code",
        "Salary From": "salary_from",
        "Salary To": "salary_to",
        "Salary Period": "salary_period",
        "Industry": "industry",
        "Employees": "employees",
    }

    present_raw_cols = [c for c in col_map.keys() if c in df_raw.columns]
    if not present_raw_cols:
        raise ValueError("Не нашёл ни одной ожидаемой колонки в CSV. Проверь структуру файла.")

    df = df_raw[present_raw_cols].copy()
    df = df.rename(columns={old: new for old, new in col_map.items() if old in df.columns})

    print(f"[+] Selected {len(df)} rows and {len(df.columns)} columns")

    # Чистим текстовые поля
    text_cols = [c for c in ["title", "description", "company", "location_raw",
                             "city", "state", "country", "industry"]
                 if c in df.columns]

    print(f"[+] Cleaning text columns: {', '.join(text_cols)}")
    for col in text_cols:
        df[col] = df[col].astype(str).apply(clean_html_text)

    # Убираем строки с слишком коротким описанием (если нужно)
    if "description" in df.columns:
        before = len(df)
        df = df[df["description"].str.len() > 20].reset_index(drop=True)
        print(f"[+] Dropped {before - len(df)} rows with too short descriptions")

    # Чистим salary_from / salary_to, если есть
    for col in ["salary_from", "salary_to"]:
        if col in df.columns:
            print(f"[+] Cleaning salary column: {col}")
            df[col] = clean_salary_column(df[col])

    print(f"[+] Saving cleaned dataset to: {output_path}")
    df.to_csv(output_path, index=False)
    print("[+] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean Indeed job dataset")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/indeed_dataset.csv",
        help="Path to raw Indeed CSV (default: indeed_dataset.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/indeed_clean.csv",
        help="Path for cleaned CSV (default: indeed_clean.csv)",
    )

    args = parser.parse_args()
    main(args.input, args.output)