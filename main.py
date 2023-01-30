from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user, current_user
from flask_gravatar import Gravatar
from functools import wraps
from form_class import PostForm, RegisterForm, LoginForm, CommentForm
from date_class import CurrentDate
from email_class import SendEmail

# GENERATE FLASK APPLICATION:
app = Flask(__name__)
app.config["SECRET_KEY"] = "TommyShelby"
ckeditor = CKEditor(app)
Bootstrap(app)

# CREATE SQLITE 3 DATABASE:
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///posts.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# CREATE BLOGS TABLE:
class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(1000), nullable=False)
    # --------------- Relationship Component ----------------- #
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comments", back_populates="comment_author")


# CREATE BlogPost TABLE:
class BlogPost(db.Model):
    __tablename__ = "blog_post"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # --------------- Relationship With Users Table ----------------- #
    author_id = db.Column(db.Integer, ForeignKey("users.id"))
    author = relationship("Users", back_populates="posts")
    # --------------- Relationship With Comments Table ----------------- #
    comments = relationship("Comments", back_populates="parent_post")


# CREATE COMMENT TABLE:
class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    # --------------- Relationship With Users Table ----------------- #
    author_id = db.Column(db.Integer, ForeignKey("users.id"))
    comment_author = relationship("Users", back_populates="comments")
    # --------------- Relationship With Blogpost Table ----------------- #
    post_id = db.Column(db.Integer, ForeignKey("blog_post.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


# INITIALIZE GRAVATAR
gravatar = Gravatar(
    app,
    size=60,
    rating="g",
    default="retro",
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None
)

# USER LOGIN SECTION:
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# ADMIN ONLY DECORATOR:
def admin_only(my_function):
    @wraps(my_function)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return my_function(*args, **kwargs)
    return decorated_function


# ROUTING AREA SECTION:
@app.route("/")
def home_page():
    identity_control = None
    if current_user.is_authenticated:
        identity_control = current_user.id
    my_data = db.session.query(BlogPost).all()
    return render_template("index.html",
                           blog_list=my_data,
                           user_id=identity_control,
                           logged_in=current_user.is_authenticated
                           )


# ====================================== NEW CHALLENGE ENDS =============================== #
@app.route("/register", methods=["GET", "POST"])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        entered_email = form.email.data
        check_user = Users.query.filter_by(email=entered_email).first()
        if check_user:
            flash("You've Already Signed Up with that Email, Try Login Instead!")
            return redirect(url_for("login_page"))
        elif not check_user:
            secured_password = generate_password_hash(
                password=form.password.data,
                method="pbkdf2:sha1",
                salt_length=8
            )
            new_user = Users(
                email=form.email.data,
                name=form.name.data,
                password=secured_password
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home_page"))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/login", methods=["GET", "POST"])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if not user:
            flash("That email does not exists, please try another one!")
            return redirect(url_for("login_page"))
        elif not check_password_hash(pwhash=user.password, password=form.password.data):
            flash("Password is not correct, please try another one!")
            return redirect(url_for("login_page"))
        elif user and check_password_hash(pwhash=user.password, password=form.password.data):
            login_user(user)
            return redirect(url_for("home_page"))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/logout")
def logout_page():
    logout_user()
    return redirect(url_for("home_page"))


# ====================================== NEW CHALLENGE ENDS =============================== #
@app.route("/post", methods=["GET", "POST"])
def post_page():
    current_post_id = request.args.get("id")
    identity_control = None
    if current_user.is_authenticated:
        identity_control = current_user.id
    my_data = BlogPost.query.get(current_post_id)
    # ------------ Form on Submit ---------------- #
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comments(
                body=form.comment.data,
                author_id=current_user.id,
                post_id=current_post_id
            )
            db.session.add(new_comment)
            db.session.commit()
            form.comment.data = ""
        else:
            flash("To Leave Comment, You need to login in with your Account!")
            return redirect(url_for("login_page"))
    return render_template("post.html",
                           blog_post=my_data,
                           user_id=identity_control,
                           logged_in=current_user.is_authenticated,
                           form=form
                           )


@app.route("/add", methods=["GET", "POST"])
@admin_only
def add_page():
    # check if POST request was submitted and generate 'home_page':
    form = PostForm()
    if form.validate_on_submit():
        date_tool = CurrentDate()
        current_date = date_tool.get_date()
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=f"{current_date['month']} {current_date['day']}, {current_date['year']}",
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        db.session.close()
        return redirect(url_for("home_page"))
    # standard way to open add page with GET request:
    heading = "New Post"
    return render_template("make-post.html",
                           form=form,
                           head=heading,
                           logged_in=current_user.is_authenticated
                           )


@app.route("/edit", methods=["GET", "POST"])
@admin_only
@login_required
def edit_page():
    current_id = request.args.get("id")
    current_post = BlogPost.query.get(current_id)
    # if POST request will be submitted, update record in database and go back to Updated Post:
    new_form = PostForm()
    if new_form.validate_on_submit():
        current_post.title = new_form.title.data
        current_post.subtitle = new_form.subtitle.data
        current_post.body = new_form.body.data
        current_post.img_url = new_form.img_url.data
        db.session.commit()
        db.session.close()
        return redirect(url_for("post_page", id=current_id))
    # standard way to open 'edit page' with GET request and current post information:
    form = PostForm(
        title=current_post.title,
        subtitle=current_post.subtitle,
        img_url=current_post.img_url,
        author=current_post.author,
        body=current_post.body
    )
    heading = "Edit Post"
    return render_template("make-post.html",
                           form=form,
                           head=heading,
                           logged_in=current_user.is_authenticated
                           )


@app.route("/delete")
@admin_only
@login_required
def delete_page():
    # This current id - also can be accessed through url/endpoint -> as function argument:
    # (1."/delete/<int:current_id>"   2.def delete_page(current_id))
    current_id = request.args.get("id")
    current_record = BlogPost.query.get(current_id)
    db.session.delete(current_record)
    db.session.commit()
    db.session.close()
    return redirect(url_for("home_page"))


@app.route("/about")
def about_page():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact", methods=["POST", "GET"])
def contact_page():
    if request.method == "GET":
        return render_template("contact.html", my_answer="Contact Me", logged_in=current_user.is_authenticated)
    elif request.method == "POST":
        user_name = request.form["userName"]
        user_email = request.form["userEmail"]
        user_phone = request.form["userPhone"]
        user_message = f'By {user_name} \n{request.form["userMessage"]} \nmy phone number: {user_phone}'
        my_gmail = SendEmail(sender=user_email, subject="Message Via Your Blog", body=user_message)
        my_gmail.send_mail()
        return render_template("contact.html",
                               my_answer="Your Message sent successfully",
                               logged_in=current_user.is_authenticated
                               )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
