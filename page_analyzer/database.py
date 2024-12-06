import psycopg2


def get_url_by_name(db_url, url_name):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as curs:
            query = "SELECT id FROM urls WHERE name = %s;"
            curs.execute(query, (url_name,))
            result = curs.fetchone()
            return result[0] if result else None


def add_url(db_url, url_name):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as curs:
            query = "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id;"
            curs.execute(query, (url_name,))
            conn.commit()
            return curs.fetchone()[0]


def get_all_urls(db_url):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as curs:
            query = """
            SELECT u.id, u.name, COALESCE(uc.status_code, ''), uc.created_at
            FROM urls u
            LEFT JOIN (
                SELECT url_id, status_code, created_at,
                       ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at DESC) AS row_num
                FROM url_checks
            ) uc ON u.id = uc.url_id AND uc.row_num = 1
            ORDER BY u.created_at DESC;
            """
            curs.execute(query)
            return [
                {'id': row[0], 'name': row[1], 'status': row[2], 'check_date': row[3].date() if row[3] else ''}
                for row in curs.fetchall()
            ]


def get_url_details(db_url, url_id):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as curs:
            query = "SELECT id, name, created_at FROM urls WHERE id = %s;"
            curs.execute(query, (url_id,))
            url_data = curs.fetchone()

            query = """
            SELECT id, status_code, h1, title, content, created_at
            FROM url_checks WHERE url_id = %s ORDER BY created_at DESC;
            """
            curs.execute(query, (url_id,))
            url_checks = [
                {'id': row[0], 'status': row[1], 'h1': row[2], 'title': row[3],
                 'content': row[4], 'date': row[5].date()}
                for row in curs.fetchall()
            ]

            return {'id': url_data[0], 'name': url_data[1], 'date': url_data[2].date()}, url_checks


def add_url_check(db_url, url_id, page_data):
    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as curs:
            query = """
            INSERT INTO url_checks (url_id, status_code, created_at, h1, title, content)
            VALUES (%s, %s, NOW(), %s, %s, %s);
            """
            curs.execute(query, (url_id, page_data['status_code'], page_data['h1'],
                                 page_data['title'], page_data['content']))
            conn.commit()
