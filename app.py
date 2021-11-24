from flask import Flask, render_template, url_for, request, flash, session, redirect, abort
import datetime

app = Flask(__name__)
menu = [{'name': 'О сайте', 'url': 'about'},
        {'name': 'Увлечения', 'url': 'hobby'},
        {'name': 'Обратная связь', 'url': 'contact'}]
app.config['SECRET_KEY'] = 'qjhi3hq8u883bdi39jhnx0ndbiqo'
app.permanent_session_lifetime = datetime.timedelta(minutes=90)


@app.route('/')
def index():
    session.permanent = True
    if 'visits' in session:
        session['visits'] = session.get('visits') + 1
    else:
        session['visits'] = 1
    return render_template('index.html', menu=menu, visits=session['visits'])


@app.route('/about')
def about():
    return render_template('about.html', title='О сайте', menu=menu)


@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == 'POST':
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправки', category='error')
        print(request.form)
    return render_template('contact.html', title='Связаться с Ксюшей', menu=menu)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'userLogged' in session:
        return redirect(url_for('profile', username=session['userLogged']))
    elif request.method == 'POST' and request.form['username'] == 'Kseniia' and request.form['psw'] == '123':
        session['userLogged'] = request.form['username']
        return redirect(url_for('profile', username=session['userLogged']))

    return render_template('login.html', title='Авторизация', menu=menu)


@app.route('/profile/<username>')
def profile(username):
    if 'userLogged' not in session or session['userLogged'] != username:
        return abort(401)
    return f'Пользователь: {username}'


@app.errorhandler(404)
def pagenotfound(error):
    return render_template('page404.html', title='Страница не найдена', menu=menu), 404


if __name__ == '__main__':
    app.run(debug=True)

with app.test_request_context():  # искуственный контекст запроса без поднятия сервиса, может работать с несколькими приложениями
    print(url_for('about'))
