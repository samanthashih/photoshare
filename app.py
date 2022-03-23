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

from pymysql import NULL

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
	cursor.execute("SELECT password FROM Users WHERE email = '{0}';".format(email))
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
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}';".format(email)):
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
		print(cursor.execute("INSERT INTO Users (first_name, last_name, birth_date, hometown, gender, email, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}');".format(first_name, last_name, birth_date, hometown, gender, email, password)))
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
	cursor.execute("SELECT photo_data, photo_id, caption FROM Photos WHERE user_id = '{0}';".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(photo_data, photo_id, caption), ...]

def tagIDFromTag(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id  FROM Tags WHERE tag_name = '{0}'".format(tag))
	return cursor.fetchone()[0]

def getUsersPhotosByTag(uid, tag):
	cursor = conn.cursor()
	cursor.execute("SELECT Photos.photo_id FROM Photos INNER JOIN Tagged ON Photos.photo_id = Tagged.photo_id WHERE Tagged.tag_id = '{0}' AND Photos.user_id = '{1}'".format(tagIDFromTag(tag), uid))
	return cursor.fetchall() #NOTE list of tuples, [(photo_data, photo_id), ...]

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT photo_data, photo_id, caption FROM Photos")
	return cursor.fetchall() #NOTE return a list of tuples, [(photo_data, photo_id, caption), ...]

def getAllAlbums():
    cursor = conn.cursor()
    cursor.execute("SELECT album_name, albums_id FROM Albums")
    return cursor.fetchall() #NOTE list of tuples, [(photo_data, photo_id), ...]

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
   return cursor.fetchall() #NOTE list of tuples, [(photo_data, photo_id), ...]

#get users tags
def getTags():
   cursor = conn.cursor()
   cursor.execute("SELECT tag_name, tag_id FROM Tags")
   return cursor.fetchall()


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

@app.route('/yourphotos', methods=['GET'])
@flask_login.login_required
def your_photos():
    if request.method == 'GET':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('yourphotos.html', message='Here are your photos', photos=getUsersPhotos(uid),base64=base64)

@app.route('/photosearchbytag', methods=['GET','POST'])
def photosearchbytag():
		if request.method == 'POST':
			tag = request.form.get('photosearchbytag')
			pics = searchPhotosByTag(tag)
			results = []
			for p in pics:
				results.append(p[0])
			return render_template('photosearchbytag.html', message='Photo Search by Tag', photos = getPhotosByIDs(results), base64=base64)
		else:
			return render_template('photosearchbytag.html', message='Photo Search by Tag', photos = [], base64=base64)


def searchPhotosByTag(tag):
	cursor = conn.cursor()
	tag_id = tagIDFromTag(tag)
	cursor.execute("SELECT photo_id FROM Tagged WHERE tag_id={0}".format(tag_id))
	return cursor.fetchall() #NOTE list of tuples, [(photo_data, photo_id), ...]

def getPhotosByIDs(ids):
	cursor = conn.cursor()
	if (ids == []):
		return []
	photos = []
	for i in ids:
		cursor.execute("SELECT photo_data, photo_id, caption FROM Photos WHERE photo_id = {0}".format(i))
		photos += cursor.fetchall()
	return photos

def getPhotosInAlbum(albums_id):
    cursor = conn.cursor()
    cursor.execute("SELECT photo_data, photo_id, caption FROM Photos WHERE Photos.albums_id = {0};".format(albums_id))
    return cursor.fetchall() #NOTE list of tuples, [(photo_data, photo_id), ...]

def getUsersPhotosByTag(uid, tag_name):
	tag_id = tagIDFromTag(tag_name)
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT Photos.photo_id FROM Photos JOIN Tagged ON Photos.photo_id = Tagged.photo_id WHERE Photos.user_id = '{0}' AND Tagged.tag_id = '{1}'".format(uid, tag_id))
	return cursor.fetchall() #NOTE list of tuples, [(photo_data, photo_id), ...]

#get list of friends
def getFriends(uid):
   cursor = conn.cursor()
   sql = "SELECT first_name, last_name, user_id1, user_id2 FROM Friends INNER JOIN Users ON Users.user_id = Friends.user_id2 HAVING user_id1 = {0};".format(uid)
   cursor.execute(sql)
   return cursor.fetchall()

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
		albums_id = request.form.get('albums_id')
		tags = request.form.get('tag_name')
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (photo_data, user_id, caption, albums_id) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, albums_id))
		
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
		cursor.execute("INSERT INTO Albums (album_name, album_date, user_id) VALUES ('{0}', '{1}', '{2}');".format(album_name, album_date, uid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album uploaded!')
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('createAlbum.html')
#end photo uploading code




#view photos and albums
@app.route('/viewphotos', methods=['GET'])
def view_photos():
    if request.method == 'GET':
        return render_template('hello.html', message='Here are all the photos', photos=getAllPhotos(),base64=base64)

@app.route('/viewalbums', methods=['GET'])
def view_albums():
    if request.method == 'GET':
        return render_template('hello.html', message='Here are all the albums', albums=getAllAlbums(), base64=base64)

@app.route('/youralbums', methods=['GET'])
@flask_login.login_required
def your_albums():
    if request.method == 'GET':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('youralbums.html', message='Here are your albums', albums=getUsersAlbums(uid), base64=base64)

@app.route('/viewalbumphotos', methods=['GET'])
def view_album_photos():
    if request.method == 'GET':
        albums_id = request.args.get('albums_id')
        return render_template('hello.html', message='Here are all the photos in album', photos=getPhotosInAlbum(albums_id), base64=base64)

@app.route('/yourphotosbytag', methods=['GET','POST'])
@flask_login.login_required
def yourphotosbytag():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		tag = request.form.get('yourphotosbytag')
		pics = getUsersPhotosByTag(uid, tag)
		results = []
		for p in pics:
			results.append(p[0])
		return render_template('yourphotosbytag.html', message='Your Photos Search by Tag', photos = getPhotosByIDs(results), base64=base64)
	else:
		return render_template('yourphotosbytag.html', message='Your Photos Search by Tag', photos = [], base64=base64)


@app.route('/friends', methods=['GET','POST'])
@flask_login.login_required
def friends():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('friends.html', message='Friends!', listfriends=getFriends(uid), base64=base64)


#comment stuff
#add comment to photo, has to be a registered user
def addComment(photo_id, uid, comment):
  cursor = conn.cursor()
  today = date.today()
  comment_date = today.strftime("%Y-%m-%d")
  cursor.execute('''INSERT INTO Comments (user_id, photo_id, comment_text, comment_date) VALUES (%s, %s, %s, %s )''', (uid, photo_id, comment, comment_date))
  conn.commit()


#get all comments for a photo
def getComments(photo_id):
   cursor = conn.cursor()
   cursor.execute("SELECT * FROM Comments WHERE photo_id = {0}".format(photo_id))
   return cursor.fetchall()

def findPhotoOwner(photo_id):
   cursor = conn.cursor()
   cursor.execute( "SELECT user_id FROM Photos WHERE photo_id = {0}".format(photo_id))
   return cursor.fetchone()[0]



@app.route('/comments', methods=['GET','POST'])
def comments():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		comment = request.form.get('comment')
		photo_id = request.form.get('photo_id')
		addComment(photo_id, uid, comment)
		return render_template('comments.html', message='Comments', allowed = True, photo=getPhotosByIDs(photo_id)[0], comments = getComments(photo_id))
	else:
		photo_id = request.args.get('photo_id')
		uid = getUserIdFromEmail(flask_login.current_user.id)
		currentUser = findPhotoOwner(photo_id)
		if uid == currentUser:
			return render_template('comments.html', message='Comments', allowed = False, photo=getPhotosByIDs(photo_id)[0], comments = getComments(photo_id))
		else:
			return render_template('comments.html', message='Comments', allowed = True, photo=getPhotosByIDs(photo_id)[0], comments = getComments(photo_id))
  

# recommendation
def getUsersFiveTags(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id, tag_id, COUNT(*) FROM Tagged JOIN Photos on Tagged.photo_id = Photos.photo_id WHERE user_id = {0} GROUP BY tag_id ORDER BY COUNT(*) DESC LIMIT 5".format(uid))
	return cursor.fetchall()

def getPhotoIDsRecs(tags):
	allTags = ""
	for t in tags:
		allTags += "'" + str(t) + "',"
	allTags = allTags[:-1] #consider tags from most common to least common
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM (SELECT photo_id, Count(photo_id) AS Countphoto_id1 From Tagged GROUP BY photo_id) AS Table1 INNER JOIN  (SELECT T2.photo_id, COUNT(*) as Countphoto_id2  FROM Tagged T2 WHERE T2.tag_id IN ({0}) GROUP BY T2.photo_id ORDER BY COUNT(T2.photo_id) DESC) AS Table2 ON Table1.photo_id = Table2.photo_id GROUP BY Table1.photo_id ORDER BY Countphoto_id2 DESC, Countphoto_id1 ASC".format(allTags))
	return cursor.fetchall()


@app.route('/photorec', methods=['GET'])
@flask_login.login_required
def photorec():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		tags = getUsersFiveTags(uid)
		res = []
		for i in tags:
			res.append(i[1])

		if res != []:
			pids = getPhotoIDsRecs(res)
			res2 = []
			for i in pids:
				res2.append(i[0])
			
			return render_template('photorec.html', message='You May Also Like Dashboard', photos = getPhotosByIDs(res2),  base64=base64)	
		else:
			return render_template('photorec.html', message='You May Also Like Dashboard', photos = [],  base64=base64)	


def getTopUserTagID(uid):
	cursor = conn.cursor()
	sql = "SELECT Tagged.tag_id FROM Photos JOIN Tagged WHERE Photos.user_id = {0} GROUP BY Tagged.tag_id ORDER BY COUNT(*) DESC LIMIT 1".format(uid)
	cursor.execute(sql)
	return cursor.fetchall()

#insert like
def addLike(uid, photo_id):
   cursor = conn.cursor()
   cursor.execute("INSERT INTO Likes VALUES ({0},{1})".format(photo_id, uid))
   conn.commit()
 
#see all likes on a photo
def allLikes(photo_id):
   cursor = conn.cursor()
   sql = "SELECT first_name, last_name, email, photo_id FROM Likes INNER JOIN Users ON Users.user_id = Likes.user_id HAVING photo_id = {0};".format(photo_id)
   cursor.execute(sql)
   return cursor.fetchall()
 
def totalLikes(photo_id):
   cursor = conn.cursor()
   cursor.execute("SELECT COUNT(*) FROM Likes WHERE photo_id = {0};".format(photo_id))
   return cursor.fetchone()[0]
 
@app.route('/like', methods=['GET'])
@flask_login.login_required
def likeAction():
   if request.method == 'GET':
       uid = getUserIdFromEmail(flask_login.current_user.id)
       photo_id = request.args.get('photo_id')
       addLike(uid,photo_id)
       return render_template('hello.html', name=flask_login.current_user.id, message='All Photos By Tag', photos=getUsersPhotos(uid),base64=base64)
 
 
@app.route('/seelikes', methods=['GET'])
@flask_login.login_required
def seelikes():
   if request.method == 'GET':
       photo_id = request.args.get('photo_id')
       return render_template('seelikes.html', name=flask_login.current_user.id, message='Here are the likes you got:', photo_id = photo_id, photo=getPhotosByIDs(photo_id), likes = allLikes(photo_id), count = totalLikes(photo_id), base64=base64)

@app.route('/useractivity', methods=['GET'])
@flask_login.login_required
def useractivity():
   cursor = conn.cursor()
   cursor.execute("SELECT Users.email, COUNT(Comments.photo_id) + COUNT(Comments.comment_id) FROM Users LEFT OUTER JOIN Comments ON Users.user_id = Comments.user_id LEFT OUTER JOIN Photos ON Users.user_id = Photos.user_id GROUP BY Users.user_id HAVING COUNT(comment_id) + COUNT(Comments.photo_id) ORDER BY COUNT(comment_id) + COUNT(Comments.photo_id) DESC LIMIT 10;")
   stat = cursor.fetchall()
   return render_template('useractivity.html', message='Here are the top 10 users', stat=stat)

@app.route('/searchComments', methods=['POST', 'GET'])
def searchComments():
	if request.method == 'POST':
		cursor = conn.cursor()
		comment = request.form.get('comment')
		cursor.execute("Select COUNT(Comments.comment_id), Users.email FROM Comments INNER JOIN Users WHERE Comments.comment_text = '{0}' and Comments.user_id = Users.user_id GROUP BY Comments.comment_text, Users.email ORDER BY Count(Comments.comment_id) DESC LIMIT 10;".format(comment))
		results = cursor.fetchall()
		return render_template('searchComments.html', message='Here are the results!', results = results)
	else:
		return render_template('searchComments.html')



@app.route('/friendrec', methods=['GET'])
@flask_login.login_required
def friendrec():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("SELECT Users.email, f2.user_id2 FROM Friends f1 JOIN Friends f2 ON f2.user_id1 = f1.user_id2 and f2.user_id2 <> f1.user_id1 JOIN Users on f2.user_id2 = Users.user_id WHERE f1.user_id1 = {0} AND f2.user_id2 NOT IN (SELECT f3.user_id2 from Friends f3 where f3.user_id1 = {1}) GROUP BY f2.user_id2 ORDER BY COUNT(*) DESC LIMIT 1;".format(uid, uid))
		rec = cursor.fetchall()
		if len(rec) == 0:
			rec = []
		return render_template('friendrec.html', message='Recommended friends', friends=rec, base64=base64)


@app.route('/deletephoto', methods=['POST', 'GET'])
@flask_login.login_required
def deletePhoto():
   if request.method == 'GET':
       photo_id = request.args.get('photo_id')
       cursor = conn.cursor()
       cursor.execute("DELETE FROM Tagged WHERE Tagged.photo_id = {0}".format(photo_id))
       cursor.execute("DELETE FROM Photos WHERE Photos.photo_id = {0}".format(photo_id))
       conn.commit()
       return render_template('yourphotos.html', name=flask_login.current_user.id, message='Your Photo Has Been Deleted')
   else:
       return render_template('hello.html')
  
@app.route('/deletealbum', methods=['POST', 'GET'])
@flask_login.login_required
def deleteAlbum():
	if request.method == 'GET':
		albums_id = request.args.get('albums_id')
		photos_todel = getPhotosInAlbum(albums_id)
		cursor = conn.cursor()
		for p in photos_todel:
			photo_id = p[1]
			cursor.execute("DELETE FROM Tagged WHERE photo_id = {0}".format(photo_id))
			cursor.execute("DELETE FROM Photos WHERE photo_id = {0}".format(photo_id))
		cursor.execute("DELETE FROM Albums WHERE Albums.albums_id = {0}".format(albums_id))
		conn.commit()
		return render_template('youralbums.html', name=flask_login.current_user.id, message='Your Album Has Been Deleted')
	else:
		return render_template('hello.html')
 
  
def getTags():
   cursor = conn.cursor()
   sql = "SELECT Tags.tag_name FROM Tags GROUP BY Tags.tag_name ORDER BY COUNT(*) DESC LIMIT 5"
   cursor.execute(sql)
   return cursor.fetchall()

@app.route('/viewPopularTags', methods=['GET'])
def viewPopularTag():
   if request.method == 'GET':
       tags = getTags()
       return render_template('toptags.html', tags=tags)

 



#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
