from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    email = StringField('Email: ', validators=[Email('Некорректный email')])
    psw = PasswordField('Пароль: ', validators=[Length(min=3, max=100, message='Пароль должен быть от 4 до 100 символов'), DataRequired()])
    remember = BooleanField('Запомнить: ', default=False)
    submit = SubmitField('Войти')