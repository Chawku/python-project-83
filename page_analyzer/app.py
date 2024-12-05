from flask import Flask, render_template, request, flash, redirect, get_flashed_messages, url_for
from .database import add_url, get_url_by_id, get_urls_list, add_url_check
from .utils import validate_url, extract_url_data, fetch_url_content
from psycopg2 import connect
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = 'secret key'
DATABASE_URL = os.getenv('DATABASE_URL')


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.post('/urls')
def urls_page():
    url_string = request.form.to_dict().get('url', '')
    if not validate_url(url_string):
        messages = [("alert alert-danger", "Некорректный URL")]
        return render_template("index.html", messages=messages), 422
    url_string = extract_url_data(url_string)
    with connect(DATABASE_URL) as conn:
        url_id, message, category = add_url(conn, url_string)
        flash(message, category)
    return redirect(url_for('get_url', id=url_id)), 301


@app.get('/urls')
def get_urls():
    messages = get_flashed_messages(with_categories=True)
    with connect(DATABASE_URL) as conn:
        urls_list = get_urls_list(conn)
    return render_template("urls.html", urls=urls_list, messages=messages)


@app.get('/urls/<id>')
def get_url(id):
    messages = get_flashed_messages(with_categories=True)
    with connect(DATABASE_URL) as conn:
        url_data, url_checks = get_url_by_id(conn, id)
    return render_template("url.html", url=url_data, url_checks=url_checks, messages=messages)


@app.post('/urls/<id>/checks')
def check_url(id):
    with connect(DATABASE_URL) as conn:
        url_data = get_url_by_id(conn, id)[0]
        try:
            status_code, h1, title, content = fetch_url_content(url_data['name'])
            add_url_check(conn, id, status_code, h1, title, content)
            flash("Страница успешно проверена", "alert alert-success")
        except Exception:
            flash("Произошла ошибка при проверке", "alert alert-danger")
    return redirect(url_for('get_url', id=id))


if __name__ == "__main__":
    app.run(debug=True)
