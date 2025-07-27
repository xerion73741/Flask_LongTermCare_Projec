import os 
import sqlite3
# 計算BMI
def get_bmi(height, weight):
    height /= 100
    bmi = weight / height **2
    bmi = round(bmi, 1)
    return bmi

# 計算BMR 
def get_bmr(sex, height, weight, age):
    if sex == "男":
        bmr = 66 +13.7*weight +5*height - 6.8*age
    else:
        bmr = 655 + 9.6*weight +1.8*height - 5.7*age
        bmr = round(bmr, 2)
    return bmr
# 計算TDEE
def get_tdee(sex, height, weight, age, times):
    bmr = get_bmr(sex, height, weight, age)
    tdee = bmr*times
    tdee = round(tdee, 2)
    return tdee

# 初始化資料庫
def health_db():
    if not os.path.exists("tdee.db"):
        conn = sqlite3.connect("tdee.db")
        c = conn.cursor()
        c.execute('''
            CREATE TABLE tdee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sex TEXT,
                height REAL,
                weight REAL,
                age INTEGER,
                times REAL,
                tdee REAL
            )
        ''')
        conn.commit()
        conn.close()
        
health_db()
print("資料庫建立完成")