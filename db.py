import sqlite3
import time
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "verity_v1.db"

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def safe_execute(conn, query, params=()):
    for _ in range(5):
        try:
            return conn.execute(query, params)

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                return None
            raise

        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                time.sleep(0.3)
                continue
            raise

def get_db():
    print("USING DB:", DB_PATH)
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def get_domain(url):
    host = urlparse(url).netloc.lower()
    host = host.replace("www.", "")

    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])

    return host

def is_valid_model(model: str) -> bool:
    if not model:
        return False

    model = model.strip()

    if len(model) > 25:
        return False

    if not re.search(r"[A-Z]", model, re.I):
        return False
    if not re.search(r"\d", model):
        return False

    if re.fullmatch(r"[A-Za-z0-9]{15,}", model):
        return False

    return True

def normalize_url(url):
    if not url:
        return ""

    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/")

    keep_keys = {
        "id", "sku", "skuid", "pid", "productid",
        "model", "mpn", "upc", "ean", "gtin", "asin"
    }

    filtered_query = []
    for k, v in parse_qsl(parsed.query, keep_blank_values=False):
        key = k.lower().strip()
        if key in keep_keys and v:
            filtered_query.append((key, v.strip()))

    filtered_query.sort()

    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        "",
        urlencode(filtered_query, doseq=True),
        ""
    ))

def initialize_database():
    conn = get_db()

    safe_execute(conn, """
    CREATE TABLE IF NOT EXISTS pending_crawl (
        url TEXT PRIMARY KEY,
        domain TEXT,
        category TEXT,
        priority INTEGER,
        status TEXT,
        discovered_at TEXT
    )
    """)

    safe_execute(conn, """
    CREATE TABLE IF NOT EXISTS crawled_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        domain TEXT,
        crawl_ts TEXT,
        status TEXT
    )
    """)

    safe_execute(conn, """
    CREATE TABLE IF NOT EXISTS raw_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT,
        page_id INTEGER,
        source_id INTEGER,
        attribute TEXT,
        value_string TEXT,
        value_numeric TEXT,
        unit TEXT,
        UNIQUE(product_id, source_id, attribute, value_string),
        FOREIGN KEY (page_id) REFERENCES crawled_pages(id),
        FOREIGN KEY (source_id) REFERENCES sources(id)
    ) 
    """)

    safe_execute(conn, """
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT UNIQUE,
        brand TEXT,
        source_type TEXT,
        initial_reliability REAL,
        learned_reliability REAL,
        crawl_priority INTEGER
    )
    """)

    safe_execute(conn, """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        brand TEXT,
        title TEXT,
        gtin TEXT UNIQUE,
        price REAL,
        image_url TEXT,
        verified_specs TEXT
    )
    """)

    safe_execute(conn, """
    CREATE TABLE IF NOT EXISTS product_prices (
        gtin TEXT,
        domain TEXT,
        price REAL,
        url TEXT,
        last_seen TEXT,
        PRIMARY KEY (gtin, domain)
    )
    """)

    safe_execute(conn, """
    CREATE INDEX IF NOT EXISTS idx_pending_status
    ON pending_crawl(status)
    """)

    safe_execute(conn, """
    CREATE INDEX IF NOT EXISTS idx_claims_product_id
    ON raw_claims(product_id)
    """)

    safe_execute(conn, """
    CREATE INDEX IF NOT EXISTS idx_claims_page_id
    ON raw_claims(page_id)
    """)

    safe_execute(conn, """
    CREATE INDEX IF NOT EXISTS idx_claims_source_id
    ON raw_claims(source_id)
    """)

    conn.commit()
    conn.close()

def count_urls(conn, category):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(DISTINCT url) FROM pending_crawl WHERE category = ?",
        (category,)
    )
    return cursor.fetchone()[0]

