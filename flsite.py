import sqlite3
import os
from flask import Flask, render_template, g, flash, request, abort, session, redirect, url_for, make_response
from FDataBase import FDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from UserLogin import UserLogin
from forms import LoginForm
import requests
from googletrans import Translator

# Конфигурация
DATABASE = '/flsite.db'
DEBUG = True
SECRET_KEY = 'qjhi3hq8u883bdi39jhnx0ndbiqo'
MAX_CONTENT_LENGHT = 1024 * 1024

app = Flask(__name__)
app.config.from_object(__name__)  # загрузка нашей конфигурации
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Авторизуйтесь для доступа к закрытым страницам'
login_manager.login_message_category = 'success'

translator = Translator(service_urls=['translate.googleapis.com'])

@login_manager.user_loader
def load_user(user_id):
    print('Load user')
    return UserLogin().fromDB(user_id, dbase)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row  # строчка, чтобы данные записывались в виде словарей, а не кортежей
    return conn


def create_db():
    # Создаем базу данныех без запуска сервера
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    # Устанавливаем соединение с БД, если оно еще не установлено
    if not hasattr(g, 'link_db'):  # Проверяем, есть ли такое свойство у глобальной переменной контекста запроса
        g.link_db = connect_db()
    return g.link_db


dbase = None


@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@app.route("/")
def index():
    if 'visits' in session:
        session['visits'] = session.get('visits') + 1
    else:
        session['visits'] = 1
    return render_template('index.html', menu=dbase.getMenu(), posts=dbase.getPostsAnonce(), visits=session['visits'])


@app.route("/add_post", methods=["POST", "GET"])
def addPost():
    if request.method == "POST":
        if len(request.form['post_title']) > 4 and len(request.form['post_text']) > 10:
            res = dbase.addPost(request.form['post_title'], request.form['post_text'], request.form['post_url'])
            if not res:
                flash('Ошибка добавления статьи', category='error')
            else:
                flash('Статья добавлена успешно', category='success')
        else:
            flash('Ошибка добавления статьи', category='error')
    return render_template('add_post.html', menu=dbase.getMenu(), title="Добавление статьи")


@app.route("/post/<alias>")
@login_required
def showPost(alias):
    post_title, post_text = dbase.getPost(alias)
    if not post_title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=post_title, post=post_text)


@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html', menu=dbase.getMenu(), title='Профиль')


@app.route("/fun")
@login_required
def fun():
    return render_template('fun.html', menu=dbase.getMenu(), title='Штуковины')


@app.route("/facts")
@login_required
def facts():
    return render_template('facts.html', menu=dbase.getMenu(), title='Забавные факты')


@app.route("/num", methods=["POST", "GET"])
@login_required
def num():
    params = {
        'json': True,
        'default': "Boring number is boring"
    }
    if request.method == "POST":
        if request.form['number']:
            if request.form['numtype'] == "math":
                url = 'http://numbersapi.com/' + request.form['number'] + '/math'
            else:
                url = 'http://numbersapi.com/' + request.form['number']
            res = requests.get(url, params=params)
            if 'Boring number is boring' in res.json()['text']:
                flash(translator.translate(res.json()['text'], dest='ru').text, category='error')
            else:
                flash(translator.translate(res.json()['text'], dest='ru').text, category='success')
    return render_template('num.html', menu=dbase.getMenu(), title='Числа')


@app.route("/userava")
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route("/upload", methods=['POST', 'GET'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash('Ошибка обновления аватара', category='error')
                flash('Аватар обновлен', category='success')
            except FileNotFoundError as e:
                flash('Ошибка чтения файла', category='error')
        else:
            flash('Ошибка обновления аватара', category='error')
    return redirect(url_for('profile'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', category='success')
    return redirect(url_for('login'))


@app.teardown_appcontext
def close_db(error):
    # Закрываем соединение с БД, если оно было установлено
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.getUserByEmail(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)  # авторизуем вот тут!
            return redirect(request.args.get('next') or url_for('profile'))
        flash('Неверный логин/пароль', category='error')
    return render_template('login2.html', title='Авторизация', menu=dbase.getMenu(), form=form)

    #if request.method == 'POST':
    #    user = dbase.getUserByEmail(request.form['email'])
    #    if user and check_password_hash(user['psw'], request.form['psw']):
    #        userlogin = UserLogin().create(user)
    #        rm = True if request.form.get('remainme') else False
    #        login_user(userlogin, remember=rm)  # авторизуем вот тут!
    #        return redirect(request.args.get('next') or url_for('profile'))
    #    flash('Неверный логин/пароль', category='error')
    #return render_template('login2.html', title='Авторизация', menu=dbase.getMenu())


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        if len(request.form['name']) > 4 and len(request.form['email']) > 4 \
                and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2']:
            hash = generate_password_hash(request.form['psw'])
            res = dbase.AddUser(request.form['name'], request.form['email'], hash)
            if res:
                flash('Вы успешно зарегистрированы', category='success')
                return redirect(url_for('login'))
            else:
                flash('Ошибка при добавлении в БД', category='error')
        else:
            flash('Ошибка при заполнении полей', category='error')
    return render_template('register.html', title='Регистрация', menu=dbase.getMenu())


@app.errorhandler(404)
def pagenotfound(error):
    db = get_db()
    dbase = FDataBase(db)
    return render_template('page404.html', title='Страница не найдена', menu=dbase.getMenu()), 404


if __name__ == '__main__':
    app.run(debug=True)
