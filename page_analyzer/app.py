from urllib.parse import urlparse

from flask import Flask, redirect, render_template, request, url_for

from .database import (
    add_url,
    add_url_check,
    get_all_urls,
    get_url_checks_data,
    get_url_data,
    get_url_id,
)

from .utils import make_request, parse_html, get_messages, flash_message, is_valid_url, normalize_url

app = Flask(__name__)
app.secret_key = 'secret key'

@app.route('/')
def index():
    messages = get_messages()
    return render_template("index.html", messages=messages)

@app.post('/urls')
def urls_page():
    url_string = request.form.to_dict().get('url', '')
    if not is_valid_url(url_string):
        messages = [("alert alert-danger", "Некорректный URL")]
        return render_template("index.html", messages=messages), 422
    url_string = normalize_url(url_string)
    if url_string:
        url_id = get_url_id(url_string)
        if url_id:
            flash_message("Страница уже существует", "alert alert-danger")
        else:
            url_id = add_url(url_string)
            flash_message("Страница успешно добавлена", "alert alert-success")
        return redirect(url_for('get_url', id=url_id)), 301

@app.get('/urls')
def get_urls():
    messages = get_messages()
    urls_tuples = get_all_urls()
    urls_list = []
    for url_tuple in urls_tuples:
        id, name, status, date = url_tuple
        date = (date.date() if date else '')
        urls_list.append({'id': id, 'name': name, 'check_date': date, 'status': status})
    return render_template("urls.html", urls=urls_list, messages=messages)

@app.get('/urls/<id>')
def get_url(id):
    messages = get_messages()
    urls_tuples = get_url_data(id)
    id, name, date = urls_tuples[0]
    urls_data = {"id": id, "name": name, "date": date.date()}
    url_checks_tuples = get_url_checks_data(id)
    url_checks_list = []
    if url_checks_tuples:
        for url_check_tuple in url_checks_tuples:
            id, status, h1, title, content, date = url_check_tuple
            url_checks_list.append({'id': id, 'status': status, 'h1': h1, 'title': title, 'content': content, 'date': date.date()})
    return render_template("url.html", url=urls_data, url_checks=url_checks_list, messages=messages)

@app.post('/urls/<id>/checks')
def check_url(id):
    urls_tuples = get_url_data(id)
    if urls_tuples:
        name = urls_tuples[0][1]
    req = make_request(name)
    if not req:
        flash_message("Произошла ошибка при проверке", "alert alert-danger")
        return redirect(url_for('get_url', id=id))
    html_content = req.text
    parsed_data = parse_html(html_content)
    params = {'check_id': id, 'status_code': req.status_code, 'title': parsed_data['title'], 'h1': parsed_data['h1'], 'content': parsed_data['content']}
    add_url_check(params)
    flash_message("Страница успешно проверена", "alert alert-success")
    return get_url(id)

if __name__ == "__main__":
    app.run(debug=True)
