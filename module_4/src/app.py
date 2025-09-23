
from flask import Flask, render_template, redirect, url_for, flash
import threading
import os
import psycopg2

app = Flask(__name__)

app.secret_key = "dev"   # any non-empty string is fine for class use

def one(cur, sql):
    cur.execute(sql)
    row = cur.fetchone()
    return row[0] if row else None

def get_conn():
    host = os.environ.get("PGHOST", "localhost")
    port = int(os.environ.get("PGPORT", "5432"))
    dbname = os.environ.get("PGDATABASE", "applicants")
    user = os.environ.get("PGUSER", "postgres")
    password = os.environ.get("PGPASSWORD", "Pr0m3th3u$")
    return psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)

@app.route("/")
def index():
    with get_conn() as conn:
        with conn.cursor() as cur:
            # The following SQL mirrors query_data.py exactly.
            q1 = one(cur, """
                SELECT COUNT(*) FROM applicants
                WHERE term = 'Fall 2025'
            """)
            total = one(cur, "SELECT COUNT(*) FROM applicants")
            intl = one(cur, """
                SELECT COUNT(*) FROM applicants
                WHERE us_or_international = 'International'
            """)
            pct_intl = round((intl / total) * 100, 2) if total else 0.0

            avg_gpa = one(cur, "SELECT AVG(gpa) FROM applicants WHERE gpa IS NOT NULL")
            avg_gre = one(cur, "SELECT AVG(gre) FROM applicants WHERE gre IS NOT NULL")
            avg_gre_v = one(cur, "SELECT AVG(gre_v) FROM applicants WHERE gre_v IS NOT NULL")
            avg_gre_aw = one(cur, "SELECT AVG(gre_aw) FROM applicants WHERE gre_aw IS NOT NULL")

            avg_gpa_us_fall2025 = one(cur, """
                SELECT AVG(gpa) FROM applicants
                WHERE (us_or_international = 'US' OR us_or_international = 'American')
                  AND term = 'Fall 2025' AND gpa IS NOT NULL
            """)

            fall_total = one(cur, "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2025'")
            fall_accept = one(cur, """
                SELECT COUNT(*) FROM applicants
                WHERE term = 'Fall 2025' AND status = 'Accepted'
            """)
            pct_fall_accept = round((fall_accept / fall_total) * 100, 2) if fall_total else 0.0

            avg_gpa_fall_accepted = one(cur, """
                SELECT AVG(gpa) FROM applicants
                WHERE term = 'Fall 2025' AND status = 'Accepted' AND gpa IS NOT NULL
            """)

            jhu_ms_cs = one(cur, """
                SELECT COUNT(*) FROM applicants
                WHERE (llm_generated_university = 'johns hopkins' OR llm_generated_university = 'jhu')
                  AND llm_generated_program = 'computer science'
                  AND degree = 'Masters'
            """)

            gtown_phd_cs_2025_accept = one(cur, """
                SELECT COUNT(*) FROM applicants
                WHERE term = '2025'
                  AND status = 'Accepted'
                  AND llm_generated_university = 'georgetown'
                  AND llm_generated_program = 'computer science'
                  AND degree = 'PhD'
            """)
            
            berkeley = one(cur, """
                SELECT COUNT(*) FROM applicants
                WHERE term = 'Fall 2025'
                    AND status = 'Accepted'
                    AND llm_generated_university = 'University of California, Berkeley'
            """)

            rejected = one(cur, """
                SELECT COUNT(*) FROM applicants
                WHERE term = 'Fall 2025'
                    AND status = 'Rejected'
            """)

    return render_template("index.html",
        q1=q1,
        pct_intl=pct_intl,
        avg_gpa=avg_gpa, avg_gre=avg_gre, avg_gre_v=avg_gre_v, avg_gre_aw=avg_gre_aw,
        avg_gpa_us_fall2025=avg_gpa_us_fall2025,
        pct_fall_accept=pct_fall_accept,
        avg_gpa_fall_accepted=avg_gpa_fall_accepted,
        jhu_ms_cs=jhu_ms_cs,
        gtown_phd_cs_2025_accept=gtown_phd_cs_2025_accept,
        berkeley=berkeley,
        rejected=rejected
    )

is_scraping = False

@app.route("/pull-data")
def pull_data():
    global is_scraping
    if is_scraping:
        flash("A pull is already running, please wait.")
        return redirect(url_for("index"))

    def scrape_job():
        global is_scraping
        is_scraping = True
        try:
            # Where I call my module2 scraper
            print("running scraper...")
        finally:
            is_scraping = False

    threading.Thread(target=scrape_job).start()
    flash("Pull Data started. Refresh later to see updates.")
    return redirect(url_for("index"))

@app.route("/update-analysis")
def update_analysis():
    global is_scraping
    if is_scraping:
        flash("Cannot update analysis while Pull Data is running.")
        return redirect(url_for("index"))
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
