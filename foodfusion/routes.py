from flask import render_template, redirect, url_for, request, flash, session
from foodfusion import app, conn, cursor, bcrypt, user_login, current_date
from foodfusion.forms import RegisterForm, LoginForm, Residance, BasicInfo, ContactDetails, ChangePassword, Checkout

@app.route('/')
def home():
    if user_login():
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))

    return render_template('index.html')

@app.route('/order', methods=['GET','POST'])
def order_page():
    checkout_form = Checkout()
    if request.method == "POST":
        if not user_login():
            flash('To continue, please login first!', category='warning')
            return redirect(url_for('login_page', next=request.path))
        else:
            item_id = request.form['item-id']
            item_name = request.form['item-name']
            size = request.form['size']
            cart = cursor.execute("SELECT * FROM tblcart WHERE id=?",session['id']).fetchone()
            itemDetail = cursor.execute("SELECT * FROM tblitem_details WHERE itmdet_id=?",size).fetchone()
            add_item = [cart.cart_id,item_id,item_name,itemDetail.size,itemDetail.price,1,itemDetail.price]
            cursor.execute("INSERT INTO tblcart_details VALUES(?,?,?,?,?,?,?)",add_item)
            conn.commit()
            active_cart_det = cursor.execute("SELECT * FROM tblcart_details WHERE cart_id=?",cart.cart_id).fetchall()
            amount = 0
            for item in active_cart_det:
                amount += item.total_price
            cursor.execute("UPDATE tblcart SET total_price=? WHERE id=?",amount,session['id'])
            conn.commit()
            flash("Item added to cart!", category='success')
            return redirect(url_for('order_page'))

    if user_login():
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        active_cart = cursor.execute("SELECT * FROM tblcart WHERE id=?",session['id']).fetchone()
        active_cart_det = cursor.execute("SELECT * FROM tblcart_details WHERE cart_id=?",active_cart.cart_id).fetchall()
    else:
        active_cart = None
        active_cart_det = None

    items = cursor.execute("SELECT * FROM tblitem").fetchall()
    item_details = cursor.execute("SELECT * FROM tblitem_details").fetchall()
    return render_template('make-order.html', items=items, item_details=item_details, active_cart=active_cart,
       active_cart_det=active_cart_det, checkout_form=checkout_form)

@app.route('/order/checkout', methods=['GET','POST'])
def checkout():
    checkout_form = Checkout()
    if checkout_form.validate_on_submit():
        user = cursor.execute("SELECT * FROM tbluser WHERE id=?",session['id']).fetchone()
        userdet = cursor.execute("SELECT * FROM tbluser_details WHERE id=?",session['id']).fetchone()
        cart = cursor.execute("SELECT * FROM tblcart WHERE id=?",session['id']).fetchone()
        if userdet.address1 != None and userdet.city != None and userdet.district != None and userdet.zipcode != None:
            if cart.total_price != 0:
                cartdetails = cursor.execute("SELECT * FROM tblcart_details WHERE cart_id=?",cart.cart_id).fetchall()
                order_info = [user.id, user.fname+" "+user.lname, cart.total_price, current_date, "confirmed"]
                orderid = cursor.execute("INSERT INTO tblorder OUTPUT INSERTED.order_id VALUES(?,?,?,?,?)",order_info).fetchone()
                for item in cartdetails:
                    order_info_det = [orderid[0], item.item_id, item.item_name, item.size, item.price, item.qty, item.total_price]
                    cursor.execute("INSERT INTO tblorder_details VALUES(?,?,?,?,?,?,?)",order_info_det)
                cursor.execute("DELETE FROM tblcart_details WHERE cart_id=?",cart.cart_id)
                cursor.execute("UPDATE tblcart SET total_price=0 WHERE id=?",session['id'])
                conn.commit()
                order = cursor.execute("SELECT * FROM tblorder WHERE order_id=?",orderid).fetchone()
                order_det = cursor.execute("SELECT * FROM tblorder_details WHERE order_id=?",orderid).fetchall()
                return render_template('checkout.html', order=order, order_det=order_det)
            else:
                flash("Your cart is empty!", category='danger')
                return redirect(url_for('order_page'))
        else:
            flash("You did not enter your address", category='danger')
            return redirect(url_for('user_settings'))

    return redirect(url_for('order_page'))

