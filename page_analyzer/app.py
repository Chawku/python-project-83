import os
from flask import Flask, render_template, request, redirect, flash, url_for
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['GET'])
def list_urls():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT urls.id, urls.name, MAX(url_checks.created_at) AS last_check
            FROM urls
            LEFT JOIN url_checks ON urls.id = url_checks.url_id
            GROUP BY urls.id
            ORDER BY urls.id DESC;
        """)
        urls = cursor.fetchall()
    conn.close()
    return render_template('urls.html', urls=urls)

@app.route('/urls', methods=['POST'])
def create_url():
    url = request.form.get('url')
    parsed_url = urlparse(url)
    normalized_url = f'{parsed_url.scheme}://{parsed_url.netloc}'

    if not url or len(normalized_url) > 255:
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422

    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Проверка, существует ли уже такой URL
        cursor.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = cursor.fetchone()

        if existing_url:
            flash('URL уже существует', 'info')
            url_id = existing_url[0]
        else:
            # Добавление нового URL
            cursor.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (normalized_url, datetime.now())
            )
            url_id = cursor.fetchone()[0]
            flash('URL успешно добавлен', 'success')

    conn.commit()
    conn.close()
    return redirect(url_for('show_url', id=url_id))

@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Получение информации о сайте
        cursor.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
        url = cursor.fetchone()

        # Получение проверок для данного сайта
        cursor.execute("SELECT id, created_at FROM url_checks WHERE url_id = %s ORDER BY created_at DESC", (id,))
        checks = cursor.fetchall()
    conn.close()
    return render_template('url.html', url=url, checks=checks)

@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Вставка новой проверки в таблицу url_checks
            cursor.execute(
                "INSERT INTO url_checks (url_id, created_at) VALUES (%s, %s)",
                (id, datetime.now())
            )
        conn.commit()
        flash('Проверка была успешно добавлена', 'success')
    except Exception as e:
        flash(f'Ошибка при создании проверки: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('show_url', id=id))

if __name__ == '__main__':
    app.run(debug=True)
