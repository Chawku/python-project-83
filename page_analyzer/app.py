from flask import Flask, render_template, request, flash, redirect, get_flashed_messages, url_for
import os
from dotenv import load_dotenv
from .database import (
    get_url_by_name, add_url, get_all_urls, get_url_details, add_url_check
)
from .validation import validate_url
from .web import fetch_page_data

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

    url_id = get_url_by_name(DATABASE_URL, url_string)
    if url_id:
        flash("Страница уже существует", "alert alert-danger")
    else:
        url_id = add_url(DATABASE_URL, url_string)
        flash("Страница успешно добавлена", "alert alert-success")
    return redirect(url_for('get_url', id=url_id)), 301


@app.get('/urls')
def get_urls():
    messages = get_flashed_messages(with_categories=True)
    urls_list = get_all_urls(DATABASE_URL)
    return render_template("urls.html", urls=urls_list, messages=messages)


@app.get('/urls/<id>')
def get_url(id):
    messages = get_flashed_messages(with_categories=True)
    urls_data, url_checks_list = get_url_details(DATABASE_URL, id)
    return render_template("url.html", url=urls_data,
                           url_checks=url_checks_list, messages=messages)


@app.post('/urls/<id>/checks')
def check_url(id):
    url_data = get_url_by_name(DATABASE_URL, id)
    if not url_data:
        flash("URL не найден", "alert alert-danger")
        return redirect(url_for('index'))

    try:
        page_data = fetch_page_data(url_data['name'])
        add_url_check(DATABASE_URL, id, page_data)
        flash("Страница успешно проверена", "alert alert-success")
    except Exception:
        flash("Произошла ошибка при проверке", "alert alert-danger")
    return redirect(url_for('get_url', id=id))


if __name__ == "__main__":
    app.run(debug=True)
