from flask import Flask, render_template, request, redirect, make_response, session, url_for
import sqlite3
import re  # for email validation
from crawler import crawl_news
from longterm_care_map import create_longtermcare_map
from functools import wraps

app = Flask(__name__)
app.secret_key = 'Gail secret key'

#  檢查 Email 格式的函式
def is_valid_email(email):
   return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get('logined') != '1':
            return redirect(url_for('login_form'))
        return view_func(*args, **kwargs)
    return wrapper

# 🔸 首頁
@app.route('/')
def home():
        name = request.cookies.get('userName')
        return render_template('home.html', userName=name)
    
#  登入頁（GET）post進來不會觸發
@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

#  登入處理（POST）
@app.route('/login', methods=['POST'])
def login():
    user = request.form['user']
    passwd = request.form['passwd']
    # name = request.form['name']

    
    conn = sqlite3.connect('users.db')
    # 將 sql execute 拿出來的資料變成 dict
    # conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (user,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        db_passwd = result[2]
        db_name = result[3]
        if passwd == db_passwd:
            # make_response 是為了 set_cookie
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('userName', db_name)
            # session Flask會自動回傳給 user
            session['logined'] = "1"
            return resp
        else:
            return "登入失敗，密碼不正確"
    else:
        return "登入失敗，帳號不正確"

#  註冊頁（GET）
@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')

# 註冊處理（POST）
@app.route('/register', methods=['POST'])
def register():
    user = request.form['user']
    passwd = request.form['passwd']
    name = request.form['name']
    email = request.form['email']

    # 驗證 Email 格式
    if not is_valid_email(email):
        return "註冊失敗：Email 格式錯誤"

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password, name, email) VALUES (?, ?, ?, ?)",
                       (user, passwd, name, email))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "註冊失敗：帳號或 Email 已存在"
    
    conn.close()
    return redirect('/login')

#  登出
@app.route('/logout')
def logout():
    session.pop('logined', None)
    resp = make_response(redirect('/login'))
    resp.set_cookie('userName', '', expires=0)
    return resp

@app.route('/search', methods=["POST", "GET"])
@login_required
def search():
    name = request.cookies.get('userName')

    if request.method == 'POST':
        city = request.form.get('city')
        dist = request.form.get('dist')
        if not city or not dist:
            return render_template('search.html', userName=name)

        # 先產生 map_html
        map_html = create_longtermcare_map(city, dist)

        # 接著檢查 map_html 是不是「查無資料」的訊息
        if "<p style='color:red;'>查無資料，請重新輸入</p>" in map_html:
            return render_template('search.html', map_html=map_html, userName=name)
        else:
            return render_template('search.html', map_html=map_html, userName=name)
    # 如果沒有東西進來
    else:
        return render_template('search.html', userName=name)

@app.route("/news", methods=["GET", "POST"]) # 新聞
@login_required
def news():
    news_list = crawl_news()
    name = request.cookies.get('userName')

    return render_template("news.html", news_list=news_list, userName=name)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)