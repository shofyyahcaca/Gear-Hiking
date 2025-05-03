import os
from datetime import date
import stripe
import json
from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
from flask_bcrypt import Bcrypt
from forms import SignUp, Login, contactForm, searchRoom, addRoom, editMyProfile, bookingForm, forgotpassword, changepassword
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv


#Creating Database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

load_dotenv()  # Memuat variabel dari .env
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL belum diset dalam lingkungan atau file .env")

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = '123my456secret789key'


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



stripe.api_key = os.getenv("SEC_KEY")



#Calculate Age Function
def calculateAge(birthDate):
    today = date.today()
    age = today.year - birthDate.year - ((today.month, today.day) < (birthDate.month, birthDate.day))

    return age



#Calculate Order Amount Function for Stripe
def calculate_order_amount(total):
    total = session.get('total')

    return int(total*100)



#Index Route
@app.route('/', methods=['GET', 'POST'])
def index():

    user_id = session.get('u_id')
    user_name = session.get('u_name')

    sroom = searchRoom()

    if sroom.validate_on_submit():
        checkin = sroom.checkin.data
        checkout = sroom.checkout.data
        no_of_guests = sroom.no_of_guests.data

        d0 = checkin
        d1 = checkout

        delta = d1 - d0
        session['days'] = delta.days
        session['checkin'] = sroom.checkin.data
        session['checkout'] = sroom.checkout.data
        session['no_of_guests'] = sroom.no_of_guests.data

        return redirect(url_for('roomdetails'))



    return render_template('index.html', sroom=sroom, user_id=user_id, user_name=user_name)



#Search Room from Index based on Search Criteria
@app.route('/roomdetails', methods=['GET', 'POST'])
def roomdetails():

    user_id = session.get('u_id')
    user_name = session.get('u_name')

    days = session.get('days')
    checkin_date = session.get('checkin')
    checkout_date = session.get('checkout')
    no_of_guests = session.get('no_of_guests')

    checkin = checkin_date.strftime("%d-%m-%Y")
    checkout = checkout_date.strftime("%d-%m-%Y")



    roomdt = db.execute("SELECT * FROM room_details").fetchall()



    return render_template('roomdetails.html', days=days, checkin=checkin, checkout=checkout, no_of_guests=no_of_guests, roomdt=roomdt, user_id=user_id, user_name=user_name)




#Check-Out Page
@app.route('/checkout/<int:roomid>', methods=['GET', 'POST'])
def checkout(roomid):

    user_id = session.get('u_id')
    user_name = session.get('u_name')


    days = session.get('days')
    checkin_date = session.get('checkin')
    checkout_date = session.get('checkout')

    checkin = checkin_date.strftime("%d-%m-%Y")
    checkout = checkout_date.strftime("%d-%m-%Y")

    specific_room_detail = db.execute("SELECT * FROM room_details WHERE id = :id", {"id" : roomid}).fetchone()


    adro = addRoom()


    if adro.validate_on_submit():
        extraroom = adro.extraRoom.data

    noofrooms = adro.extraRoom.data


    if noofrooms:
        tax_amount = specific_room_detail.price * .12
        total = specific_room_detail.price * days * int(noofrooms) + tax_amount
    else:
        tax_amount = specific_room_detail.price * .12
        total = specific_room_detail.price * days + tax_amount



    session['tax_amount'] = tax_amount
    session['total'] = total
    session['roomid'] = roomid



    return render_template('checkout.html', user_id=user_id, user_name=user_name, specific_room_detail=specific_room_detail, checkin=checkin, checkout=checkout, tax_amount=tax_amount, total=total, days=days, adro=adro)




#Booking Form Route
@app.route('/booknow', methods=['GET', 'POST'])
def booknow():

    user_id = session.get('u_id')
    user_name = session.get('u_name')
    user_email = session.get('u_email')


    if user_id is None:
        return redirect(url_for('login', next='booking'))


    days = session.get('days')
    checkin_date = session.get('checkin')
    checkout_date = session.get('checkout')

    checkin = checkin_date.strftime("%d-%m-%Y")
    checkout = checkout_date.strftime("%d-%m-%Y")


    tax_amount = session.get('tax_amount')
    total = session.get('total')
    roomid = session.get('roomid')

    specific_room_detail = db.execute("SELECT * FROM room_details WHERE id = :id", {"id" : roomid}).fetchone()


    bf = bookingForm()


    if bf.validate_on_submit():
        prefix = bf.prefix.data
        fname = bf.fname.data
        lname = bf.lname.data
        dob = bf.dob.data
        isdcode = bf.isdcode.data
        contactno = bf.contactno.data
        sp_req = bf.sp_req.data



        age = calculateAge(bf.dob.data) #Age Calculator Function will be called and will store the Age


        db.execute("INSERT INTO booking_details (prefix, fname, lname, email, dob, isdcode, contactno, sp_req, checkin, checkout, nights, total, room_type) VALUES (:prefix, :fname, :lname, :email, :dob, :isdcode, :contactno, :sp_req, :checkin, :checkout, :nights, :total, :room_type)", {"prefix" : prefix, "fname" : fname, "lname" : lname, "email" : user_email, "dob" : age, "isdcode" : isdcode, "contactno" : contactno, "sp_req" : sp_req, "checkin" : checkin, "checkout" : checkout, "nights" : days, "total" : total, "room_type" : specific_room_detail.roomtype})
        db.commit()


        return redirect(url_for('payment'))


    return render_template('booknow.html', bf=bf, user_id=user_id, user_name=user_name, checkin=checkin, checkout=checkout, tax_amount=tax_amount, total=total, days=days, specific_room_detail=specific_room_detail)




