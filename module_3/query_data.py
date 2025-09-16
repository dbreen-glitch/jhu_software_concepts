
# query_data.py
# Minimal script: connect to PostgreSQL and answer 8 questions against the 'applicants' table.
# No error handling or data cleaning; expects the schema and values to be consistent.

import psycopg2

host = input("PostgreSQL host [localhost]: ").strip() or "localhost"
port = int(input("PostgreSQL port [5432]: ").strip() or "5432")
dbname = input("Database name: ").strip()
user = input("User: ").strip()
password = input("Password: ").strip()

conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
cur = conn.cursor()

def one(sql, params=None):
    cur.execute(sql, params or ())
    return cur.fetchone()[0]

print("\nAnswers:\n")

# 1) How many entries applied for Fall 2025?
q1 = one("""
    SELECT COUNT(*) FROM applicants
    WHERE term = 'Fall 2025'
""")
print(f"1) Entries applied for Fall 2025: {q1}")

# 2) Percentage of entries that are international (not American or Other)
#    Here we treat values marked 'international' (case-insensitive) as international.
#    Everything else is considered non-international.
total = one("SELECT COUNT(*) FROM applicants")
intl = one("""
    SELECT COUNT(*) FROM applicants
    WHERE us_or_international = 'International'
""")
pct_intl = round((intl / total) * 100, 2) if total else 0.0
print(f"2) % International (not American/Other): {pct_intl:.2f}%")

# 3) Average GPA, GRE, GRE V, GRE AW for applicants who provide these metrics (non-null)
avg_gpa = one("SELECT AVG(gpa) FROM applicants WHERE gpa IS NOT NULL")
avg_gre = one("SELECT AVG(gre) FROM applicants WHERE gre IS NOT NULL")
avg_gre_v = one("SELECT AVG(gre_v) FROM applicants WHERE gre_v IS NOT NULL")
avg_gre_aw = one("SELECT AVG(gre_aw) FROM applicants WHERE gre_aw IS NOT NULL")
print(f"3) Averages — GPA: {avg_gpa}, GRE: {avg_gre}, GRE V: {avg_gre_v}, GRE AW: {avg_gre_aw}")

# 4) Average GPA of American students in Fall 2025
avg_gpa_us_fall2025 = one("""
    SELECT AVG(gpa) FROM applicants
    WHERE (us_or_international = 'US' OR us_or_international = 'American')
      AND term = 'Fall 2025' AND gpa IS NOT NULL
""")
print(f"4) Avg GPA of American students in Fall 2025: {avg_gpa_us_fall2025}")

# 5) Percent of entries for Fall 2025 that are Acceptances
fall_total = one("SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2025'")
fall_accept = one("""
    SELECT COUNT(*) FROM applicants
    WHERE term = 'Fall 2025' AND status = 'Accepted'
""")
pct_fall_accept = round((fall_accept / fall_total) * 100, 2) if fall_total else 0.0
print(f"5) % of Fall 2025 entries that are Acceptances: {pct_fall_accept:.2f}%")

# 6) Average GPA of applicants who applied for Fall 2025 who are Acceptances
avg_gpa_fall_accepted = one("""
    SELECT AVG(gpa) FROM applicants
    WHERE term = 'Fall 2025' AND status = 'Accepted' AND gpa IS NOT NULL
""")
print(f"6) Avg GPA of Fall 2025 Acceptances: {avg_gpa_fall_accepted}")

# 7) How many entries are from applicants who applied to JHU for a masters in Computer Science?
#    Using normalized fields if available: llm_generated_university and llm_generated_program.
#    Masters assumed degree = 2.
jhu_ms_cs = one("""
    SELECT COUNT(*) FROM applicants
    WHERE (llm_generated_university = 'johns hopkins' OR llm_generated_university = 'jhu')
      AND llm_generated_program = 'computer science'
      AND degree = 'Masters'
""")
print(f"7) Entries for JHU MS in Computer Science: {jhu_ms_cs}")

# 8) How many entries from 2025 are acceptances from applicants who applied to Georgetown University for a PhD in CS?
#    Year determined from term containing '2025'. PhD assumed degree = 3.
gtown_phd_cs_2025_accept = one("""
    SELECT COUNT(*) FROM applicants
    WHERE term = '2025'
      AND status = 'Accepted'
      AND llm_generated_university = 'georgetown'
      AND llm_generated_program = 'computer science'
      AND degree = 'PhD'
""")
print(f"8) 2025 Acceptances at Georgetown for PhD in CS: {gtown_phd_cs_2025_accept}")

cur.close()
conn.close()
