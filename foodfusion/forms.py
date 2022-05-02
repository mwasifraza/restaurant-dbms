from flask import session
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SelectField, SubmitField
from wtforms.validators import Length, Email, DataRequired, EqualTo, ValidationError
from foodfusion import cursor

districts = [
    ('','-- District --'),
    ('Central','Central'),
    ('East','East'),
    ('West','West'),
    ('South','South'),
    ('Malir','Malir'),
    ('Korangi','Korangi'),
    ('Keamari','Keamari'),
]

class RegisterForm(FlaskForm):

    def validate_username(self, username_to_check):
        user = cursor.execute("SELECT * FROM tbluser WHERE username=?",username_to_check.data).fetchone()
        if user:
            raise ValidationError('Username already exist!')
    
    def validate_email(self, email_to_check):
        email_add = cursor.execute("SELECT * FROM tbluser WHERE email=?",email_to_check.data).fetchone()
        if email_add:
            raise ValidationError('Email Address already exist!')

    fname = StringField(label='First Name', validators=[Length(min=3, max=30), DataRequired()])
    lname = StringField(label='Last Name', validators=[Length(min=3, max=30), DataRequired()])
    username = StringField(label='Username', validators=[Length(min=5, max=15), DataRequired()])
    email = StringField(label='Email Address', validators=[Email(), DataRequired()])
    mobile = StringField(label='Mobile No', validators=[Length(min=10, max=10), DataRequired()])
    password = PasswordField(label='Password', validators=[Length(min=5, max=15), DataRequired()])
    gender = SelectField(label='Gender', choices=[('','-- Gender --'), ('Male','Male'), ('Female','Female')], validators=[DataRequired()])
    submit = SubmitField(label='Sign Up')

class LoginForm(FlaskForm):
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Sign In')

class Residance(FlaskForm):
    address1 = StringField(label='Address Line 1', validators=[Length(max=75), DataRequired()])
    address2 = StringField(label='Address Line 2 (Optional)', validators=[Length(max=75)])
    city = SelectField(label='City', choices=[('','-- City --'), ('Karachi','Karachi')], validators=[DataRequired()])
    district = SelectField(label='District', choices=districts, validators=[DataRequired()])
    zipcode = IntegerField(label='Postal Zip Code', validators=[DataRequired()])
    submit = SubmitField(label='Update')

class BasicInfo(FlaskForm):

    def validate_username(self, username_to_check):
        user = cursor.execute("SELECT * FROM tbluser WHERE username=?",username_to_check.data).fetchone()
        if user:
            if user.username != session['username']:
                raise ValidationError('Username already exist!')

    fname = StringField(label='First Name', validators=[Length(min=3, max=30), DataRequired()])
    lname = StringField(label='Last Name', validators=[Length(min=3, max=30), DataRequired()])
    username = StringField(label='Username', validators=[Length(min=5, max=15), DataRequired()])
    submit = SubmitField(label='Update Profile')

class ContactDetails(FlaskForm):

    def validate_email(self, email_to_check):
        current_user = cursor.execute("SELECT email FROM tbluser WHERE id=?",session['id']).fetchone()
        user_email = cursor.execute("SELECT * FROM tbluser WHERE email=?",email_to_check.data).fetchone()
        if user_email:
            if user_email.email != current_user.email:
                raise ValidationError('Email Address already exist!')

    email = StringField(label='Email Address', validators=[Email(), DataRequired()])
    mobile = StringField(label='Mobile No', validators=[Length(min=10, max=10), DataRequired()])
    submit = SubmitField(label='Update Details')

class ChangePassword(FlaskForm):
    currentpass = PasswordField(label='Current Password', validators=[DataRequired()])
    newpass = PasswordField(label='New Password', validators=[Length(min=5, max=15), DataRequired()])
    confirmpass = PasswordField(label='Confirm New Password', validators=[EqualTo('newpass', message="Password don't match!")])
    submit = SubmitField(label='Update Password')

class Checkout(FlaskForm):
    submit = SubmitField(label='Checkout!')