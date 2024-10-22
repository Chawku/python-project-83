from flask import Flask, render_template, request, flash, redirect, get_flashed_messages, url_for
import psycopg2
import os
import validators
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__)
app.secret_key = 'secret key'

DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def fetch_one(query, params=()):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetch_all(query, params=()):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def execute_query(query, params=()):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)

@app.post('/urls')
def urls_page():
    url_string = request.form.get('url', '')
    if not validators.url(url_string):
        return render_template("index.html", messages=[("alert alert-danger", "Некорректный URL")]), 422

    url_string = f'{urlparse(url_string).scheme}://{urlparse(url_string).netloc}'
    existing_url = fetch_one("SELECT id FROM urls WHERE name=%s;", (url_string,))

    if existing_url:
        flash("Страница уже существует", "alert alert-danger")
        return redirect(url_for('get_url', id=existing_url[0])), 301

    url_id = fetch_one(
        "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id;",
        (url_string,)
    )[0]
    flash("Страница успешно добавлена", "alert alert-success")
    return redirect(url_for('get_url', id=url_id)), 301

@app.get('/urls')
def get_urls():
    urls_tuples = fetch_all("""
        SELECT u.id, u.name, COALESCE(uc.status_code, '') AS status_code, uc.created_at
        FROM urls u
        LEFT JOIN (
            SELECT url_id, status_code, created_at, 
                   ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at DESC) AS row_num
            FROM url_checks
        ) uc ON u.id = uc.url_id AND uc.row_num = 1
        ORDER BY u.created_at DESC;
    """)
    urls_list = [{'id': id, 'name': name, 'check_date': (date.date() if date else ''), 'status': status}
                 for id, name, status, date in urls_tuples]
    return render_template("urls.html", urls=urls_list, messages=get_flashed_messages(with_categories=True))

@app.get('/urls/<id>')
def get_url(id):
    url_data = fetch_one("SELECT id, name, created_at FROM urls WHERE id=%s;", (id,))
    url_checks = fetch_all("""
        SELECT id, status_code, h1, title, content, created_at
        FROM url_checks WHERE url_id=%s ORDER BY created_at DESC;
    """, (id,))
    url_checks_list = [{'id': id, 'status': status, 'h1': h1, 'title': title, 'content': content, 'date': date.date()}
                       for id, status, h1, title, content, date in url_checks]
    return render_template("url.html", url={'id': url_data[0], 'name': url_data[1], 'date': url_data[2].date()},
                           url_checks=url_checks_list, messages=get_flashed_messages(with_categories=True))

@app.post('/urls/<id>/checks')
def check_url(id):
    url = fetch_one("SELECT name FROM urls WHERE id=%s;", (id,))
    if not url:
        flash("URL не найден", "alert alert-danger")
        return redirect(url_for('index'))

    try:
        response = requests.get(url[0])
        response.raise_for_status()
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "alert alert-danger")
        return redirect(url_for('get_url', id=id))

    soup = BeautifulSoup(response.text, 'html.parser')
    h1 = soup.h1.text if soup.h1 else ''
    title = soup.title.text if soup.title else ''
    description = soup.find('meta', {'name': 'description'})
    content = description.get('content', '') if description else ''

    execute_query(
        "INSERT INTO url_checks (url_id, status_code, created_at, h1, title, content) VALUES (%s, %s, NOW(), %s, %s, %s);",
        (id, response.status_code, h1, title, content)
    )
    flash("Страница успешно проверена", "alert alert-success")
    return redirect(url_for('get_url', id=id))


if __name__ == "__main__":
    app.run(debug=True)
