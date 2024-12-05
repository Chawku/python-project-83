def add_url(conn, url):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM urls WHERE name = %s;", (url,))
        result = cur.fetchone()
        if result:
            return result[0], "Страница уже существует", "alert alert-danger"
        cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id;", (url,))
        conn.commit()
        return cur.fetchone()[0], "Страница успешно добавлена", "alert alert-success"


def get_urls_list(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT u.id, u.name, COALESCE(uc.status_code, ''), uc.created_at
            FROM urls u
            LEFT JOIN (
                SELECT url_id, status_code, created_at
                FROM url_checks
                WHERE ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at DESC) = 1
            ) uc ON u.id = uc.url_id
            ORDER BY u.created_at DESC;
        """)
        return [{'id': row[0], 'name': row[1], 'status': row[2], 'check_date': row[3].date() if row[3] else ''} for row in cur.fetchall()]


def get_url_by_id(conn, id):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s;", (id,))
        url_data = cur.fetchone()
        cur.execute("SELECT id, status_code, h1, title, content, created_at FROM url_checks WHERE url_id = %s ORDER BY created_at DESC;", (id,))
        checks = [{'id': row[0], 'status': row[1], 'h1': row[2], 'title': row[3], 'content': row[4], 'date': row[5].date()} for row in cur.fetchall()]
        return {'id': url_data[0], 'name': url_data[1], 'date': url_data[2].date()}, checks


def add_url_check(conn, url_id, status_code, h1, title, content):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO url_checks (url_id, status_code, created_at, h1, title, content)
            VALUES (%s, %s, NOW(), %s, %s, %s);
        """, (url_id, status_code, h1, title, content))
        conn.commit()
