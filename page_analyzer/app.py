from flask import Flask, render_template, request, flash, redirect, get_flashed_messages, url_for
from dotenv import load_dotenv
import os
from .url import add_url, get_all_urls, get_single_url, check_url

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
    url_string = request.form.get('url', '')
    return add_url(url_string)


@app.get('/urls')
def get_urls():
    return get_all_urls()


@app.get('/urls/<id>')
def get_url(id):
    return get_single_url(id)


@app.post('/urls/<id>/checks')
def url_check(id):
    return check_url(id)


if __name__ == "__main__":
    app.run(debug=True)
