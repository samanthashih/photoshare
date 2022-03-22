######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

from getpass import getuser
import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64
#for album
from datetime import date

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'photoshareFinalFinal'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		first_name=request.form.get('first_name')
		last_name=request.form.get('last_name')
		last_name=request.form.get('last_name')
		birth_date=request.form.get('birth_date')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
		email=request.form.get('email')
		password=request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (first_name, last_name, birth_date, hometown, gender, email, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(first_name, last_name, birth_date, hometown, gender, email, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, photo_id, caption FROM Photos")
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]


def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

#get users albums
def getUsersAlbums(uid):
   cursor = conn.cursor()
   cursor.execute("SELECT album_name, albums_id FROM Albums WHERE Albums.user_id = '{0}'".format(uid))
   return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

@app.route('/profile')
@flask_login.login_required
def protected1():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")


def getUser(uid):
   cursor = conn.cursor()
   sql = "SELECT * FROM Users WHERE user_id = {0}".format(uid)
   cursor.execute(sql)
   return cursor.fetchall()

@app.route('/profile_info')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('profile.html', name=flask_login.current_user.id, getUser = getUser(uid), message="Here's your profile")


#comment stuff
#add comment to photo, has to be a registered user
def addComment(pid, uid, comment):
   cursor = conn.cursor()
   date = date.today()
   sql = "INSERT INTO Comments(user_id, photo_id, comment_text, comment_date) VALUES ('{0}', '{1}', '{2}', '{3}')".format(uid, pid, comment, date)
   print(sql)
   cursor.execute(sql)
   conn.commit()
 
#add comment to photo, anonymous user
def addAnonComment(pid, comment):
   cursor = conn.cursor()
   date = date.today()
   sql = "INSERT INTO Comments(photo_id, comment_text, comment_date) VALUES ('{0}', '{1}', '{2}')".format(pid, comment, date)
   print(sql)
   cursor.execute(sql)
   conn.commit()

#get all comments for a photo
def getComments(pid):
	cursor = conn.cursor()
	sql = "SELECT * FROM (SELECT * FROM Comments Where pid = {0}) as A INNER JOIN Users X ON X.user_id = Y.user_id".format(pid)
	cursor.execute(sql)
	return cursor.fetchall()

def getAnonComments(pid): 
	cursor = conn.cursor() 
	cursor.execute("SELECT * FROM Comments WHERE photo_id = {0} AND user_id IS NULL".format(pid))
	return cursor.fetchall()

def getPhotoById(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, photo_id, caption FROM Photos WHERE photo_id = '{0}".format(pid))
	return cursor.fetchall()[0]

def findPhotoOwner(pid):
	cursor = conn.cursor()
	cursor.execute(	"SELECT user_id FROM Photos WHERE photo_id = {0}".format(pid))
	return cursor.fetchone()[0]
 
@app.route('/comment', methods=['GET','POST'])
@flask_login.login_required
def comment():
	if (flask_login.current_user.is_anonymous): 
		if request.method == 'POST': 
			pid = request.form.get('pid')
			comment = request.form.get('comment')
			addAnonComment(pid, comment)
			return render_template('comments.html', message='Comments', allowed = True, photo=getPhotoById(pid), comments = getComments(pid), acomments = getAnonComments(pid), base64 = base64)

		else: 
			pid = request.args.get('pid')
			return render_template('comments.html', message='Comments', allowed = True, photo=getPhotoById(pid), comments = getComments(pid), acomments = getAnonComments(pid), base64=base64)

	else:
		if request.method == 'POST':
			uid = getUserIdFromEmail(flask_login.current_user.id)
			comment = request.form.get('comment')
			pid = request.form.get('pid')
			addComment(pid, uid, comment)
			#return flask.redirect(flask.url_for('hello'))
			return render_template('comments.html', message='Comments', allowed = True, photo=getPhotoById(pid), comments = getComments(pid), acomments = getAnonComments(pid), base64=base64)
		
		else:
			pid = request.args.get('pid')
			uid = getUserIdFromEmail(flask_login.current_user.id)
			currentUser = findPhotoOwner(pid)
			if uid == currentUser:
				return render_template('comments.html', message='Comments', allowed = False, photo=getPhotoById(pid), comments = getComments(pid), anonComments = getAnonComments(pid), base64=base64)

			else:
				return render_template('comments.html', message='Comments', allowed = True, photo=getPhotoById(pid), comments = getComments(pid), anonComments = getAnonComments(pid), base64=base64)
	
		


#friend stuff
#get list of friends
def getFriends(uid):
	cursor = conn.cursor()
	sql = "SELECT first_name, last_name, user_id1, user_id2 FROM Friends INNER JOIN Users ON Users.user_id = Friends.userID2 HAVING userID1 = {0}".format(uid)
	cursor.execute(sql)
	return cursor.fetchall()
 
#find friend by email
def findPersonByEmail(email):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	sql = "SELECT first_name, last_name, email FROM Users WHERE email = '{0}' AND user_id NOT IN (SELECT Friends.user_id2 FROM Friends WHERE Friends.user_id1 = {1}) HAVING user_id <> {2}".format(email, uid, uid)
	cursor.execute(sql)
	return cursor.fetchall()
 
def addFriend(uid1, uid2):
   cursor = conn.cursor()
   sql = "INSERT INTO Friends VALUES ({0}, {1}), ({2}, {3});".format(uid1, uid2, uid2, uid1)
   cursor.execute(sql)
   conn.commit()


@app.route('/addfriends', methods=['GET', 'POST'])
@flask_login.login_required
def add_friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)

	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		friend_email = request.form.get('friend_email')
		friend_uid = getUserIdFromEmail(friend_email)
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Friends VALUES ({0}, {1}), ({2}, {3});".format(uid, friend_uid, friend_uid, uid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Friend added!', base64=base64)
	#The method is GET so we return a  HTML form to add the friend.
	else:
		return render_template('addfriends.html')


# @app.route('/addfriends', methods=['POST'])
# @flask_login.login_required
# def addFriends():
#    friend_email = request.form.get('email')
#    return render_template('addfriends.html',stranger = findPersonByEmail(friend_email),  message = 'add friend')
 
# @app.route('/makefriend', method = ['GET'])
# @flask_login.login_required
# def makeFriend():
#    uid1 = getUserIdFromEmail(flask_login.current_user.id)
#    uid2 = request.args.get('userID')
#    addFriend(uid1, uid2)
#    return flask.redirect(flask.url_for('/addfriends'))



#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	users_albums = getUsersAlbums(uid)
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		album_id = request.form.get('album_id')
		tags = request.form.get('tag_name')
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (photo_data, user_id, caption, albums_id) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, album_id))
		
		if len(tags)>0:
			cursor_tags = conn.cursor()
			cursor_tags.execute("SELECT photo_id FROM Photos WHERE photo_id = (SELECT LAST_INSERT_ID())")
			photo_id = cursor_tags.fetchone()[0]            
            
			tag_list = tags.split(',')
			for tag in tag_list:
				try:
					cursor_tags.execute('''SELECT tag_id FROM Tags WHERE tag_name = tag''', (tag))
					tag_id = cursor_tags.fetchone()[0] 
					cursor_tags.execute('''INSERT INTO Tagged (photo_id, tag_id) VALUES (%s, %s)''' ,(photo_id, tag_id))
				except:
                    #new tag
					cursor_tags.execute('''INSERT INTO Tags (tag_name) VALUES (%s)''' ,(tag))
					cursor_tags.execute("SELECT tag_id FROM Tags WHERE tag_id = (SELECT LAST_INSERT_ID())")
					new_tag_id = cursor_tags.fetchone()[0]            
					cursor_tags.execute('''INSERT INTO Tagged (photo_id, tag_id) VALUES (%s, %s)''' ,(photo_id, new_tag_id))
					
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html', albums=users_albums)
#end photo uploading code

#create album code
@app.route('/createAlbum', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_name = request.form.get('album_name')
		today = date.today()
		album_date = today.strftime("%Y-%m-%d")
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Albums (album_name, album_date, user_id) VALUES ('{0}', '{1}', '{2}')".format(album_name, album_date, uid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album uploaded!')
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('createAlbum.html')
#end photo uploading code



#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
