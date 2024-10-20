import os
import psycopg2
from flask import Flask, render_template, request, redirect, flash, url_for
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
connection = psycopg2.connect(DATABASE_URL)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO urls (name, created_at) VALUES (%s, NOW())", (url,))
            conn.commit()
        except Exception as e:
            flash(f'Ошибка при добавлении URL: {str(e)}', 'danger')
            return render_template('index.html')
        finally:
            conn.close()
        
        flash('URL успешно добавлен', 'success')
        return redirect(url_for('index'))

    return render_template('index.html')