@app.route('/payment', methods=['GET', 'POST'])
def payment():

    user_id = session.get('u_id')
    user_name = session.get('u_name')
    total = session.get('total')


    return render_template('payment.html', total=total, user_id=user_id, user_name=user_name)


#Payment Route
@app.route('/create-payment-intent', methods=['POST'])
def create_payment():
    try:
        data = json.loads(request.data)
        intent = stripe.PaymentIntent.create(
            amount=calculate_order_amount(data['items']),
            currency='inr',
            description='Hotel Booking'
        )
        return jsonify({
          'clientSecret': intent['client_secret']
        })
    except Exception as e:
        return jsonify(error=str(e)), 403



#Thank You Page
@app.route('/thanks', methods=['GET', 'POST'])
def thanks():

    user_id = session.get('u_id')
    user_name = session.get('u_name')


    return render_template('thanks.html', user_id=user_id, user_name=user_name)




#My Bookings
@app.route('/user_booking', methods=['GET', 'POST'])
def user_booking():



    user_id = session.get('u_id')
    user_name = session.get('u_name')
    user_email = session.get('u_email')

    if user_id is None:
        return redirect(url_for('login'))



    bd = db.execute("SELECT * FROM booking_details WHERE email = :email", {"email" : user_email}).fetchall()




    return render_template('user-booking.html', user_id=user_id, user_name=user_name, bd=bd)





#Login + SignUp Route
@app.route('/login', methods=['GET', 'POST'])
def login():



    user_id = session.get('u_id')
    if user_id:
        return redirect(url_for('index'))

    form_one = SignUp()

    if form_one.validate_on_submit():
        fname = form_one.fname.data
        lname = form_one.lname.data
        username_one = form_one.username_one.data
        email_one = form_one.email_one.data
        password = form_one.password.data
        contactno = form_one.contactno.data

        hash_password = bcrypt.generate_password_hash(password).decode('utf-8')

        db.execute("INSERT INTO reg_accounts (fname, lname, username, email, password, contactno) VALUES (:fname, :lname, :username, :email, :password, :contactno)", {"fname" : fname, "lname" : lname, "username" : username_one, "email" : email_one, "password" : hash_password, "contactno" : contactno})
        db.commit()

        flash(f'Your Account has been created successfully, you can now login.', 'success')

        return redirect(url_for('login'))


    form_two = Login()

    if form_two.validate_on_submit():
        username_two = form_two.username_two.data
        password = form_two.password.data

        user = db.execute("SELECT * FROM reg_accounts WHERE username = :username", {"username" : username_two}).fetchone()

        if user and bcrypt.check_password_hash(user.password, password) is True:
            session['u_id'] = user.id
            session['u_name'] = user.fname
            session['u_email'] = user.email
            if request.args.get('next') == 'booking':   #Book Now Route will be called back
                return redirect(url_for('booknow'))
            return redirect(url_for('index'))
        else:
            flash(f'You have entered incorrect credentials, please check again', 'warning')
            return redirect(url_for('login'))

    return render_template('login.html', form_one=form_one, form_two=form_two)


#Logout Route
@app.route('/logout', methods=['GET', 'POST'])
def logout():

    session.pop('u_id', None)

    flash(f'You have successfully logout', 'success')

    return redirect(url_for('login'))


#Forgot Password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():


    user_id = session.get('u_id')
    if user_id:
        return redirect(url_for('index'))


    fp = forgotpassword()


    if fp.validate_on_submit():
        email = fp.email.data

        user = db.execute("SELECT * FROM reg_accounts WHERE email = :email", {"email" : email}).fetchone()
        session['fpemail'] = user.email


        if user:
            return redirect(url_for('change_password'))
        else:
            flash(f'Sorry, your email does not exist, please check again.', 'danger')
            return redirect(url_for('forgot_password'))




    return render_template('forgotpassword.html', fp=fp)