@app.route('/order/remove/<int:cid>')
def remove_item(cid):
    if session['id'] and session['role'] == 'user':
        amount = cursor.execute("SELECT total_price FROM tblcart_details WHERE cartdet_id=?",cid).fetchone()
        active_cart = cursor.execute("SELECT * FROM tblcart WHERE id=?",session['id']).fetchone()
        cutPrice = active_cart.total_price - amount.total_price
        cursor.execute("UPDATE tblcart SET total_price=? WHERE id=?",cutPrice,session['id'])
        cursor.execute("DELETE FROM tblcart_details WHERE cartdet_id=?",cid)
        conn.commit()
        flash('Item has been removed!', category='info')
    return redirect(url_for('order_page'))

@app.route('/fetchdata', methods=['GET','POST'])
def fetch_data():
    if request.method == "POST":
        size_id = request.form['id']
        item = cursor.execute('SELECT price FROM tblitem_details WHERE itmdet_id=?',size_id).fetchone()
        price = str(item.price)
        return price
    return redirect(url_for('home'))


# admin routes
@app.route('/admin', methods=['GET','POST'])
def admin_page():
    adminlogin = LoginForm()
    if user_login():
        return redirect(url_for('home'))
    else:
        return render_template('admin-login.html', adminlogin=adminlogin)

@app.route('/delete/<int:uid>')
def delete_user(uid):
    cursor.execute("DELETE FROM tbluser_details WHERE id=?",uid)
    cursor.execute("DELETE FROM tbluser WHERE id=?",uid)
    conn.commit()
    flash('User has been deleted!', category='info')
    return redirect(url_for('register_page'))

@app.route('/login', methods=['GET','POST'])
def login_page():
    loginform = LoginForm()
    if loginform.validate_on_submit():
        attempted_user = cursor.execute("SELECT * FROM tbluser WHERE username=?",loginform.username.data).fetchone()
        if attempted_user and bcrypt.check_password_hash(attempted_user.password_hash, loginform.password.data):
            if attempted_user.role == 'user':
                session['loggedin'] = True
                session['id'] = attempted_user.id
                session['username'] = attempted_user.username
                session['role'] = attempted_user.role
                available_cart = cursor.execute("SELECT * FROM tblcart WHERE id=?",attempted_user.id).fetchone()
                if not available_cart:
                    cursor.execute("INSERT INTO tblcart(id, cart_date, total_price) VALUES(?,?,?)",attempted_user.id,current_date,0)
                    conn.commit()
                # flash("You are now logged in", category='success')
                return redirect(request.args.get("next") or url_for('home'))
            else:
                flash('Username or Password incorrect!', category='danger')
        else:
            flash('Username or Password incorrect!', category='danger')
    
    if user_login():
        return redirect(url_for('home'))
    else:
        return render_template('login.html', loginform=loginform)

