from flask import Flask, render_template, request, flash, redirect, url_for, get_flashed_messages
import psycopg2
import os
import validators
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'secret key')
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def fetch_one(query, params=()):
    with get_db_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(query, params)
            return curs.fetchone()


def fetch_all(query, params=()):
    with get_db_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(query, params)
            return curs.fetchall()


def insert_and_return_id(query, params=()):
    with get_db_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(query, params)
            conn.commit()
            return curs.fetchone()[0]


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.post('/urls')
def add_url():
    url_string = request.form.get('url', '').strip()
    if not validators.url(url_string):
        flash("Некорректный URL", "alert alert-danger")
        return render_template("index.html", messages=get_flashed_messages(with_categories=True)), 422

    parsed_url = urlparse(url_string)
    normalized_url = f'{parsed_url.scheme}://{parsed_url.netloc}'

    existing_url = fetch_one("SELECT id FROM urls WHERE name = %s", (normalized_url,))
    if existing_url:
        url_id = existing_url[0]
        flash("Страница уже существует", "alert alert-danger")
    else:
        url_id = insert_and_return_id(
            "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id;",
            (normalized_url,)
        )
        flash("Страница успешно добавлена", "alert alert-success")

    return redirect(url_for('get_url', id=url_id)), 302


@app.get('/urls')
def list_urls():
    messages = get_flashed_messages(with_categories=True)
    urls = fetch_all("""
        SELECT u.id, u.name, COALESCE(uc.status_code, '') AS status_code, uc.created_at
        FROM urls u
        LEFT JOIN (
            SELECT url_id, status_code, created_at,
            ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at DESC) AS row_num
            FROM url_checks
        ) uc ON u.id = uc.url_id AND uc.row_num = 1
        ORDER BY u.created_at DESC;
    """)
    return render_template("urls.html", urls=[
        {
            'id': url[0],
            'name': url[1],
            'status': url[2],
            'check_date': url[3].date() if url[3] else ''
        } for url in urls
    ], messages=messages)


@app.get('/urls/<int:id>')
def get_url(id):
    messages = get_flashed_messages(with_categories=True)
    url_data = fetch_one("SELECT * FROM urls WHERE id = %s", (id,))
    if not url_data:
        flash("URL не найден", "alert alert-danger")
        return redirect(url_for('list_urls'))

    url_checks = fetch_all("""
        SELECT id, status_code, h1, title, content, created_at
        FROM url_checks WHERE url_id = %s ORDER BY created_at DESC;
    """, (id,))
    return render_template("url.html", url={
        'id': url_data[0],
        'name': url_data[1],
        'date': url_data[2].date()
    }, url_checks=[{
        'id': check[0],
        'status': check[1],
        'h1': check[2],
        'title': check[3],
        'content': check[4],
        'date': check[5].date()
    } for check in url_checks], messages=messages)


def parse_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    h1 = soup.find('h1').text if soup.find('h1') else ''
    title = soup.find('title').text if soup.find('title') else ''
    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag.get("content") if description_tag else ''
    return h1, title, description


@app.post('/urls/<int:id>/checks')
def check_url(id):
    url_data = fetch_one("SELECT name FROM urls WHERE id = %s", (id,))
    if not url_data:
        flash("URL не найден", "alert alert-danger")
        return redirect(url_for('list_urls'))

    url_name = url_data[0]
    try:
        response = requests.get(url_name)
        response.raise_for_status()
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "alert alert-danger")
        return redirect(url_for('get_url', id=id))

    h1, title, description = parse_html(response.text)
    insert_and_return_id(
        "INSERT INTO url_checks (url_id, status_code, created_at, h1, title, content) "
        "VALUES (%s, %s, NOW(), %s, %s, %s);",
        (id, response.status_code, h1, title, description)
    )
    flash("Страница успешно проверена", "alert alert-success")
    return redirect(url_for('get_url', id=id)), 302


if __name__ == "__main__":
    app.run(debug=True)
