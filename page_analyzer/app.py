from urllib.parse import urlparse

import requests
import validators
from bs4 import BeautifulSoup
from flask import (Flask, flash, get_flashed_messages, redirect,
                   render_template, request, url_for)

from .database import (add_url, add_url_check, get_all_urls,
                       get_url_checks_data, get_url_data, get_url_id)


app = Flask(__name__)
app.secret_key = 'secret key'


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.post('/urls')
def urls_page():
    url_string = request.form.to_dict().get('url', '')
    if not validators.url(url_string):
        messages = [("alert alert-danger", "Некорректный URL")]
        return render_template("index.html", messages=messages), 422
    url_string = urlparse(url_string)
    url_string = f'{url_string.scheme}://{url_string.netloc}'
    if url_string:
        url_id = get_url_id(url_string)
        if url_id:
            flash("Страница уже существует", "alert alert-danger")
        else:
            url_id = add_url(url_string)
            flash("Страница успешно добавлена", "alert alert-success")
        return redirect(url_for('get_url', id=url_id)), 301


@app.get('/urls')
def get_urls():
    messages = get_flashed_messages(with_categories=True)
    urls_tuples = get_all_urls()
    urls_list = []
    for url_tuple in urls_tuples:
        id, name, status, date = url_tuple
        date = (date.date() if date else '')
        urls_list.append({'id': id, 'name': name,
                          'check_date': date, 'status': status})
    return render_template("urls.html", urls=urls_list, messages=messages)


@app.get('/urls/<id>')
def get_url(id):
    messages = get_flashed_messages(with_categories=True)
    urls_tuples = get_url_data(id)
    id, name, date = urls_tuples[0]
    urls_data = {"id": id, "name": name, "date": date.date()}
    url_checks_tuples = get_url_checks_data(id)
    url_checks_list = []
    if url_checks_tuples:
        for url_check_tuple in url_checks_tuples:
            id, status, h1, title, content, date = url_check_tuple
            url_checks_list.append({'id': id, 'status': status, 'h1': h1,
                                    'title': title, 'content': content,
                                    'date': date.date()})
    return render_template("url.html", url=urls_data,
                           url_checks=url_checks_list, messages=messages)


@app.post('/urls/<id>/checks')
def check_url(id):
    urls_tuples = get_url_data(id)
    if urls_tuples:
        name = urls_tuples[0][1]
    try:
        req = requests.request("GET", name)
        status_code = req.status_code
        if status_code != 200:
            raise requests.RequestException
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "alert alert-danger")
        return redirect(url_for('get_url', id=id))
    html_content = req.text

    soup = BeautifulSoup(html_content, 'html.parser')
    h1 = soup.find('h1')
    h1 = h1.text if h1 else ''
    title = soup.find('title')
    title = title.text if title else ''
    attrs = {'name': 'description'}
    meta_description_tag = soup.find('meta', attrs=attrs)
    content = ''
    if meta_description_tag:
        content = meta_description_tag.get("content")
        content = content if content else ''

    params = {'check_id': id, 'status_code': req.status_code,
              'title': title, 'h1': h1, 'content': content}
    add_url_check(params)
    flash("Страница успешно проверена", "alert alert-success")
    return get_url(id)


if __name__ == "__main__":
    app.run(debug=True)
