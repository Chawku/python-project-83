import psycopg2
import os
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def get_url_id(name):
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT id FROM urls WHERE name = %s;", (name,))
            url = curs.fetchone()
            return url['id'] if url else None


def insert_url(name):
    with get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id;",
                (name,)
            )
            return curs.fetchone()['id']


def fetch_urls():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id AS url_id, u.name AS url_name, 
                       COALESCE(uc.status_code, '') AS status_code,
                       uc.created_at AS max_created_at
                FROM urls u
                LEFT JOIN (
                    SELECT url_id, status_code, created_at,
                           ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at DESC) AS row_num
                    FROM url_checks
                ) uc ON u.id = uc.url_id AND uc.row_num = 1
                ORDER BY u.created_at DESC;
            """)
            return cur.fetchall()


def fetch_url_by_id(id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s;", (id,))
            url = cur.fetchone()
            url['created_at'] = url['created_at'].date()
            return url


def get_last_check(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, status_code, h1, title, content, created_at 
                FROM url_checks WHERE url_id = %s ORDER BY created_at DESC;
            """, (url_id,))
            return cur.fetchall()


def insert_url_check(url_id, status_code, h1, title, content):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO url_checks (url_id, status_code, created_at, h1, title, content)
                VALUES (%s, %s, NOW(), %s, %s, %s);
                """,
                (url_id, status_code, h1, title, content)
            )
            conn.commit()
