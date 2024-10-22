import os
from flask import Flask, render_template, request, flash, redirect, url_for, get_flashed_messages
import validators
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse
import psycopg2
from bs4 import BeautifulSoup
from psycopg2.extras import DictCursor

load_dotenv()

app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')


def get_db_connection():
    return psycopg2.connect(app.config['DATABASE_URL'], cursor_factory=DictCursor)


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)

@app.post('/urls')
def add_url():
    url_string = request.form.get('url', '').strip()
    if not validators.url(url_string):
        flash("Некорректный URL", "alert alert-danger")
        return redirect(url_for('index')), 422

    parsed_url = urlparse(url_string)
    normalized_url = f'{parsed_url.scheme}://{parsed_url.netloc}'

    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
                existing_url = curs.fetchone()

                if existing_url:
                    flash("Страница уже существует", "alert alert-danger")
                    url_id = existing_url['id']
                else:
                    curs.execute(
                        "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id",
                        (normalized_url,)
                    )
                    url_id = curs.fetchone()['id']
                    flash("Страница успешно добавлена", "alert alert-success")

        return redirect(url_for('get_url', id=url_id)), 302

    except Exception as e:
        flash(f"Ошибка при добавлении URL: {e}", "alert alert-danger")
        return redirect(url_for('index')), 500

@app.get('/urls')
def list_urls():
    messages = get_flashed_messages(with_categories=True)
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute("""
                    SELECT u.id, u.name, COALESCE(uc.status_code, '') AS status_code, uc.created_at
                    FROM urls u
                    LEFT JOIN (
                        SELECT url_id, status_code, created_at
                        FROM url_checks
                        WHERE (url_id, created_at) IN (
                            SELECT url_id, MAX(created_at)
                            FROM url_checks
                            GROUP BY url_id
                        )
                    ) uc ON u.id = uc.url_id
                    ORDER BY u.created_at DESC
                """)
                urls = curs.fetchall()

        return render_template("urls.html", urls=urls, messages=messages)

    except Exception as e:
        flash(f"Ошибка при получении списка URL: {e}", "alert alert-danger")
        return redirect(url_for('index')), 500

@app.get('/urls/<int:id>')
def get_url(id):
    messages = get_flashed_messages(with_categories=True)
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM urls WHERE id = %s", (id,))
                url_data = curs.fetchone()
                
                if not url_data:
                    flash("URL не найден", "alert alert-danger")
                    return redirect(url_for('list_urls'))

                curs.execute("""
                    SELECT id, status_code, h1, title, content, created_at
                    FROM url_checks
                    WHERE url_id = %s
                    ORDER BY created_at DESC
                """, (id,))
                url_checks = curs.fetchall()

        return render_template("url.html", url=url_data, url_checks=url_checks, messages=messages)

    except Exception as e:
        flash(f"Ошибка при получении данных URL: {e}", "alert alert-danger")
        return redirect(url_for('list_urls')), 500

@app.post('/urls/<int:id>/checks')
def check_url(id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT name FROM urls WHERE id = %s", (id,))
                url_data = curs.fetchone()

                if not url_data:
                    flash("URL не найден", "alert alert-danger")
                    return redirect(url_for('list_urls'))

                url_name = url_data['name']
                response = requests.get(url_name)

                if response.status_code != 200:
                    flash("Произошла ошибка при проверке", "alert alert-danger")
                    return redirect(url_for('get_url', id=id))

                soup = BeautifulSoup(response.text, 'html.parser')
                h1 = (soup.find('h1').text if soup.find('h1') else '').strip()
                title = (soup.find('title').text if soup.find('title') else '').strip()
                description = (soup.find('meta', attrs={'name': 'description'}) or {}).get('content', '').strip()

                curs.execute("""
                    INSERT INTO url_checks (url_id, status_code, created_at, h1, title, content)
                    VALUES (%s, %s, NOW(), %s, %s, %s)
                """, (id, response.status_code, h1, title, description))

                flash("Страница успешно проверена", "alert alert-success")

        return redirect(url_for('get_url', id=id))

    except Exception as e:
        flash(f"Ошибка при проверке URL: {e}", "alert alert-danger")
        return redirect(url_for('get_url', id=id)), 500


if __name__ == "__main__":
    app.run(debug=True)
