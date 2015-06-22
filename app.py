import os

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, EqualTo, ValidationError


app = Flask(__name__)
app.config['SECRET_KEY'] = 'test for prom.ua'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)

bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.password == form.password.data:
            login_user(user, form.remember_me.data)
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thanks for registration. You can now login.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/q/', methods=['GET', 'POST'])
def newanswer():
    form = request.form
    answer = Answer(answer_text=form['answer'], question_id=session['q_number'], user_id=session['user_id'])
    db.session.add(answer)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/q/<int:number>', methods=['GET', 'POST'])
def question(number):
    question = Question.query.filter_by(id=number).first()
    answers = Answer.query.filter_by(question_id=number).all()
    form = AnswerForm()
    session['q_number'] = number
    return render_template('question.html', form=form, question=question, answers=answers)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session['user_id'] = None
    flash('You have been logged out.')
    flash("Вы вышли. Теперь Вы не можете задавать вопросы и давать ответы.")
    return redirect(url_for('index'))


@app.route('/')
def index():
    questions = Question.query.order_by(Question.id.desc()).all()
    return render_template('index.html', username=session.get('username'), questions=questions)


@app.route('/newquestion', methods=['GET', 'POST'])
def newquestion():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(q_text=form.question.data, author=current_user._get_current_object())
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('newquestion.html', form=form)

# ==================== FORMS =========================


class RegistrationForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm',
                                                                             message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Submit')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField('Log in')


class QuestionForm(Form):
    question = TextAreaField('Question:', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AnswerForm(Form):
    answer = TextAreaField('Answer:', validators=[DataRequired()])
    submit = SubmitField('Submit')


# ========================================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================== DB section ==============================


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode, unique=True, index=True)
    password = db.Column(db.String(128))
    questions = db.relationship('Question', backref='author', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    q_text = db.Column(db.Unicode, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    answers = db.relationship('Answer', backref='q_item', lazy='dynamic')

    def __repr__(self):
        return '%s' % self.question_text


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.String(64), unique=True, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Answer %r>' % self.unswer_text


if __name__ == '__main__':
    app.run(debug=True)
