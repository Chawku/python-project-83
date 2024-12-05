import psycopg2
from psycopg2.extras import DictCursor
import os


DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)


def get_url_by_name(name):
    query = "SELECT id FROM urls WHERE name = %s;"
    with get_db_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(query, (name,))
            return curs.fetchone()


def add_url(name):
    query = "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id;"
    with get_db_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(query, (name,))
            conn.commit()
            return curs.fetchone()[0]


def get_all_urls():
    query = """
    SELECT
        u.id AS url_id,
        u.name AS url_name,
        COALESCE(uc.status_code, '') AS status_code,
        uc.created_at AS max_created_at
    FROM
        urls u
    LEFT JOIN (
        SELECT
            url_id,
            status_code,
            created_at,
            ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at DESC) AS row_num
        FROM
            url_checks
    ) uc ON u.id = uc.url_id AND uc.row_num = 1
    ORDER BY u.created_at DESC;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def get_url_by_id(url_id):
    query = "SELECT * FROM urls WHERE id = %s;"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (url_id,))
            return cur.fetchone()


def get_url_checks(url_id):
    query = """
    SELECT id, status_code, h1, title, content, created_at
    FROM url_checks
    WHERE url_id = %s
    ORDER BY created_at DESC;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (url_id,))
            return cur.fetchall()


def add_url_check(url_id, status_code, h1, title, content):
    query = """
    INSERT INTO url_checks (url_id, status_code, created_at, h1, title, content)
    VALUES (%s, %s, NOW(), %s, %s, %s);
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (url_id, status_code, h1, title, content))
            conn.commit()
