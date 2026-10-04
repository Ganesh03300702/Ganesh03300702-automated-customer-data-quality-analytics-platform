import re
import pandas as pd


def normalize_columns(df):
    out = df.copy()
    seen = {}
    cols = []
    for c in out.columns:
        name = re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_") or "column"
        seen[name] = seen.get(name, 0) + 1
        cols.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    out.columns = cols
    for c in out.select_dtypes(include=["object", "string"]).columns:
        out[c] = out[c].astype("string").str.strip()
    return out


def semantic_column(name):
    n = name.lower()
    if re.search(r"(^|_)(email|e_mail)(_|$)", n): return "email"
    if re.search(r"(^|_)(phone|mobile|telephone|contact)(_|$)", n): return "phone"
    if re.search(r"(^|_)(date|dob|registration|created|updated|timestamp)(_|$)", n): return "date"
    if re.search(r"(^|_)(age)(_|$)", n): return "age"
    if re.search(r"(^|_)(quantity|qty|amount|price|salary|score|value|total)(_|$)", n): return "numeric"
    if re.search(r"(^|_)(status|state|category|type|gender|country|city)(_|$)", n): return "categorical"
    if re.search(r"(^|_)(id|code|key)(_|$)", n): return "identifier"
    return "generic"


def process_dataframe(df):
    df = normalize_columns(df)
    result = df.copy()
    issues = [[] for _ in range(len(result))]
    checks = []

    # Missing values: generic and applicable to every dataset.
    missing_mask = result.isna() | result.astype("string").apply(lambda s: s.str.strip().eq(""))
    for i in range(len(result)):
        cols = list(result.columns[missing_mask.iloc[i]])
        if cols:
            issues[i].append("Missing values: " + ", ".join(cols[:8]) + ("..." if len(cols) > 8 else ""))
    if missing_mask.any().any(): checks.append("Missing-value detection")

    # Duplicate complete rows.
    dup = result.duplicated(keep=False)
    for i in result.index[dup]:
        issues[i].append("Duplicate row")
    if dup.any(): checks.append("Duplicate-row detection")

    # Candidate identifier duplicate check.
    id_cols = [c for c in result.columns if semantic_column(c) == "identifier"]
    if id_cols:
        checks.append("Identifier duplicate detection")
        for c in id_cols:
            mask = result[c].notna() & result[c].duplicated(keep=False)
            for i in result.index[mask]:
                issues[i].append(f"Duplicate identifier in {c}")

    for c in result.columns:
        kind = semantic_column(c)
        if kind == "email":
            checks.append("Email format validation")
            mask = result[c].notna() & ~result[c].astype(str).str.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", na=False)
            for i in result.index[mask]: issues[i].append(f"Invalid email format in {c}")
        elif kind == "phone":
            checks.append("Phone format validation")
            digits = result[c].astype("string").str.replace(r"\D", "", regex=True)
            mask = result[c].notna() & ((digits.str.len() < 7) | (digits.str.len() > 15))
            for i in result.index[mask]: issues[i].append(f"Invalid phone format in {c}")
        elif kind == "date":
            checks.append("Date validation")
            parsed = pd.to_datetime(result[c], errors="coerce")
            mask = result[c].notna() & parsed.isna()
            for i in result.index[mask]: issues[i].append(f"Invalid date in {c}")
        elif kind == "age":
            checks.append("Age range validation")
            nums = pd.to_numeric(result[c], errors="coerce")
            mask = result[c].notna() & ((nums.isna()) | (nums < 0) | (nums > 120))
            for i in result.index[mask]: issues[i].append(f"Invalid age in {c}")
        elif kind == "numeric":
            checks.append("Numeric consistency validation")
            nums = pd.to_numeric(result[c], errors="coerce")
            mask = result[c].notna() & nums.isna()
            for i in result.index[mask]: issues[i].append(f"Non-numeric value in {c}")

    # Deduplicate check labels.
    checks = list(dict.fromkeys(checks))
    result["quality_issues"] = ["; ".join(x) for x in issues]
    result["classification"] = ["Valid" if not x else ("Review Required" if any("Missing" in e or "Duplicate" in e for e in x) else "Invalid") for x in issues]

    profile_rows = []
    for c in result.columns:
        if c in {"classification", "quality_issues"}: continue
        profile_rows.append({
            "column": c,
            "detected_type": semantic_column(c),
            "pandas_dtype": str(result[c].dtype),
            "non_null": int(result[c].notna().sum()),
            "missing": int(result[c].isna().sum()),
            "unique": int(result[c].nunique(dropna=True)),
        })
    profile = pd.DataFrame(profile_rows)
    quality = {
        "missing_cells": int(missing_mask.sum().sum()),
        "duplicate_rows": int(dup.sum()),
        "valid_records": int((result["classification"] == "Valid").sum()),
        "invalid_records": int((result["classification"] == "Invalid").sum()),
        "review_records": int((result["classification"] == "Review Required").sum()),
        "checks_applied": checks,
    }
    return {"data": result, "profile": profile, "quality": quality}
