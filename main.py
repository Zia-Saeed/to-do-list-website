from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import Login, SignUp, Contact
from sqlalchemy.orm import relationship
from datetime import datetime
import smtplib
import os


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///to_do_list.db'
app.config["SECRET_KEY"] = "893492U4JHDFSF32JDHFAJHSDJAHSD"
Bootstrap(app=app)
db = SQLAlchemy(app=app)
login_manager = LoginManager()
login_manager.__init__(app=app)



APP_PERMISSION = os.environ.get("password")
to_do_list = {

}


class ToDo(db.Model, UserMixin,):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    todo = db.Column(db.String, nullable=False)
    user_list = db.Column(db.Integer, db.ForeignKey("users.id"))
    user_list_obj = relationship("Users", back_populates="list_user")
    date = db.Column(db.Date, default=datetime.utcnow, nullable=False)


class Users(db.Model, UserMixin):
    __tablename = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    list_user = relationship("ToDo", back_populates="user_list_obj")


@login_manager.user_loader
def login_manager(user_id):
    return Users.query.get(user_id)


@app.route("/", methods=["POST", "GET"])
def home():
    global to_do_list
    if request.method == "POST":
        user = current_user.is_authenticated
        if user is False:

            to_do_list[request.form.get("to_do_list")] = request.form.get("dateInput")

            return redirect(url_for("home"))
        elif user is True:
            new_list = ToDo(
                todo=request.form.get("to_do_list"),
                user_list=current_user.id,
                date=datetime.strptime(request.form.get("dateInput"), "%Y-%m-%d")
            )
            db.session.add(new_list)
            db.session.commit()
            use = db.session.execute(db.select(Users).where(Users.id == current_user.id)).scalar()
            return render_template("index.html", user=use)
    if not current_user.is_authenticated:
        return render_template("index.html", list_elements=to_do_list)
    elif current_user.is_authenticated:
        if len(to_do_list) > 0:
            for td, d in to_do_list.items():
                new_list = ToDo(
                    todo=td,
                    user_list=current_user.id,
                    date=datetime.strptime(d, "%Y-%m-%d"),
                )
                db.session.add(new_list)
                db.session.commit()
        use = db.session.execute(db.select(Users).where(Users.id == current_user.id)).scalar()
        to_do_list = {}
        if use:
            return render_template("index.html", user=use)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    form = SignUp()
    if request.method == "POST" and form.validate_on_submit():
        password = generate_password_hash(password=form.password.data, salt_length=8, method="pbkdf2:sha256")
        new_user = Users(
            name=form.name.data,
            email=form.email.data,
            password=password,

        )
        db.session.add(new_user)
        db.session.commit()
        flash("Register Successfully")
        return redirect(url_for('login'))
    return render_template("signup.html", signup=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    if not current_user.is_authenticated:
        logout_user()
    form = Login()
    if request.method == "POST" and form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            password = check_password_hash(password=form.password.data, pwhash=user.password)
            if password:
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("Invalid Password")
                return redirect(url_for('login'))
        else:
            flash("Invalid Email")
            return redirect(url_for('login'))
    else:
        return render_template("login.html", login=form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/manage_lists")
def manage_list():
    user = Users.query.get(current_user.id)
    dat_to_do = {

    }
    for dat in user.list_user:
        d = f"{dat.date.year}-{dat.date.month}-{dat.date.day}"
        if d in dat_to_do.keys():
            dat_to_do[d][dat.id] = dat.todo
        else:
            dat_to_do[d] = {}
            dat_to_do[d][dat.id] = dat.todo
    return render_template('manage_list.html', to_do=dat_to_do)


@app.route("/logout")
def logout():
    logout_user()
    flash(message="Logout successfully")
    return redirect(url_for('home'))


@app.route("/done_list")
def done_list():
    list_id = int(request.args.get("id"))
    delete_list = db.session.execute(db.select(ToDo).where(ToDo.id == list_id)).scalar()
    db.session.delete(delete_list)
    db.session.commit()
    # use = db.session.execute(db.select(Users).where(Users.id == current_user.id)).scalar()
    return redirect(url_for('home'))


@app.route('/manage_display')
def manage_display():
    dic = eval(request.args.get("dit"))
    print(dic)
    return render_template("display_manage_list.html", dic=dic)


@app.route("/contact", methods=["POST", "GET"])
def contact():
    contact = Contact()
    if request.method == "POST" and contact.validate_on_submit():
        if not current_user.is_authenticated:
            flash("To Contact Us please Login or Signup")
            return render_template("contact.html", contact=contact)
        name = contact.name.data
        email = contact.email.data
        message = contact.message.data
        msg = f"Subject:Cafe website contact message\n\nFrom Email:{email}, Name: {name}\nMessage: {message}"
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            send_email = "zia.aseh@gmail.com"
            connection.login(
                user=send_email,
                password=APP_PERMISSION,
            )
            connection.sendmail(
                from_addr=send_email,
                to_addrs=send_email,
                msg=msg,
            )
            flash(message="Message sent Successfully")
    return render_template("contact.html", contact=contact)


if __name__ == '__main__':

    app.run(debug=True)