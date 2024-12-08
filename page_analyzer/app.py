import os

import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    url_for,
)

from .database import (
    add_url,
    add_url_check,
    find_by_url,
    find_url_by_id,
    get_all_urls,
    get_url_checks_data,
)
from .html_parser import extract_page_data
from .urls import normalize_url, validate_url

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.post('/urls')
def urls_page():
    url_string = request.form.to_dict().get('url', '')
    is_valid, error_message = validate_url(url_string)
    if not is_valid:
        messages = [("alert alert-danger", error_message)]
        return render_template("index.html", messages=messages), 422

    normalized_url = normalize_url(url_string)
    url_id = find_by_url(normalized_url)

    if url_id:
        flash("Страница уже существует", "alert alert-danger")
    else:
        url_id = add_url(normalized_url)
        flash("Страница успешно добавлена", "alert alert-success")

    return redirect(url_for('get_url', id=url_id)), 301


@app.get('/urls')
def get_urls():
    messages = get_flashed_messages(with_categories=True)
    urls_tuples = get_all_urls()
    urls_list = []
    for url_tuple in urls_tuples:
        id, name, status, date = url_tuple
        urls_list.append({
            'id': id,
            'name': name,
            'check_date': date,
            'status': status
        })
    return render_template("urls.html", urls=urls_list, messages=messages)


@app.get('/urls/<id>')
def get_url(id):
    messages = get_flashed_messages(with_categories=True)
    url_dict = find_url_by_id(id)
    if not url_dict:
        flash("URL не найден", "alert alert-danger")
        return redirect(url_for('get_urls'))

    urls_data = {"id": url_dict['id'], "name": url_dict['name'], "date": url_dict['created_at']}
    url_checks_tuples = get_url_checks_data(id)
    url_checks_list = []
    if url_checks_tuples:
        for url_check_tuple in url_checks_tuples:
            id, status, h1, title, content, date = url_check_tuple
            url_checks_list.append({
                'id': id,
                'status': status,
                'h1': h1,
                'title': title,
                'content': content,
                'date': date
            })
    return render_template("url.html", url=urls_data,
                           url_checks=url_checks_list, messages=messages)


@app.post('/urls/<id>/checks')
def check_url(id):
    url_dict = find_url_by_id(id)
    if not url_dict:
        flash("URL не найден", "alert alert-danger")
        return redirect(url_for('get_urls'))

    name = url_dict['name']
    try:
        req = requests.get(name)
        req.raise_for_status()
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "alert alert-danger")
        return redirect(url_for('get_url', id=id))

    html_content = req.text
    page_data = extract_page_data(html_content)

    params = {
        'check_id': id,
        'status_code': req.status_code,
        **page_data
    }
    add_url_check(params)
    flash("Страница успешно проверена", "alert alert-success")
    return redirect(url_for('get_url', id=id))


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
