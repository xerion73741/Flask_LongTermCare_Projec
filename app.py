from flask import Flask, render_template, request, redirect, make_response, session, url_for
import sqlite3
import re  # for email validation
from crawler import get_crawler_news
from longterm_care_map import create_longtermcare_map
from functools import wraps
from volunteers_db import volunteers_db
from datetime import date, timedelta
from email.mime.text import MIMEText
import smtplib 
import os
from service import get_carecenter_data
from weight_machtine import get_bmi, get_bmr, get_tdee

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


# --------------- 註冊成功後寄信 --------------------------------------------
    subject = "長照系統，註冊成功通知"
    body = f'{name} 您好，\n\n 您已成功註冊長照系統，歡迎您的加入！ \n\n帳號： {user}\n\n 此信件由系統自動發出，請勿回信。'
    send_mail(to_email=email, subject=subject, body=body)

    return redirect('/login')


# --------------- 寄送註冊信 --------------------------------------------
def send_mail(to_email, subject, body):
    from_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com' , 465 ) as stmp:
            stmp.login(from_email, password)
            stmp.send_message(msg)
            print('信件已發送')
    except Exception as e:
        print("信件發送失敗",e)

#  登出
@app.route('/logout')
def logout():
    session.pop('logined', None)
    resp = make_response(redirect('/login'))
    resp.set_cookie('userName', '', expires=0)
    return resp


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
        # 志工 id
        session["volunteer_id"] = user["id"]
        # 志工 name
        session["volunteer"] = user["name"]
        # 志工登入
        session['volunteer_logined'] = "1"
        # user 登入
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
    volunteer = session.get("volunteer") ###########
    db = volunteers_db()

    if request.method == "GET":
        shifts_7 = db.get_shifts_grouped_by_date_time()  
        week_map = ['日', '一', '二', '三', '四', '五', '六']
        today = date.today()
        # 計算今天離周日是第幾天 today.weekday() 周日是0
        days_since_sunday = (today.weekday() + 1) % 7  
        # timedelta 將參數轉乘時間格式
        # 今日扣去與周日的時間差, 便可以找到周日(0)
        # 找出 周日的日期
        sunday = today - timedelta(days=days_since_sunday) 
        # 動態產生: index(0)為周日的日期序列
        # ['2025-07-20','2025-07-21'...]
        dates = [sunday + timedelta(days=i) for i in range(7)]
        # [ (datetime.date(2025, 7, 20), '日'),.......]
        dates_with_week = [(d, week_map[(d.weekday() + 1) % 7]) for d in dates]
        return render_template(
            'volunteer_schedule.html',
            shifts_7=shifts_7,
            dates_with_week=dates_with_week,
            volunteer_id=volunteer_id,
            volunteer=volunteer,
            days_since_sunday=days_since_sunday,
            week_map=week_map,
        )



        # adjusted_start = (start + 1) % 7
        # week = week_map[adjusted_start:] + week_map[:adjusted_start]
        # return render_template(
        #     "volunteer_schedule.html",
        #     personal_shifts=personal_shifts,
        #     shifts_7=shifts_7,
        #     today=today,
        #     timedelta=timedelta,
        #     personal_shifts_7=personal_shifts_7,
        #     volunteer=volunteer ########
        # )

    elif request.method == "POST":
        today = date.today()
        days_since_sunday = (today.weekday() + 1) % 7
        sunday = today - timedelta(days=days_since_sunday)

        # 先刪除本週日開始連續七天的班表
        for i in range(7):
            shift_date = (sunday + timedelta(days=i)).isoformat()
            db.delete_shifts_for_date(volunteer_id, shift_date)

        # 插入新班表
        for i in range(7):
            status = request.form.get(f'status_{i}')
            note = request.form.get(f'note_{i}')
            shift_date = (sunday + timedelta(days=i)).isoformat()
            shift_time = status

            if status:
                db.insert_shifts(volunteer_id, shift_date, shift_time, note)

        return redirect(url_for('volunteer_schedule'))



# -----------------新聞相關 ---------------------------
@app.route("/news", methods=["GET", "POST"]) # 新聞
# @login_required 要先登入  才能進入news的頁面
def news():
    # 爬新聞
    news_list = get_crawler_news()
    name = request.cookies.get('userName')
    volunteer = session.get('volunteer')
    # 分頁邏輯
    per_page = 8 #每頁顯示8筆
    page = request.args.get("page",1, type=int) # 取得目前第幾頁(預設為第1頁)
    start = (page-1)*per_page # page-1 是扣除預設的第1頁
    end = start + per_page
    total_pages = (len(news_list)+per_page-1) // per_page # 計算總頁數
    # 傳到news.html 的資料
    return render_template("news.html", 
                           news_list=news_list[start:end], 
                           current_page = page,
                           total_pages = total_pages,
                           userName=name,
                           volunteer=volunteer,
                           )


# --------------- 地圖相關 --------------------------------------------
@app.route('/search', methods=["POST", "GET"])
# @login_required
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
        if map_html is None:
            message = "<p style='color:red;'>查無資料, 請重新輸入</p>"
            return render_template('search.html', message=message, userName=name, )
        else:
            print(map_html[:300])
            return render_template('search.html', map_html=map_html, userName=name)
    # 如果沒有東西進來
    else:
        return render_template('search.html', userName=name)


# --------------- 各縣市長照線上申請---------------------------------------
# 加上request.args.get()判斷搜尋關鍵字

@app.route("/service")
def service():
# -- 給他快取, render 也要回傳, html 才判斷的到
    userName = request.cookies.get('userName') 
    volunteer = session.get("volunteer")  
# ----------------------------------------
    data = get_carecenter_data()                                
    return render_template('service.html', centers = data, userName=userName, volunteer=volunteer)

# --------------- 綜合健康計算機---------------------------------------
#  BMI BMR
@app.route("/bmi", methods=["POST", "GET"])
def bmi():
    bmi_result = None
    bmr_result = None
    if request.method == "POST":
        form_type = request.form.get("form_type")
        height = float(request.form["height"])
        weight = float(request.form["weight"])

        if form_type == "bmi":
            bmi_value = get_bmi(height, weight)
            bmi_result = f"你的身高：{height:.1f}公分，體重：{weight:.1f}公斤，你的身體質量指數（BMI）：{bmi_value:.2f}"

        elif form_type == "bmr":
            sex = request.form["sex"]
            age = int(request.form["age"])
            bmr_value = get_bmr(sex, height, weight, age)
            bmr_result = f"你的性別：{sex}，身高：{height:.1f}公分，體重：{weight:.1f}公斤，年齡是：{age}歲，你的基礎代謝率（BMR）：{bmr_value:.2f}"

    return render_template("bmi.html", bmi_result=bmi_result, bmr_result=bmr_result)



if __name__ == '__main__':
    # 這段程式碼只在您直接運行 app.py 時執行，例如在本地開發時
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)