def save_url(conn, url, category, priority=5, provider=None):
    url = normalize_url(url)
    domain = get_domain(url)

    safe_execute(conn, """
        INSERT OR IGNORE INTO pending_crawl
        (url, domain, category, priority, status, discovered_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (url, domain, category, priority, utcnow()))

    upsert_source(conn, domain)

    conn.commit()

def get_pending(conn, limit=10):
    rows = conn.execute(
        """
        SELECT url, category
        FROM pending_crawl
        WHERE status IN ('pending', 'failed', 'unresolved')
        ORDER BY id ASC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()

    for row in rows:
        safe_execute(conn,
            "UPDATE pending_crawl SET status='processing' WHERE url=?",
            (row["url"],)
        )

    return rows

def get_product_urls(conn, limit=500):
    rows = conn.execute("""
        SELECT DISTINCT product_id
        FROM raw_claims
        WHERE product_id LIKE 'http%'
        LIMIT ?
    """, (limit,)).fetchall()

    return [r["product_id"] for r in rows]

def reset_product_urls(conn, limit=500):
    rows = conn.execute("""
        SELECT DISTINCT rc.product_id
        FROM raw_claims rc
        LEFT JOIN products p
            ON rc.product_id = p.gtin
        WHERE rc.product_id LIKE 'http%'
        LIMIT ?
    """, (limit,)).fetchall()

    reset = 0

    for r in rows:
        url = normalize_url(r["product_id"])

        updated = conn.execute("""
            UPDATE pending_crawl
            SET status='pending'
            WHERE url=?
            AND status='completed'
            AND url IN (
                SELECT DISTINCT product_id
                FROM raw_claims
                WHERE product_id NOT LIKE 'http%'
            )
        """, (url,))

        if updated.rowcount > 0:
            reset += 1

    print(f"[RESET PRODUCT URLS] reset={reset}")
    conn.commit()

def mark_processing(conn, url):
    safe_execute(conn,
        "UPDATE pending_crawl SET status='processing' WHERE url=?",
        (url,)
    )

def mark_complete(conn, url):
    safe_execute(conn,
        "UPDATE pending_crawl SET status='completed' WHERE url=?",
        (url,)
    )

def mark_failed(conn, url):
    safe_execute(conn,
        "UPDATE pending_crawl SET status='failed' WHERE url=?",
        (url,)
    )

def mark_unresolved(conn, url):
    conn.execute(
        "UPDATE pending_crawl SET status='unresolved' WHERE url=?",
        (url,)
    )
    conn.commit()

def log_crawl(conn, url, status):
    domain = get_domain(url)

    row = conn.execute(
        "SELECT id FROM crawled_pages WHERE url=?",
        (url,)
    ).fetchone()

    if row:
        return row["id"]

    safe_execute(conn, """
        INSERT INTO crawled_pages (url, domain, crawl_ts, status)
        VALUES (?, ?, ?, ?)
    """, (url, domain, utcnow(), status))

    row = conn.execute("SELECT last_insert_rowid()").fetchone()
    return row[0]

def insert_claim(conn, page_id, source_id, attribute, value_string, product_id=None, unit=None, value_numeric=None):
    safe_execute(conn, """
        INSERT OR IGNORE INTO raw_claims
        (product_id, page_id, source_id, attribute, value_string, value_numeric, unit)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        product_id,
        page_id,
        source_id,
        attribute,
        value_string,
        value_numeric,
        unit
    ))

def upsert_source(conn, domain, score=0.5, source_type=None):
    safe_execute(conn, """
        INSERT INTO sources (domain, source_type, initial_reliability, learned_reliability, crawl_priority)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(domain) DO NOTHING
    """, (domain, source_type or "unknown", score, score, 5))

def update_source_score(conn, domain, score):
    safe_execute(conn,
        "UPDATE sources SET learned_reliability=? WHERE domain=?",
        (score, domain)
    )

def upsert_product(conn, product):

    incoming_model = product.get("model")
    incoming_gtin = product.get("gtin")

    if incoming_model and incoming_gtin and is_valid_model(incoming_model):
        row = conn.execute(
            "SELECT id, gtin FROM products WHERE model=? LIMIT 1",
            (incoming_model,)
        ).fetchone()

        if row and not row["gtin"]:
            safe_execute(conn,
                "UPDATE products SET gtin=? WHERE id=?",
                (incoming_gtin, row["id"])
            )
            print(f"[MODEL MATCH → FILLED GTIN] {incoming_model} → {incoming_gtin}")
            conn.commit()
            return

    if not incoming_gtin and incoming_model:
        row = conn.execute(
            "SELECT gtin FROM products WHERE model=? AND gtin IS NOT NULL LIMIT 1",
            (incoming_model,)
        ).fetchone()

        if row:
            product["gtin"] = row["gtin"]
            incoming_gtin = row["gtin"]
            print(f"[MODEL MATCH → GTIN] {incoming_model} → {incoming_gtin}")

    existing = None
    if incoming_gtin:
        existing = conn.execute(
            "SELECT model FROM products WHERE gtin=?",
            (incoming_gtin,)
        ).fetchone()

    existing_model = existing["model"] if existing else None

    if existing_model:
        if not is_valid_model(existing_model) and is_valid_model(incoming_model):
            print(f"[MODEL FIXED] {existing_model} → {incoming_model}")
            final_model = incoming_model
        else:
            final_model = existing_model
    else:
        final_model = incoming_model

    safe_execute(conn, """
        INSERT INTO products (model, brand, title, gtin, image_url)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(gtin) DO UPDATE SET
            model = ?,
            brand = COALESCE(products.brand, excluded.brand),
            title = COALESCE(products.title, excluded.title),
            image_url = COALESCE(products.image_url, excluded.image_url)
    """, (
        final_model,
        product.get("brand"),
        product.get("title"),
        incoming_gtin,
        product.get("image_url"),
        final_model
    ))

    conn.commit()

def upsert_price(conn, data):
    gtin = data.get("gtin")
    domain = data.get("domain")
    price = data.get("price")
    url = data.get("url")

    if not gtin or not domain or price is None:
        return

    safe_execute(conn, """
        INSERT INTO product_prices (gtin, domain, price, url, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(gtin, domain) DO UPDATE SET
            price=excluded.price,
            url=excluded.url,
            last_seen=excluded.last_seen
    """, (
        gtin,
        domain,
        price,
        url,
        utcnow()
    ))

    conn.commit()

def get_existing_attributes_for_category(category):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT attribute, unit
        FROM raw_claims
        WHERE attribute IS NOT NULL
    """)

    results = []
    for row in cursor.fetchall():
        results.append({
            "attribute": row[0],
            "unit": row[1]
        })

    conn.close()
    return results