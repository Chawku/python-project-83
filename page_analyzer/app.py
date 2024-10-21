import os
from flask import Flask, render_template, request, redirect, flash, url_for
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
import requests
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
connection = psycopg2.connect(DATABASE_URL)

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except psycopg2.Error as e:
        flash(f"Database connection error: {e}", 'danger')
        return None

def is_valid_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme in ('http', 'https') and parsed_url.netloc

def normalize_url(url):
    parsed_url = urlparse(url)
    return f'{parsed_url.scheme}://{parsed_url.netloc}'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['GET'])
def list_urls():
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))
    
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
    if not is_valid_url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422

    normalized_url = normalize_url(url)
    
    if len(normalized_url) > 255:
        flash('URL слишком длинный', 'danger')
        return render_template('index.html'), 422

    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
            existing_url = cursor.fetchone()

            if existing_url:
                flash('URL уже существует', 'info')
                url_id = existing_url[0]
            else:
                cursor.execute(
                    "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                    (normalized_url, datetime.now())
                )
                url_id = cursor.fetchone()[0]
                flash('URL успешно добавлен', 'success')

        conn.commit()
    finally:
        conn.close()
    
    return redirect(url_for('show_url', id=url_id))

@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
            url = cursor.fetchone()

            cursor.execute("SELECT id, created_at FROM url_checks WHERE url_id = %s ORDER BY created_at DESC", (id,))
            checks = cursor.fetchall()
    finally:
        conn.close()
    
    return render_template('url.html', url=url, checks=checks)

@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('index'))

    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute('SELECT name FROM urls WHERE id = %s', (id,))
            url_data = cursor.fetchone()

        if url_data is None:
            flash('Сайт не найден', 'danger')
            return redirect(url_for('list_urls'))

        url = url_data['name']
        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            h1 = soup.find('h1').get_text(strip=True) if soup.find('h1') else None
            title = soup.find('title').get_text(strip=True) if soup.find('title') else None
            meta_description = None
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_tag and 'content' in meta_tag.attrs:
                meta_description = meta_tag['content']

            status_code = response.status_code

        except requests.RequestException:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('show_url', id=id))

        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                '''
                INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''',
                (id, status_code, h1, title, meta_description, datetime.now())
            )
            conn.commit()

        flash('Проверка успешно выполнена', 'success')
    finally:
        conn.close()

    return redirect(url_for('show_url', id=id))

if __name__ == '__main__':
    app.run(debug=True)
