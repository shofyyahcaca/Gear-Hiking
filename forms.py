import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DecimalField, MultipleFileField, SubmitField
from wtforms.fields import EmailField, TelField, DateField
from wtforms.validators import DataRequired, InputRequired, Length, Email, ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


class SignUp(FlaskForm):
    fname = StringField('First Name', validators=[DataRequired(), Length(max=12)])
    lname = StringField('Last Name', validators=[DataRequired(), Length(max=12)])
    username_one = StringField('Username', validators=[DataRequired()])
    email_one = EmailField('Email ID', validators=[DataRequired(), Email(message='Invalid Email')])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=16)])
    contactno = TelField('Phone Number', validators=[DataRequired(), Length(min=10, max=10)])
    submit = SubmitField('Create Account!')

    def validate_email(self, email):
        user_one = db.execute("SELECT * FROM reg_accounts WHERE username = :username", {"username" : username_one.data}).fetchone()

        if user_one:
            raise ValidationError('This Username is already registered with us, please use another username.')


    def validate_email(self, email):
        user = db.execute("SELECT * FROM reg_accounts WHERE email = :email", {"email" : email_one.data}).fetchone()

        if user:
            raise ValidationError('This Email ID is already registered with us, please use another email id.')


    def validate_contactno(self, contactno):
        if len(contactno.data) <=9 and len(contactno.data) >=10:
            raise ValidationError('Phone Number must be of 10 digits only.')



class Login(FlaskForm):
    username_two = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')



class contactForm(FlaskForm):
    fname = StringField('Full Name', validators=[DataRequired()])
    email_two = EmailField('Email ID', validators=[DataRequired(), Email(message='Invalid Email')])
    contactno = TelField('Phone', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=250)])
    submit = SubmitField('Send Message')



class searchRoom(FlaskForm):
    checkin = DateField('Check-In Date', validators=[DataRequired()])
    checkout = DateField('Check-Out Date', validators=[DataRequired()])
    no_of_guests = SelectField('No. of Guests', choices=[(' ', ' '), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')])
    submit = SubmitField('Check Availability')



class addRoom(FlaskForm):
    extraRoom = SelectField('Extra Room', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')])
    submit = SubmitField('Add Room')



class bookingForm(FlaskForm):
    prefix = SelectField('Title', choices=[(' ', ' '), ('Mr', 'Mr'), ('Mrs', 'Mrs'), ('Miss', 'Miss'), ('Dr', 'Dr')], validators=[DataRequired()])
    fname = StringField('First Name', validators=[DataRequired()])
    lname = StringField('Last Name', validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    isdcode = DecimalField('Country Code', validators=[DataRequired()])
    contactno = TelField('Phone Number', validators=[DataRequired(), Length(min=10, max=10)])
    sp_req = StringField('Special Request')
    submit = SubmitField('Proceed')


    def validate_contactno(self, contactno):
        if len(contactno.data) <=9 and len(contactno.data) >=10:
            raise ValidationError('Phone Number must be of 10 digits only.')



class editMyProfile(FlaskForm):
    fname = StringField('First Name')
    lname = StringField('Last Name')
    username = StringField('Username')
    email = EmailField('Email ID')
    contactno = TelField('Phone Number')
    submit = SubmitField('Update Profile')



class forgotpassword(FlaskForm):
    email = EmailField('Enter your Email ID', validators=[DataRequired(), Email(message='Invalid Email')])
    submit = SubmitField('Forgot Password')


class changepassword(FlaskForm):
    password = PasswordField('Enter Password', validators=[DataRequired(), Length(min=8, max=16)])
    submit = SubmitField('Change Password')