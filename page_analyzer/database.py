import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_url_id(url_string):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as curs:
            get_ids_of_url_query = "SELECT id from urls WHERE name= %s;"
            curs.execute(get_ids_of_url_query, (url_string,))
            urls_dicts = curs.fetchall()
            if urls_dicts:
                return urls_dicts[0]['id']
            else:
                return None


def add_url(url_string):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as curs:
            add_url_query = (
                "INSERT INTO urls (name, created_at) "
                "VALUES (%s, NOW()) "
                "RETURNING id;"
            )
            curs.execute(add_url_query, (url_string,))
            url_id = curs.fetchone()['id']
            conn.commit()
            return url_id


def get_all_urls():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            sql_query = """
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
                    ROW_NUMBER() OVER (PARTITION BY
                    url_id ORDER BY created_at DESC) AS row_num
                FROM
                    url_checks
            ) uc ON u.id = uc.url_id AND uc.row_num = 1
            ORDER BY u.created_at DESC;
            """
            cur.execute(sql_query)
            urls_dicts = cur.fetchall()
            return urls_dicts


def get_url_data(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            get_url_data_query = "SELECT * FROM urls where id=%s ;"
            cur.execute(get_url_data_query, (id,))
            urls_dicts = cur.fetchall()
            return urls_dicts


def get_url_checks_data(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            get_url_checks_data = (
                "SELECT id, status_code, h1, title, content, created_at "
                "FROM url_checks "
                "WHERE url_id=%s "
                "ORDER BY created_at DESC;"
            )
            cur.execute(get_url_checks_data, (id,))
            url_checks_dicts = cur.fetchall()
            return url_checks_dicts


def add_url_check(params):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            request_string = (
                "INSERT INTO url_checks ("
                "url_id, status_code, created_at, h1, title, content"
                ") VALUES ("
                "%s, %s, NOW(), %s, %s, %s"
                ");"
            )
            cur.execute(request_string, (params['check_id'],
                                         params['status_code'], params['h1'],
                                         params['title'], params['content']))
            conn.commit()
