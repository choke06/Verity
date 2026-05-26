from bs4 import BeautifulSoup

def dedupe_claims(claims):
    seen = set()
    deduped = []

    for attr, value in claims:
        if not attr or value is None:
            continue

        key = (
            str(attr).strip().lower(),
            str(value).strip().lower()
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append((attr, value))

    return deduped


def is_valid_spec_table(rows):

    if not rows:
        return False

    keys = [
        str(k).lower().strip()
        for k, _ in rows
    ]

    unique_keys = len(set(keys))

    repeated_ratio = 1 - (
        unique_keys / max(len(keys), 1)
    )

    if repeated_ratio > 0.6:
        return False

    return True


def extract_generic_html_specs(html):
    generic_specs = []

    if not html:
        return generic_specs

    print("\n=== GENERIC HTML DEBUG ===")
    print(html[:10000])

    soup = BeautifulSoup(html, "lxml")

    tables = soup.find_all("table")

    for table in tables:

        table_specs = []

        rows = table.find_all("tr")

        for row in rows:

            th = row.find("th")
            td = row.find("td")

            if th and td:

                label = th.get_text(" ", strip=True)
                value = td.get_text(" ", strip=True)

                if not label or not value:
                    continue

                if len(label) > 200 or len(value) > 500:
                    continue

                table_specs.append((label, value))
                continue

            cols = [
                c.get_text(" ", strip=True)
                for c in row.find_all(["td", "th"])
            ]

            cols = [c for c in cols if c]

            if len(cols) < 2:
                continue

            if len(cols) % 2 != 0:
                continue

            for i in range(0, len(cols) - 1, 2):

                label = cols[i]
                value = cols[i + 1]

                if not label or not value:
                    continue

                if len(label) > 200 or len(value) > 500:
                    continue

                table_specs.append((label, value))

        if is_valid_spec_table(table_specs):
            generic_specs.extend(table_specs)

    cards = soup.select(
        ".full-specifications__specifications-single-card"
    )

    for card in cards:

        rows = card.select(
            ".full-specifications__specifications-single-card__sub-list"
        )

        for row in rows:

            name_el = row.select_one(
                ".full-specifications__specifications-single-card__sub-list__name"
            )

            value_el = row.select_one(
                ".full-specifications__specifications-single-card__sub-list__value"
            )

            if not name_el or not value_el:
                continue

            label = name_el.get_text(" ", strip=True)
            value = value_el.get_text(" ", strip=True)

            if not label or not value:
                continue

            generic_specs.append((label, value))

    spec_rows = soup.select("""
        li,
        .spec-row,
        .specs-row,
        .spec-item,
        .specifications-row,
        .techSpec,
        .tech-spec,
        .attribute,
        .feature,
        .details-row
    """)

    for row in spec_rows:

        label = None
        value = None

        label_el = row.select_one("""
            .label,
            .name,
            .title,
            .spec-name,
            .attribute-label,
            dt
        """)

        value_el = row.select_one("""
            .value,
            .spec-value,
            .attribute-value,
            dd
        """)

        if label_el and value_el:

            label = label_el.get_text(" ", strip=True)
            value = value_el.get_text(" ", strip=True)
    
        else:

            text = row.get_text(" | ", strip=True)

            parts = [
                p.strip()
                for p in text.split("|")
                if p.strip()
            ]

            if len(parts) >= 2:
                label = parts[0]
                value = parts[1]

        if not label or not value:
            continue

        if len(label) > 200 or len(value) > 500:
            continue
 
        generic_specs.append((label, value))

    return dedupe_claims(generic_specs)


def clean_html(text):
    if not text:
        return ""

    clean = re.sub(r"<.*?>", "", text)

    if ":" in clean:
        parts = clean.split(":", 1)
        if len(parts[0]) < 40:
            clean = parts[1]

    return clean.strip()