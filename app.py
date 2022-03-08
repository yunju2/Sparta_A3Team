from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

import pafy

from pymongo import MongoClient
client = MongoClient()
db = client.dbsparta

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/music", methods=["POST"])
def music_post():
    url_receive = request.form['url_give']
    cate_receive = request.form['cate_give']
    comment_receive = request.form['comment_give']
    embed = url_receive.replace(url_receive.split('/')[-1][0:8], 'embed/')
    video = pafy.new(url_receive)
    title = video.title
    rating = video.rating
    view = video.viewcount
    author = video.author
    print(title, rating, view, author)
    doc={
        'embed':embed,
        'url':url_receive,
        'title':title,
        'rating':rating,
        'view':view,
        'author':author,
        'comment':comment_receive,
        'cate':cate_receive
    }
    db.music.insert_one(doc)

    return jsonify({'msg':'노래 일기 기록 완료'})

@app.route("/music", methods=["GET"])
def music_get():
    music_list = list(db.music.find({}, {'_id': False}))
    return jsonify({'music_list':music_list})

@app.route("/music/happy", methods=["GET"])
def music_happy():
    music_list = list(db.music.find({'cate':'희'}, {'_id': False}))
    return jsonify({'music_list':music_list})

@app.route("/music/angry", methods=["GET"])
def music_angry():
    music_list = list(db.music.find({'cate':'노'}, {'_id': False}))
    return jsonify({'music_list':music_list})

@app.route("/music/sad", methods=["GET"])
def music_sad():
    music_list = list(db.music.find({'cate':'애'}, {'_id': False}))
    return jsonify({'music_list':music_list})

@app.route("/music/fun", methods=["GET"])
def music_fun():
    music_list = list(db.music.find({'cate':'락'}, {'_id': False}))
    return jsonify({'music_list':music_list})


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)