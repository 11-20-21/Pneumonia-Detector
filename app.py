from flask import Flask,redirect,url_for,render_template,request,send_from_directory,session,flash,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import pdfkit
import os
import json
import tensorflow as tf
import cv2
from werkzeug.utils import secure_filename

config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

with open('config.json','r') as c:
    params = json.load(c) ["params"]

app = Flask(__name__, template_folder='templates', static_folder='static')

local_server = True
app = Flask(__name__)
app.secret_key = "login"
mail=Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = params['gmail-user']
app.config['MAIL_PASSWORD'] = params['gmail-password']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
app.config['UPLOAD_FOLDER'] = 'C:/Users/PRATHMESH WADIYA/OneDrive/Desktop/Flask/pimages'
db = SQLAlchemy(app)

class Login(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rid = db.Column(db.Integer)
    username = db.Column(db.String(30))
    password = db.Column(db.String(30))
    
    
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    username = db.Column(db.String(15))
    password = db.Column(db.String(15))
    email = db.Column(db.String(30))
    phone = db.Column(db.String(12))
    gender = db.Column(db.String(10))
    address = db.Column(db.String(100))
    
    
class Pdetection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(4))
    email = db.Column(db.String(30))
    phone = db.Column(db.String(12))
    xray_image = db.Column(db.String(255))
    result = db.Column(db.String(10))

    
@app.route("/")
def home():
    return render_template('index.html')

@app.route("/about")
def about_page():
    return render_template('About.html')

@app.route("/about_welcome")
def aboutwelcome_page():
    return render_template('About_welcome.html')

@app.route("/login")
def login_page():
    return render_template('Login.html')

@app.route("/register")
def register_page():
    return render_template('Registration.html')

@app.route("/pdetection")
def pdetection_page():
    return render_template('Pneumonia_Detection.html')

@app.route("/welcome")
def welcome_page():
    return render_template('Welcome.html')

@app.route("/history")
def history_page():
    return render_template('History.html')

@app.route("/lsubmit", methods=["GET", "POST"])
def login_submit():
    if request.method == "POST":
        uname = request.form.get('uname')
        upassword = request.form.get('upassword')
        login_credential = Registration.query.filter_by(username=uname,password=upassword).first()
        if login_credential is None:
            flash("Error, Invalid Username or Password!")
            return render_template('Login.html')
        else:
            entry = Login(rid=login_credential.id,username=uname,password=upassword)
            db.session.add(entry)
            db.session.commit()
            session['name']=uname
            session['password']=upassword
            flash("Welcome, You have been successfully logged-in!")
            return render_template('Welcome.html')

@app.route("/rsubmit", methods=["GET", "POST"])
def register_submit():
    if request.method == "POST":
        fname = request.form.get('fname')
        uname = request.form.get('uname')
        upassword = request.form.get('upassword')
        uemail = request.form.get('uemail')
        uphone = request.form.get('uphone')
        gender = request.form.get('gender')
        address = request.form.get('address')
        entry = Registration(name=fname,username=uname,password=upassword,email=uemail,phone=uphone,gender=gender,address=address)
        db.session.add(entry)
        db.session.commit()
    flash("You have been successfully registered!")
    return render_template('Login.html')

@app.route("/pdsubmit", methods=["GET", "POST"])
def pdetection_submit():
    if request.method == "POST":
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        bg = request.form.get('bg')
        email = request.form.get('email')
        pnumber = request.form.get('pnumber')
        file = request.files['xray']
        if file:
            filename = file.filename
            file.save("./pimages/"+ filename)
            newimg = cv2.imread("./pimages/"+filename, cv2.IMREAD_GRAYSCALE)
            newimg = cv2.resize(newimg, (150, 150)) 
            newimg = newimg.reshape(-1, 150, 150, 1)
            model=tf.keras.models.load_model('model/mp70.h5')
            prediction = model.predict(newimg)
            if int(prediction[0][0])==1:
                result="Normal"
                status="Pneumonia is not detected"
            else:
                result="Pneumonia"
                status="Pneumonia is detected"
            print(status)
            entry = Pdetection(name=name,age=age,gender=gender,blood_group=bg,email=email,phone=pnumber,xray_image=filename,result=result)
            db.session.add(entry)
            db.session.commit()
        return render_template('report.html', name=name,age=age,gender=gender,bloodgroup=bg,emailid=email,phoneno=pnumber,imgname=filename,prediction=status)
    
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/email_submit", methods=["GET", "POST"])
def email_submit():
    if request.method == "POST":
        name = request.form.get('pname')
        email = email = request.form.get('pemail')
        msg = request.form.get('status')
        print(msg)
        if msg=="Pneumonia is detected":
            message="Poor Report "+name+"!\nYour Lungs has been infected by Pneumonia disease.\nKindly take proper medical treatment and take care.\nHope, you get well soon!"
        else:
            message="Hello "+name+"!\nYour Pneumonia Report is Normal.\nHope, you be healthy always!"
    msg = Message(name+' Report', sender = params['gmail-user'], recipients = [email])
    msg.body = message
    mail.send(msg)
    flash("Email sent successfully!")
    return render_template('Pneumonia_Detection.html')
    
@app.route("/logout")
def logout():
    session.pop('name',None)
    session.pop('password',None)
    return render_template('index.html')    
    
if __name__ == "__main__":
    app.run(debug=True)
    
    

    
