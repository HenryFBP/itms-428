import os
import sys
import mysql_helper

from flaskext.mysql import MySQL

import forms
from mysql_helper import login_valid, user_exists, update_login_time_to_now, dump_table_to_dict, get_user_last_logged_in
from setup import ALL_TABLES
from shared_lib import get_login_creds
from user import ALL_USERS

sys.path.append('..')  # Allows us to import stuff in above folder.

from data.mysql_sample_db import UsersDatabase, OrderDetailsData, FarmerDatabase, Config

from flask import render_template, flash, redirect, url_for, Flask

username, password = get_login_creds(os.path.join('..', Config.LOGIN_FILE_NAME))

app = Flask(__name__)

mysql = MySQL()

app.config['SECRET_KEY'] = 'itsasecret'

app.config['MYSQL_DATABASE_HOST'] = Config.SERVER_IP
app.config['MYSQL_DATABASE_USER'] = username
app.config['MYSQL_DATABASE_PASSWORD'] = password
app.config['MYSQL_DATABASE_DB'] = Config.DATABASE_NAME

mysql.init_app(app)

connection = mysql.connect()

superadmin = ['henry', 'shephalika', 'reshma']
dataadmin = ['sunil', 'cody', 'dennis', 'sridhar']

sysusenotification = """******** This system is for the use of authorized users only.
Individuals using this computer system without
authority, or in excess of their authority, are subject
to having all of their activities on this system
monitored and recorded by system personnel. In the
course of monitoring individuals improperly using this
system, or in the course of system maintenance, the
activities of authorized users may also be monitored. 
Anyone using this system expressly consents to such
monitoring and is advised that if such monitoring
reveals possible evidence of criminal activity, system
personnel may provide the evidence of such monitoring
to law enforcement officials. **********"""


@app.route("/")
def main():
    return render_template('index.html',
                           users=len(ALL_USERS), tables=len(ALL_TABLES), dbname=Config.DATABASE_NAME)


@app.route("/data")
def data():
    return render_template('data.html', data={  # This odd-looking stuff just merges dictionaries.
        **dump_table_to_dict(OrderDetailsData.table_name, connection, limit=20),
        **dump_table_to_dict(FarmerDatabase.table_name, connection, limit=10)
    })


@app.route('/admin')
def admin():
    return render_template('data.html', data=dump_table_to_dict(UsersDatabase.table_name, connection))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()

    if form.validate_on_submit():
        # there is no use to display below info
        # flash('Login requested for user {}, remember_me={}'.format(
        # form.username.data, form.remember_me.data))

        if login_valid(username=form.username.data, password=form.password.data, connection=connection):
            flash(
                "Welcome, {}! Current date and time is {}".format(form.username.data, mysql_helper.display_datetime()))

            flash(f"Last logged in on {get_user_last_logged_in(form.username.data, connection)}.")

            update_login_time_to_now(form.username.data, connection)
            # superadmin

            user = form.username.data

            if user in superadmin: # TODO remove hard-coded list and use MySQL queries
                flash("You have full access to database."
                      "Please be cautious while performing any actions")
                flash(sysusenotification)
            elif user in dataadmin:
                flash("You have all privileges to "
                      "database except delete commands")
                flash(sysusenotification)
            else:
                flash("Ha! You have no power here!")
                flash(sysusenotification)

        return redirect(url_for('main'))

    return render_template('login.html', title="Sign in", form=form)


if __name__ == '__main__':
    app.run()

    # Sanity checks.
    assert (login_valid("henry", "iliketofarm", connection))
    assert (not login_valid("henry", "notafarmer", connection))

    assert (user_exists("henry", connection))
    assert (not user_exists("tiffany_the_lord_of_squids", connection))
