from flask import (Flask,
                   render_template,
                   flash,
                   redirect,
                   abort,
                   url_for,
                   request,
                   get_flashed_messages)
from collections import namedtuple
from dotenv import load_dotenv
import os
import requests
from page_analyzer.db_tools import (get_all_urls,
                                    get_url_by_db_field,
                                    post_new_url,
                                    get_checks_by_url_id,
                                    add_url_checks)
from page_analyzer.urls import normalize_url, validate_url, parse_page

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')
app.config['DEBUG'] = os.getenv('DEBUG')


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def get_urls():
    """Shows all added URLs with last check dates and status codes if any"""

    urls: namedtuple = get_all_urls()
    return render_template('urls.html', items=urls)


@app.post('/urls')
def post_url():
    """
    Get new URL, validates the URL.
    Adds the URL to DB if it isn't there and passed validation.
    Redirect to url_info.
    """
    url: str = request.form.get('url')
    errors: list = validate_url(url)
    if errors:
        for error in errors:
            flash(error, 'alert-danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            url=url,
            messages=messages
        ), 422

    url: str = normalize_url(url)
    current_url: namedtuple = get_url_by_db_field(url)
    if current_url:
        flash('Страница уже существует', 'alert-info')
        url_id = current_url.id
    else:
        post_new_url(url)
        current_url = get_url_by_db_field(url)
        url_id = current_url.id
        flash('Страница успешно добавлена', 'alert-success')
    return redirect(url_for('url_info', id=url_id)), 301


@app.get('/urls/<int:id>')
def url_info(id):
    """
    Shows URL information and made checks
    :param id: URL's id
    """

    url: namedtuple = get_url_by_db_field(id)
    if not url:
        abort(404)

    checks: namedtuple = get_checks_by_url_id(id)
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'url_info.html',
        url=url,
        checks=checks,
        messages=messages
    )


@app.post('/url/<int:id>/checks')
def url_checks(id):
    """
    Checks requested URL.
    If no errors, adds got data to DB.
    :param id: URL's id
    :return: redirect to url_info
    """

    url: namedtuple = get_url_by_db_field(id)

    try:
        response = requests.get(url.name)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', 'alert-danger')
        return redirect(url_for('url_info', id=id))

    checks: dict = parse_page(response.text)
    checks['url_id'] = id
    checks['status_code'] = response.status_code

    add_url_checks(checks)

    flash('Страница успешно проверена', 'alert-success')

    return redirect(url_for('url_info', id=id))


if __name__ == '__main__':
    app.run()
