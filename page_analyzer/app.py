import os
import psycopg2
from flask import Flask, render_template, request, redirect, flash, url_for
from urllib.parse import urlparse
from validators import url as validate_url
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        parsed_url = urlparse(url)
        normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if not validate_url(normalized_url) or len(normalized_url) > 255:
            flash('Некорректный URL. Пожалуйста, введите валидный адрес.', 'danger')
            return render_template('index.html')
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO urls (name, created_at) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
                    (normalized_url, datetime.now())
                )
            conn.commit()
        except Exception as e:
            flash(f'Ошибка при добавлении URL: {str(e)}', 'danger')
            return render_template('index.html')
        finally:
            conn.close()
        
        flash('URL успешно добавлен', 'success')
        return redirect(url_for('urls'))

    return render_template('index.html')

@app.route('/urls')
def urls():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, created_at FROM urls ORDER BY created_at DESC")
        urls_list = cursor.fetchall()
    conn.close()
    return render_template('urls.html', urls=urls_list)

@app.route('/urls/<int:url_id>')
def show_url(url_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
        url_info = cursor.fetchone()
    conn.close()
    return render_template('url.html', url=url_info)
