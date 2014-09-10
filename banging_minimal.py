
# Minimal flask-security demo app!
#import os, re, uuid, traceback, sys, time, csv, socket, itertools

import os, sys, shutil

from   flask import Flask, request, Response, session, g, redirect, url_for, abort, send_file 
from   flask import render_template, render_template_string, flash, send_from_directory, json, jsonify              # note use of flask's json
from   flask import make_response

from   flask.ext.mail import Mail, Message
from   flask.ext.sqlalchemy import SQLAlchemy
from   flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, roles_accepted
import jinja2

import paste

# --- Flask App ---

app = Flask(__name__)

app.config.update(
    DEBUG = True,

    SECRET_KEY      = os.urandom(16),          
    SQLALCHEMY_DATABASE_URI = 'sqlite:///./users.db',

    MAIL_SERVER     = 'smtp.gmail.com',
    MAIL_PORT       = 465,
    MAIL_USE_SSL    = True,
    MAIL_USERNAME   = 'accounts@pwnoddy.com',
    MAIL_PASSWORD   = 'AIo3ENJ53B5DXm9jnTm2',
    
    SECURITY_PASSWORD_HASH  = 'bcrypt',
    SECURITY_PASSWORD_SALT  = 'rock or table, ROCK OR TABLE!!!??',

    SECURITY_REGISTERABLE   = True,             # They all default to off, including PASSWORDLESS, thankfully  
    SECURITY_CONFIRMABLE    = False,            # dont bother with confirm workflow. 
    SECURITY_CHANGEABLE     = True,
    SECURITY_RECOVERABLE    = True,             # this is the kicker, you always end up needing this :/

    #SECURITY_LOGIN_USER_TEMPLATE       = 'security/others.html',       # Login form IS actually a custom template.
    #SECURITY_RESET_PASSWORD_TEMPLATE   = 'security/others.html',       # SIGH, >< url_for_security with the token, breaks generic processing.
    SECURITY_REGISTER_USER_TEMPLATE     = 'security/others.html',       # Non-login form can be generic.
    SECURITY_CHANGE_PASSWORD_TEMPLATE   = 'security/others.html',
    SECURITY_FORGOT_PASSWORD_TEMPLATE   = 'security/others.html',   
    SECURITY_SEND_CONFIRMATION_TEMPLATE = 'security/others.html',
    SECURITY_SEND_LOGIN_TEMPLATE        = 'security/others.html',

)

app.url_map.strict_slashes = False              # (DONT) care about trailing slashes

# --- Templating Hacks ---

@jinja2.contextfunction
def TheForm(c):                                 # flask-sec has different names for all its forms.
    for k,v in c.items():                       # If we want to use one generic template for different forms, we need to get
        if k.endswith('_form'):                 # and re-supply the form in a non-explicitely-named way, hence this function.
            return v
    return None
app.jinja_env.globals['TheForm'] = TheForm
app.jinja_env.globals['unicode'] = unicode

# --- User DB ---

sdb = SQLAlchemy(app)

roles_users = sdb.Table('roles_users',
        sdb.Column('user_id', sdb.Integer(), sdb.ForeignKey('user.id')),
        sdb.Column('role_id', sdb.Integer(), sdb.ForeignKey('role.id')))

class Role(sdb.Model, RoleMixin):
    id = sdb.Column(sdb.Integer(), primary_key=True)
    name = sdb.Column(sdb.String(80), unique=True)
    description = sdb.Column(sdb.String(255))

class User(sdb.Model, UserMixin):
    id = sdb.Column(sdb.Integer, primary_key=True)
    email = sdb.Column(sdb.String(255), unique=True)
    password = sdb.Column(sdb.String(255))
    active = sdb.Column(sdb.Boolean())
    confirmed_at = sdb.Column(sdb.DateTime())
    roles = sdb.relationship('Role', secondary=roles_users, backref=sdb.backref('users', lazy='dynamic'))

# --- Flask-security ---

user_datastore  = SQLAlchemyUserDatastore(sdb, User, Role)
security        = Security(app, user_datastore)
mail            = Mail(app)

# --- DB connections, etc ---

@app.before_request
def before_request():
    g.db = None # an sqlite connection or something

@app.teardown_request
def teardown_request(exc):
    if hasattr(g, 'db') and g.db:        
        del(g.db)  


# =========================== APP =============================================

# Root-static small files 
@app.route('/robots.txt')
@app.route('/sitemap.xml')
@app.route('/favicon.ico')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

###############################################################################
#  SECURITY PROTECTION GOES HERE                                              #
###############################################################################
@app.route('/edit', methods=['GET','POST'])
#@roles_accepted('editor')
def Edit():
    if request.method == 'POST':
        with open('pagecontent_dynamic.html','wt') as f:
            f.write(request.form['src'])
        return redirect(url_for('Root'))
    else:
        return render_template('edit.html', pagecontent=open('pagecontent_dynamic.html','r').read())

@app.route('/')
def Root():
    return render_template('root.html', pagecontent=open('pagecontent_dynamic.html','r').read())

# =========================== APP =============================================

# --- Command Line Stuff ---

def ArgEquals(argv, name):
    name = name.lower()
    for a in argv:
        if a.lower().startswith(name):   return a.split('=',1)[1]
    return ''

def AddRoleToUser(args):
    user = ArgEquals(args, 'user')
    role = ArgEquals(args, 'role')
    if user and role:
        user_datastore.add_role_to_user(user, role)         # accepts these parms as strings, and does the finding. Handy.
        user_datastore.commit()
    else:
        print 'Fail with user or role parameters.'

def CreateRole(args):
    roleName = ArgEquals(args, 'name')
    roleDesc = ArgEquals(args, 'desc')
 
    if roleName and roleDesc:
        user_datastore.create_role(name=roleName, description=roleDesc)
        user_datastore.commit()
    else:
        print 'Fail with role or desc parameters'

def MakeDB():
    print 'Doing db create_all...'
    sdb.create_all()
    shutil.copyfile('pagecontent_pure.html','pagecontent_dynamic.html')
    print '...Done'


if __name__ == '__main__':

    largs = [arg.lower() for arg in sys.argv]

    if 'addrole' in largs:
        AddRoleToUser(sys.argv)
    elif 'createrole' in largs:
        CreateRole(sys.argv)
    elif 'makedb' in largs:
        MakeDB()
    else:
        print 'Flask sec test starting...'
        
        # SELECT FROM ALTERNATIVES: 

        # (1) Flask builtin dev server with auto-reload (1)
        app.run(host='0.0.0.0', port=8005) #, use_evalex=False)      # debug=code reloader, apparently

        # (2) Paste httpserver for a better builtin 'production' experience 
        # Also so we can test the SecurityMiddleware
        #import paste.httpserver
        #import paste.translogger
        #paste.httpserver.serve( paste.translogger.TransLogger(app.wsgi_app),  host='0.0.0.0', port=8005, use_threadpool=True, threadpool_workers=1, threadpool_options={'spawn_if_under':0})

        # also Also  http://i.imgflip.com/4mz6i.jpg  "other people's C# code"
