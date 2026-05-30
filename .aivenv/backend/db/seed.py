from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY,
    product TEXT,
    region TEXT,
    revenue INTEGER,
    date TEXT
)
""")

data = [
    ("Laptop", "India", 50000, "2024-01-01"),
    ("Phone", "US", 30000, "2024-01-02"),
    ("Tablet", "India", 20000, "2024-01-03"),
]

cursor.executemany(
    "INSERT INTO sales (product, region, revenue, date) VALUES (?, ?, ?, ?)",
    data
)

conn.commit()
conn.close()