#Change Password Field
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():

    user_id = session.get('u_id')
    if user_id:
        return redirect(url_for('index'))


    fpemail = session.get('fpemail')


    cp = changepassword()


    if cp.validate_on_submit():
        password = cp.password.data



        userpass = db.execute("SELECT password FROM reg_accounts WHERE email = :email", {"email" : fpemail}).fetchone()



        if bcrypt.check_password_hash(userpass.password, password) is True:
            flash(f'please try a different password, this is your current password', 'danger')
            return redirect(url_for('change_password'))
        else:
            hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.execute("UPDATE reg_accounts SET password = :password WHERE email = :email", {"password" : hash_password , "email" : fpemail })
            flash(f'Your Password has been changed successfully, you can now login.', 'success')
            db.commit()


        return redirect(url_for('login'))


    return render_template('changepassword.html', cp=cp)


#Delete Profile + Data
@app.route('/delete', methods=['GET', 'POST'])
def delete():


    user_id = session.get('u_id')
    user_name = session.get('u_name')



    db.execute("DELETE FROM reg_accounts WHERE id = :id", {"id" : user_id})
    db.commit()

    session.pop('u_id', None)


    flash(f'Sorry to see you go, your Account has been deleted successfully', 'danger')

    return redirect(url_for('login'))





#My Account Route
@app.route('/myaccount', methods=['GET', 'POST'])
def myaccount():

    user_id = session.get('u_id')
    user_name = session.get('u_name')

    us_detail = db.execute("SELECT * FROM reg_accounts WHERE id = :id", {"id" : user_id}).fetchone()



    emp = editMyProfile()


    if emp.validate_on_submit():
        fname = emp.fname.data
        lname = emp.lname.data
        username = emp.username.data
        email = emp.email.data
        contactno = emp.contactno.data



        if emp.fname.data:
            db.execute("UPDATE reg_accounts SET fname = :fname WHERE id = :id", {"fname" : fname , "id" : user_id })
            flash(f'Your First Name has been changed successfully, please refresh to view changes', 'success')
            db.commit()
        if emp.lname.data:
            db.execute("UPDATE reg_accounts SET lname = :lname WHERE id = :id", {"lname" : lname, "id" : user_id })
            flash(f'Your Last Name has been changed successfully, please refresh to view changes', 'success')
            db.commit()
        if emp.username.data:
            db.execute("UPDATE reg_accounts SET username = :username WHERE id = :id", {"username" : username, "id" : user_id })
            flash(f'Your Username has been changed successfully, please refresh to view changes', 'success')
            db.commit()
        if emp.email.data:
            db.execute("UPDATE reg_accounts SET email = :email WHERE id = :id", {"email" : email, "id" : user_id })
            flash(f'Your Email has been changed successfully, please refresh to view changes', 'success')
            db.commit()
        if emp.contactno.data:
            db.execute("UPDATE reg_accounts SET contactno = :contactno WHERE id = :id", {"contactno" : contactno, "id" : user_id })
            flash(f'Your Contact Number has been changed successfully, please refresh to view changes', 'success')
            db.commit()




    return render_template('myprofile.html', user_id=user_id, user_name=user_name, us_detail=us_detail, emp=emp)



#About Us Route
@app.route('/about', methods=['GET', 'POST'])
def about():

    user_id = session.get('u_id')
    user_name = session.get('u_name')


    return render_template('about.html', user_id=user_id, user_name=user_name)


#Rooms & Suites Route
@app.route('/room', methods=['GET', 'POST'])
def room():

    user_id = session.get('u_id')
    user_name = session.get('u_name')


    return render_template('room.html', user_id=user_id, user_name=user_name)


#Gallery Route
@app.route('/gallery', methods=['GET', 'POST'])
def gallery():

    user_id = session.get('u_id')
    user_name = session.get('u_name')


    return render_template('gallery.html', user_id=user_id, user_name=user_name)


#Contact Us Route
@app.route('/contact', methods=['GET', 'POST'])
def contact():

    user_id = session.get('u_id')
    user_name = session.get('u_name')


    cform = contactForm()


    if cform.validate_on_submit():
        fname = cform.fname.data
        email_two = cform.email_two.data
        contactno = cform.content.data
        message = cform.message.data


        flash(f'Thank You for contacting us. We will get in touch with you soon.', 'success')

        return redirect(url_for('contact'))

    return render_template('contact.html', cform=cform, user_id=user_id, user_name=user_name)