@app.route('/register', methods=['GET','POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        password_hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        mobile_number = "+92"+form.mobile.data
        user_to_create = [form.fname.data, form.lname.data, form.username.data, form.email.data,
                          password_hashed, mobile_number, form.gender.data, current_date, 'user']
        insert_query = """ INSERT INTO tbluser VALUES (?,?,?,?,?,?,?,?,?) """
        cursor.execute(insert_query, user_to_create)
        conn.commit()
        user_to_active = cursor.execute("SELECT * FROM tbluser WHERE username=?",form.username.data).fetchone()
        cursor.execute("INSERT INTO tbluser_details(id) VALUES (?)",user_to_active.id)
        conn.commit()
        session['loggedin'] = True
        session['id'] = user_to_active.id
        session['username'] = user_to_active.username
        session['role'] = user_to_active.role
        cursor.execute("INSERT INTO tblcart(id, cart_date, total_price) VALUES(?,?,?)",user_to_active.id,current_date,0)
        conn.commit()
        # flash("Account Created! You are now logged in", category='success')
        return redirect(url_for('home'))
    
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(err_msg, category='danger')
    
    # rows = cursor.execute("SELECT * FROM tbluser WHERE role='user'").fetchall()
    if user_login():
        return redirect(url_for('home'))
    else:
        return render_template('register.html', form=form)


# can access after logging in
@app.route('/myaccount', methods=['GET','POST'])
def user_settings():
    basic = BasicInfo()
    contact = ContactDetails()
    residance = Residance()
    passwordform = ChangePassword()

    # For basic info form
    if basic.validate_on_submit():
        user_basic_info = [basic.fname.data, basic.lname.data, basic.username.data, session['id']]
        basic_upd_query = """ UPDATE tbluser SET fname=?, lname=?, username=? WHERE id=? """
        cursor.execute(basic_upd_query, user_basic_info)
        conn.commit()
        session['username'] = basic.username.data
        flash('Basic Info Updated Successfully!', category='success')
        return redirect(request.url)

    # For contact form
    if contact.validate_on_submit():
        user_contact = [contact.email.data, "+92"+contact.mobile.data, session['id']]
        contact_upd_query = """ UPDATE tbluser SET email=?, mobile=? WHERE id=? """
        cursor.execute(contact_upd_query, user_contact)
        conn.commit()
        flash('Contact Details Updated Successfully!', category='success')
        return redirect(request.url)

    # For residance form
    if residance.validate_on_submit():
        user_address = [residance.address1.data, residance.address2.data, residance.city.data, residance.district.data, residance.zipcode.data, session['id']]
        residance_upd_query = """ UPDATE tbluser_details SET address1=?, address2=?, city=?, district=?, zipcode=? WHERE id=? """
        cursor.execute(residance_upd_query, user_address)
        conn.commit()
        flash('Account Updated Successfully!', category='success')
        return redirect(request.url)

    # For change password form
    if passwordform.validate_on_submit():
        current_user = cursor.execute("SELECT * FROM tbluser WHERE id=?",session['id']).fetchone()
        if bcrypt.check_password_hash(current_user.password_hash, passwordform.currentpass.data):
            password_hashed = bcrypt.generate_password_hash(passwordform.newpass.data).decode('utf-8')
            pwd_upd_query = """ UPDATE tbluser SET password_hash=? WHERE id=? """
            cursor.execute(pwd_upd_query, password_hashed, session['id'])
            conn.commit()
            flash("Password Updated Successfully!", category='success')
            return redirect(request.url)
        else:
            flash('Please enter correct password', category='danger')

    # Forms Error
    if basic.errors != {} or contact.errors != {} or residance.errors != {} or passwordform.errors != {}:
        not_err = "This field is required."
        for err_msg in basic.errors.values():
            if err_msg[0] != not_err:
                flash(f'Basic Info: {err_msg[0]}', category='danger')
        for err_msg in contact.errors.values():
            if err_msg[0] != not_err:
                flash(f'Contact: {err_msg[0]}', category='danger')
        for err_msg in residance.errors.values():
            if err_msg[0] != not_err:
                flash(f'Residance: {err_msg[0]}', category='danger')
        for err_msg in passwordform.errors.values():
            if err_msg[0] != not_err:
                flash(f'Password: {err_msg[0]}', category='danger')
    
    if user_login():
        user = cursor.execute("SELECT fname,lname,username,mobile,email,created_at FROM tbluser WHERE id=?",session['id']).fetchone()
        address = cursor.execute("SELECT * FROM tbluser_details WHERE id=?",session['id']).fetchone()
        return render_template('user-setting.html', user=user, address=address, residance=residance, basic=basic, contact=contact, passwordform=passwordform)
    else:
        flash('Please login first!', category='warning')
        return redirect(url_for('login_page', next=request.path))

@app.route('/orderdetails', methods=['GET','POST'])
def user_order_details():
    orders = cursor.execute("SELECT * FROM tblorder WHERE id=?",session['id']).fetchall()
    if user_login():
        if session['role'] == 'user':
            return render_template('user-order-details.html', orders=orders)
        else:
            return redirect(url_for('admin_dashboard'))
    else:
        flash('Please login first!', category='warning')
        return redirect(url_for('login_page', next=request.path))

@app.route('/fetchorderdetails', methods=['GET','POST'])
def fetch_order_details():
    if request.method == "POST":
        order_id = request.form['orderid']
        orderdetails = cursor.execute("SELECT * FROM tblorder_details WHERE order_id=?",order_id).fetchall()
        data = ""
        for x in orderdetails:
            data += f"<tr><td>{x.item_name}</td><td>{x.size}</td><td>{x.qty}</td><td>{x.total_amount}</td></tr>"
        return data

    return redirect(url_for('home'))

# logout route
@app.route('/logout')
def logout():
    if user_login():
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        session.pop('role', None)
        # flash('You have been logged out!', category='info')

    return redirect(url_for('home'))

