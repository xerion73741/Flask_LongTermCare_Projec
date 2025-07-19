from flask import Flask, render_template, request, redirect, make_response, session, url_for
import sqlite3
import re  # for email validation
from crawler import crawl_news
from longterm_care_map import create_longtermcare_map
from functools import wraps
from volunteers_db import volunteers_db
from datetime import date, timedelta

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

def volunteer_login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get('volunteer_logined') != '1':
            return redirect(url_for('volunteer_login'))
        return view_func(*args, **kwargs)
    return wrapper

# 🔸 首頁
# @app.route('/')
# def base():
#         name = request.cookies.get('userName')
#         volunteer = session.get('volunteer')
#         return render_template('base.html', userName=name, volunteer=volunteer)
@app.route('/')
def base():
    name = request.cookies.get('userName')
    volunteer = session.get('volunteer')
    top5_news = get_top5_news()
    return render_template('base.html', top5_news=top5_news, userName=name, volunteer=volunteer)
 # 讀取 news.db的五筆資料
def get_top5_news():
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    c.execute("SELECT title, link FROM news ORDER BY id DESC LIMIT 5")
    results = c.fetchall()
    conn.close()
    return results
#---------------------- 使用者登入 ---------------------------------------    
#  登入頁（GET）post進來不會觸發
@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

#  登入處理（POST）
@app.route('/login', methods=['POST'])
def login():
    user = request.form['user']
    passwd = request.form['passwd']
    
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
            resp = make_response(redirect(url_for('base')))
            resp.set_cookie('userName', db_name)
            # session Flask會自動回傳給 user
            session['logined'] = "1"
            return resp
        else:
            return render_template('error.html', message="登入失敗，密碼不正確", back_url = url_for('login_form'))
    else:
        return render_template('error.html', message="登入失敗，帳號不正確", back_url = url_for('login_form'))

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
        return render_template("error.html", message = "Email 格式錯誤", back_url = url_for('register_form')) 

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password, name, email) VALUES (?, ?, ?, ?)",
                       (user, passwd, name, email))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return render_template('error.html', message="帳號或 Email 已存在", back_url=url_for('register_form'))
    
    conn.close()
    return redirect('/login')

#  登出
@app.route('/logout')
def logout():
    session.pop('logined', None)
    resp = make_response(redirect('/login'))
    resp.set_cookie('userName', '', expires=0)
    return resp

# --------------- 地圖相關 --------------------------------------------
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

# -----------------新聞相關 ---------------------------
@app.route("/news", methods=["GET", "POST"]) # 新聞
@login_required
def news():
    # 爬新聞
    news_list = crawl_news()
    name = request.cookies.get('userName')
    # 分頁邏輯
    per_page = 8 #每頁顯示8筆
    page = request.args.get("page",1, type=int) # 取得目前第幾頁(預預為第1頁)
    start = (page-1)*per_page # page-1 是扣除預設的第1頁
    end = start + per_page
    total_pages = (len(news_list)+per_page-1) // per_page # 計算總頁數
    # 傳到news.html 的資料
    return render_template("news.html", 
                           news_list=news_list[start:end], 
                           current_page = page,
                           total_pages = total_pages,
                           userName=name)

#--------- 志工登入 --------------------
@app.route("/volunteer/register", methods=["GET", "POST"])
def volunteer_register():
    if request.method == "GET":
        return render_template('volunteer_register.html')
    else:
        # 用 get 取不到值也不會當掉, strip 去除前後空白
        name = request.form.get('name', '').strip()
        account = request.form.get('account', '').strip()
        password = request.form.get('password', '').strip()
        address = request.form.get('address', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        error = None

        # 驗證
        if not all([name, account, password, address, email]):
            error = "請填寫所有必要欄位"
        elif not is_valid_email(email):
            error = "email 格式錯誤"

                
        if error:
            return render_template('volunteer_register.html', error=error,
                                   name=name, account=account, address=address, 
                                   email=email, phone=phone)
        
        # 插入資料庫
        try:
            db = volunteers_db()
            db.insert_volunteers(name, account, password, address, email, phone)
        except sqlite3.IntegrityError:
            error = "註冊失敗: 帳號或 email 已存在"
            # return 所有參數可以讓使用者不用重填
            return render_template('volunteer_register.html', error=error,
                                name=name, account=account, address=address,
                                email=email, phone=phone)

        return redirect(url_for('volunteer_login'))


@app.route('/volunteer/login', methods=["GET", "POST"])
def volunteer_login():
    if request.method == "GET":
        return render_template('volunteer_login.html')
    elif request.method == "POST":
        db = volunteers_db()
        account = request.form.get('account', '').strip()
        password = request.form.get('password', '').strip()
        user = db.get_volunteer_by_account(account)

        if not user or user['password'] != password:
            error = "帳號或密碼錯誤"
            return render_template('volunteer_login.html', error=error, account=account)

        # 登入成功
        session["volunteer_id"] = user["id"]
        session["volunteer"] = user["name"]
        session['volunteer_logined'] = "1"
        session['logined'] = "1"
        return redirect(url_for("base"))
    
@app.route('/volunteer/logout', methods=["GET"])
def volunteer_logout():
        session.pop('volunteer_id', None)
        session.pop('volunteer', None)
        session.pop('volunteer_logined', None)
        session.pop('logined', None)

        resp = make_response(redirect(url_for('base')))
        resp.set_cookie('userName', '', expires=0)  # 清除 cookie
        return resp 
#---------- 志工班表 -------------------------
@app.route('/volunteer/schedule', methods = ["GET", "POST"])
@volunteer_login_required
def volunteer_schedule():
    # 用 get 取 session 即使沒有這個 session = None 也不會報錯 
    volunteer_id = session.get("volunteer_id")
    db = volunteers_db()

    if request.method == "GET":
        shifts_7 = db.get_shifts_grouped_by_date_time()  # 這裡改用新的函式
        personal_shifts_7 = db.get_all_shifts() 
        personal_shifts = db.query_personal_shifts(volunteer_id)
        today = date.today()
        week = ['日', '一', '二', '三', '四', '五', '六']

        return render_template(
            "volunteer_schedule.html",
            personal_shifts=personal_shifts,
            shifts_7=shifts_7,
            today=today,
            week=week,
            timedelta=timedelta,
            personal_shifts_7=personal_shifts_7
        )


    elif request.method == "POST":

        # 先刪除接下來七天的班表
        for i in range(7):
            shift_date = (date.today() + timedelta(days=i)).isoformat()
            db.delete_shifts_for_date(volunteer_id, shift_date)

        # 插入
        for i in range(7):
            status = request.form.get(f'status_{i}')
            note = request.form.get(f'note_{i}')
            shift_date = (date.today() + timedelta(days=i)).isoformat()
            shift_time = status  # 若 status 就是班別資料，這樣設沒問題

            if status:
                db.insert_shifts(volunteer_id, shift_date, shift_time, note)

        return redirect(url_for('volunteer_schedule'))



if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)