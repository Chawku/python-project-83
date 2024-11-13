from flask import render_template, flash, redirect, url_for, get_flashed_messages
from urllib.parse import urlparse
import validators
from .database import insert_url, get_url_id, fetch_urls, fetch_url_by_id, insert_url_check, get_last_check
import requests
from bs4 import BeautifulSoup


def add_url(url_string):
    if not validators.url(url_string):
        messages = [("alert alert-danger", "Некорректный URL")]
        return render_template("index.html", messages=messages), 422
    
    parsed_url = urlparse(url_string)
    url_string = f'{parsed_url.scheme}://{parsed_url.netloc}'
    
    url_id = get_url_id(url_string)
    if url_id:
        flash("Страница уже существует", "alert alert-danger")
    else:
        url_id = insert_url(url_string)
        flash("Страница успешно добавлена", "alert alert-success")
    
    return redirect(url_for('get_url', id=url_id)), 301


def get_all_urls():
    messages = get_flashed_messages(with_categories=True)
    urls = fetch_urls()
    return render_template("urls.html", urls=urls, messages=messages)


def get_single_url(id):
    messages = get_flashed_messages(with_categories=True)
    url_data = fetch_url_by_id(id)
    url_checks = get_last_check(id)
    return render_template("url.html", url=url_data, url_checks=url_checks, messages=messages)


def check_url(id):
    url_data = fetch_url_by_id(id)
    name = url_data['name']
    try:
        req = requests.get(name)
        req.raise_for_status()
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "alert alert-danger")
        return redirect(url_for('get_url', id=id))
    
    html_content = req.text
    soup = BeautifulSoup(html_content, 'html.parser')
    h1 = soup.find('h1').text if soup.find('h1') else ''
    title = soup.find('title').text if soup.find('title') else ''
    description = soup.find('meta', {'name': 'description'})
    content = description.get("content") if description else ''
    
    insert_url_check(id, req.status_code, h1, title, content)
    flash("Страница успешно проверена", "alert alert-success")
    return redirect(url_for('get_url', id=id))
