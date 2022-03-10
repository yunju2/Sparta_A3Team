import jwt
import datetime
import hashlib
import pafy
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = ''

from pymongo import MongoClient
client = MongoClient()

db = client.dbsparta

@app.route('/')
def home():
     token_receive = request.cookies.get('mytoken')
     try:
         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
         user_info = db.users.find_one({"username":payload['id']})
         return render_template('index.html', user_info=user_info)
     except jwt.ExpiredSignatureError:
         return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
     except jwt.exceptions.DecodeError:
         return render_template('index.html')

@app.route("/music", methods=["POST"])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        url_receive = request.form['url_give']
        cate_receive = request.form['cate_give']
        comment_receive = request.form['comment_give']
        embed = url_receive.replace(url_receive.split('/')[-1][0:8], 'embed/')
        video = pafy.new(url_receive)
        title = video.title
        rating = video.rating
        author = video.author
        view = video.viewcount
        a, b = divmod(view, 10000)
        if a:
            view = str(a) + '만'
        else:
            view = str(b)
        doc = {
            "username": user_info["username"],
            "profile_name": user_info["profile_name"],
            "profile_pic_real": user_info["profile_pic_real"],
            'embed': embed,
            'url': url_receive,
            'title': title,
            'rating': rating,
            'view': view,
            'author': author,
            'comment': comment_receive,
            'cate': cate_receive
            }
        db.music.insert_one(doc)
        return jsonify({'msg': '노래 일기 기록 완료'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
          return redirect(url_for("home"))

@app.route("/music", methods=["GET"])
def listing():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY,algorithms=['HS256'])
        username_receive = request.args.get("username_give")
        music_list = list(db.music.find({"username": username_receive}).sort("date", -1).limit(20))
        for music in music_list:
            music["_id"] = str(music["_id"])
        return jsonify({'result': 'success','msg':"포스팅을 가져왔습니다", 'music_list':music_list})
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route("/music/happy", methods=["GET"])
def music_happy():
    music_list = list(db.music.find({'cate': '희'}, {'_id': False}).sort("date",-1))
    return jsonify({'music_list': music_list})

@app.route("/music/angry", methods=["GET"])
def music_angry():
    music_list = list(db.music.find({'cate': '노'}, {'_id': False}).sort("date",-1))
    return jsonify({'music_list': music_list})

@app.route("/music/sad", methods=["GET"])
def music_sad():
    music_list = list(db.music.find({'cate': '애'}, {'_id': False}).sort("date",-1))
    return jsonify({'music_list': music_list})

@app.route("/music/fun", methods=["GET"])
def music_fun():
    music_list = list(db.music.find({'cate': '락'}, {'_id': False}).sort("date",-1))
    return jsonify({'music_list': music_list})


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})
    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})



@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/update_music', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        url_receive = request.form['url_give']
        cate_receive = request.form['cate_give']
        comment_receive = request.form['comment_give']
        video = pafy.new(url_receive)
        title = video.title
        embed = url_receive.replace(url_receive.split('/')[-1][0:8], 'embed/')
        new_doc = {
            "embed": embed,
            "url": url_receive,
            "cate": cate_receive,
            "comment": comment_receive,
            'title': title
        }
        db.music.update_one({'username': payload['id']}, {'$set':new_doc})
        return jsonify({"result": "success", 'msg': '수정 완료'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

# @app.route('/music/delete', methods=['POST'])
# def delete_music():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         id_receive = request.form['id_give']
#         db.music.delete_one({'id': id_receive})
#         return jsonify({"result": "success", 'msg': '삭제완료'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)