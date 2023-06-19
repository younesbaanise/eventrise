from flask import Flask, render_template, url_for, redirect, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, TextAreaField, DateField, TimeField, SubmitField, IntegerField
from wtforms.validators import InputRequired, DataRequired, Length, ValidationError
from flask_bcrypt import Bcrypt 
from wtforms.widgets import TextArea
from flask_wtf.file import FileField, FileAllowed
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import os

# create a flask instance
app = Flask(__name__) # helps flask to find all of our files in our directory here
# add database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# secret key
app.config['SECRET_KEY'] = "this is my secret key"

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# initialize the database
db = SQLAlchemy()
app.app_context().push()
db.init_app(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# Configuring LoginManager for User Authentication
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Loader Function for LoginManager
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# create Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    Fname = db.Column(db.String(20), nullable=False) # 20 stands for max len of caractere is 20 letters | and nullable means that the user have to enter his name
    Lname = db.Column(db.String(20), nullable=False) # 20 stands for max len of caractere is 20 letters | and nullable means that the user have to enter his name
    email = db.Column(db.String(50), nullable=False, unique=True) # unique means that you can't login with the same email
    password = db.Column(db.String(80), nullable=False)
    profile_pic = db.Column(db.String(100), nullable=True)
    posts = db.relationship('Posts', backref='poster')


    # create a string
    def __repr__(self):
        return '<Name %r>' %self.Fname # this will put the user name 

# create a register form
class RegisterForm(FlaskForm):
    Fname = StringField(validators=[
                        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Enter your first name", "autocomplete":"off"})
    
    Lname = StringField(validators=[
                        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Enter your last name", "autocomplete":"off"})
    
    email = StringField(validators=[
                        InputRequired(), Length(max=50)], render_kw={"placeholder": "Enter your email", "type":"email", "autocomplete":"off"})

    password = PasswordField(validators=[
                        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Enter your Password", "autocomplete":"off"})

    submit = SubmitField('Register')
    # validate form
    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            flash('This email already exists. Please choose a different one.')


# create a login from
class LoginForm(FlaskForm):
    email = StringField(validators=[
                        InputRequired(), Length(max=50)], render_kw={"placeholder": "email", "type":"email", "autocomplete":"off"})

    password = PasswordField(validators=[
                        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password", "autocomplete":"off"})

    submit = SubmitField('Login')


# create Name page
@app.route('/name', methods=['GET', 'POST'])
def name():
    form = RegisterForm()
    # Validate form
    if form.validate_on_submit():
        Fname = form.Fname.data
        form.Fname.data = ''
    return render_template("dashboard.html", form=form, Fname=Fname) 


# home page
@app.route('/')
def home():
    return render_template('index.html')


# User Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash('Welcome! Enjoy your stay.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password. Please try again.', 'error')
        else:
            flash('Email does not exist. Please register.', 'error')

    return render_template('login.html', form=form)

# dashboard route
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    Fname = current_user.Fname if current_user.is_authenticated else None
    # grab all post events 
    posts = Posts.query.order_by(Posts.id.desc())
    return render_template('dashboard.html', Fname=Fname, posts=posts)


# logout route
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    # validte form
    if form.validate_on_submit():
        existing_user_email = User.query.filter_by(email=form.email.data).first()
        if existing_user_email:
            flash('That email already exists. Please choose a different one.', 'error')
        else:
            hashed_password = bcrypt.generate_password_hash(form.password.data)
            new_user = User(
                Fname=form.Fname.data,
                Lname=form.Lname.data,
                email=form.email.data,
                password=hashed_password
            )
            db.session.add(new_user)
            try: 
                db.session.commit()
                flash('Registration successful!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while registering. Please try again.', 'error')

    return render_template('register.html', form=form)


# create a edit from class
class EditForm(FlaskForm):
    Fname = StringField(validators=[
                        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Enter your first name", "autocomplete": "off"})

    email = StringField(validators=[
                        InputRequired(), Length(max=50)], render_kw={"placeholder": "Enter your email", "type": "email", "autocomplete": "off"})

    password = PasswordField(validators=[
                        Length(min=8, max=20)], render_kw={"placeholder": "Enter your Password", "autocomplete": "off"})

    profile_pic = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])

    submit = SubmitField('Update')
    # validate form
    def validate_email(self, email):
        if email.data != current_user.email:
            existing_user_email = User.query.filter_by(email=email.data).first()
            if existing_user_email:
                flash('This email already exists. Please choose a different one.', 'error')
                raise ValidationError('Email already exists')
                



# profile route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditForm()

    if form.validate_on_submit():
        # Check if email already exists in the database
        existing_user_email = User.query.filter_by(email=form.email.data).first()
        if existing_user_email and existing_user_email.id != current_user.id:
            flash('This email already exists. Please choose a different one.', 'error')
        else:
            # Update user information if email is valid
            current_user.Fname = form.Fname.data
            current_user.email = form.email.data

            if form.password.data:
                current_user.password = bcrypt.generate_password_hash(form.password.data)

            if form.profile_pic.data:
                # Handle profile picture upload
                profile_pic = form.profile_pic.data
                filename = secure_filename(profile_pic.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic.save(save_path)
                current_user.profile_pic = filename
            
            db.session.commit()
            flash('Your information has been updated successfully!', 'success')
            return redirect(url_for('dashboard'))
    else:
        form.Fname.data = current_user.Fname
        form.email.data = current_user.email

    return render_template('profile.html', form=form)


# about route
@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

# calendar route
@app.route('/calendar')
@login_required
def calendar():
    posts = Posts.query.all()
    return render_template('calendar.html', posts=posts)

# Posts Model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    max_guests = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image_filename = db.Column(db.String(255))

# post from
class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()], render_kw={ "autocomplete": "off"})
    event_type = StringField('Event Type', validators=[DataRequired()], render_kw={ "autocomplete": "off"})
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()],)
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()], render_kw={ "autocomplete": "off"})
    max_guests = IntegerField('Numbers of Guests', validators=[DataRequired()], render_kw={ "autocomplete": "off"})
    description = StringField('Description', validators=[DataRequired()], widget=TextArea(), render_kw={ "autocomplete": "off"})
    image = FileField('Event Image', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')


# create form
@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PostForm()

    # validate form
    if form.validate_on_submit():
        image = form.image.data
        poster =current_user.id
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        post = Posts(
            title=form.title.data,
            event_type=form.event_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            location=form.location.data,
            max_guests=form.max_guests.data,
            description=form.description.data,
            poster_id=poster,
            #image_filename=filename if image else None  # Store the image filename in the database
        )
        # Clear the form
        form.title.data = ''
        form.event_type.data = ''
        form.start_date.data = ''
        form.end_date.data = ''
        form.start_time.data = ''
        form.end_time.data = ''
        form.location.data = ''
        form.max_guests.data = ''
        form.description.data = ''

        # Add post data to the database
        db.session.add(post)
        db.session.commit()

        flash("Event Submitted Successfully!", 'success')

    return render_template('create.html', form=form)


# update post route
@app.route('/posts/update/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()

    if form.validate_on_submit():
        # Handle the file upload
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post.image_filename = filename
    
        post.title = form.title.data
        post.event_type = form.event_type.data
        post.start_date = form.start_date.data
        post.end_date = form.end_date.data
        post.start_time = form.start_time.data
        post.end_time = form.end_time.data
        post.location = form.location.data
        post.max_guests = form.max_guests.data
        post.description = form.description.data


        db.session.commit()
        flash("Event has been updated", 'success')
        return redirect(url_for('dashboard', id=post.id))
    
    if current_user.id == post.poster_id:
        form.title.data = post.title
        form.event_type.data = post.event_type
        form.start_date.data = post.start_date
        form.end_date.data = post.end_date
        form.start_time.data = post.start_time
        form.end_time.data = post.end_time
        form.location.data = post.location
        form.max_guests.data = post.max_guests
        form.description.data = post.description
        return render_template('edit_post.html', form=form, post=post) # add post=post here

    else:
        posts = Posts.query.order_by(Posts.id.desc())
        return render_template('dashboard.html', posts=posts)

# delete post route
@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id:

        try:
            db.session.delete(post_to_delete)
            db.session.commit()

            flash("Event was deleted", 'success')

            posts = Posts.query.order_by(Posts.id.desc())
            return render_template('dashboard.html', posts=posts)

        except:
            flash('there was a probleme', 'error')


    else:
        posts = Posts.query.order_by(Posts.id.desc())
        return render_template('dashboard.html', posts=posts)




@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')


#create a custom error pages

#invalid url
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# internal server error thing
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)


