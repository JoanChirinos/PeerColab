"""
PeerColab

Base python file for PeerColab Flask App

Copyright Joan Chirinos, 2021.
"""

import sys
import os
# import datetime

from flask import (Flask, render_template, redirect, url_for, session, request,
                   flash, current_app)
from markupsafe import Markup

from util import db, helpers
import config

app = Flask(__name__)

# Production Config
# app.config.from_object(config.ProdConfig)

# Development Config
app.config.from_object(config.DevConfig)

# Database Manager with correct databse path and table defns path
with app.app_context():
    cwd = os.getcwd()
    dbm = db.DBManager(current_app.config['DATABASE_URI'],
                       f'{cwd}/static/table_definitions.sql')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    '''
    Catch-all route in case some typo happens or something
    '''
    flash(f'Invalid endpoint: /{path}', 'warning')
    return redirect(url_for('home'))


@app.route('/')
def home():
    '''
    Render the homepage.

    If user is logged in, redirect to their files.
    '''
    if 'email' in session:
        return redirect(url_for('projects'))
    return render_template('index.html')


@app.route('/login')
def login_page():
    '''
    Render the login page.

    If user is logged in, redirect to their files.
    '''
    if 'email' in session:
        return redirect(url_for('projects'))
    return render_template('login.html')


@app.route('/register')
def register_page():
    '''
    Render the registration page.

    If user is logged in, redirect to their files.
    '''
    if 'email' in session:
        return redirect(url_for('projects'))
    return render_template('register.html')


@app.route('/projects')
def projects():
    '''
    Render main projects page.
    '''
    if 'email' not in session:
        flash('You must be logged in to view that page!', 'danger')
        return redirect(url_for('home'))
    else:
        email = session['email']
        ids = dbm.get_projects(email)
        projects = list((dbm.get_project_name(id)[1],
                         id,
                         dbm.is_admin(email, id)) for id in ids)
        projects = tuple(sorted(projects))
        return render_template('projects.html', projects=projects)


@app.route('/project/<project_id>')
def project(project_id):
    '''
    Render page for project with given id
    '''
    if 'email' not in session:
        flash('You must be logged in to view that page!', 'danger')
        return redirect(url_for('home'))
    else:
        email = session['email']
        if not dbm.is_member(email, project_id):
            flash('You don\'t have permission to do that!', 'warning')
            return redirect(url_for(projects))

        project_name = dbm.get_project_name(project_id)
        #files =

        return render_template('project.html', **locals())


@app.route('/authenticate', methods=['POST'])
def authenticate():
    '''
    Attempt to log user in.

    On failure, flashes error and redirects home.
    On success, stores email in session and redirects to project page.
    '''
    email = request.form['email'].strip()
    password = request.form['password'].strip()

    if helpers.verify_auth_args(email, password)\
       and dbm.authenticate_user(email, password):
        session['email'] = email
        return redirect(url_for('projects'))
    else:
        flash('Incorrect username or password!', 'danger')
        return redirect(url_for('login_page'))


@app.route('/registerUser', methods=['POST'])
def register():
    '''
    Attempt to register user.

    On failure, flashes error and redirects home.
    On success, stores email in session and redirects to project page.
    '''
    first = request.form['first'].strip()
    last = request.form['last'].strip()
    email = request.form['email'].strip()
    password = request.form['password'].strip()

    if not helpers.verify_auth_args(first, last, email, password):
        flash('One or more fields is improperly formatted!', 'danger')
        return redirect(url_for('register_page'))
    elif not dbm.register_user(email, password, first, last, 0):
        s = ('Email already in use! <a href="/login" class="alert-link">'
             + 'Log in?</a>')
        flash(Markup(s), 'danger')
        return redirect(url_for('register_page'))
    else:
        session['email'] = email
        flash('Account creastion successful!', 'success')
        return redirect(url_for('projects'))


@app.route('/logout')
def logout():
    '''
    Attempt to log user out.

    Regardless, will redirect to home page.
    '''
    if 'email' in session:
        session.pop('email')
    return redirect(url_for('home'))


@app.route('/create/project', methods=['POST'])
def create_project():
    '''
    Attempt to create project.

    Redirects to projects page.
    '''
    if 'email' not in session:
        flash('You need to be logged in to do that!', 'warning')
        return redirect(url_for('home'))
    email = session['email']
    teacher = request.form['teacherEmail']
    name = request.form['projectName']
    forclass = 'forClass' in request.form

    if forclass:
        if not dbm.is_teacher(teacher):
            flash('Teacher\'s email is invalid!', 'danger')
            return redirect(url_for('projects'))
        project_id = dbm.create_project(teacher, name)
        dbm.add_member(email, project_id)
    else:
        dbm.create_project(email, name)

    flash('Successfully created new project!', 'success')
    return redirect(url_for('projects'))


@app.route('/create/file/<project_id>', methods=['POST'])
def create_file(project_id: str):
    '''
    Attempt to create file.

    Redirects to project page.
    '''
    if 'email' not in session:
        flash('You need to be logged in to do that!', 'warning')
        return redirect(url_for('home'))
    email = session['email']

    name = request.form['fileName']

    dbm.create_file(email, project_id, name)

    flash('Successfully created new file!', 'success')
    return redirect(url_for('projects'))


@app.route('/delete/<type>/<id>')
def delete(type: str, id: str):
    '''
    Attempt to delete project with given project_id.

    Redirects to project page.
    '''
    if 'email' not in session:
        flash('You need to be logged in to do that!', 'warning')
        return redirect(url_for('home'))
    email = session['email']
    result, error_msg = None, None

    if type == 'project':
        result, error_msg = dbm.delete_project(email, id)
    if type == 'file':
        result, error_msg = dbm.delete_file(email, id)

    if result is None:
        flash('Invalid request!', 'warning')
    elif not result:
        flash(error_msg, 'warning')
    else:
        flash('Project deleted successfully!', 'success')

    if type == 'project':
        return redirect(url_for('projects'))
    elif type == 'file':
        return redirect(url_for('project', project_id=id))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        app.run()
    else:
        if sys.argv[1] == 'create_db':
            dbm.create_db()
        elif sys.argv[1] == 'test_suite':
            dbm.create_db()
            dbm.register_user('jchirinos3201@gmail.com', 'password', 'Joan',
                              'Chirinos', 0)
            dbm.register_user('user@gmail.com', 'password', 'User', 'Userface',
                              0)
            dbm.register_user('teacher@gmail.com', 'password', 'Teach', 'Er',
                              1)
            dbm.create_project('jchirinos3201@gmail.com', 'pname')
            dbm.create_project('jchirinos3201@gmail.com', 'swag name')

            # Simulate creating a project that has a teacher
            tpid = dbm.create_project('teacher@gmail.com', 'Teacher project')
            dbm.add_member('jchirinos3201@gmail.com', tpid)
