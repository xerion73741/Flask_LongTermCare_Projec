import sqlite3

# conn = sqlite3.connect('users.db')
# cursor = conn.cursor()

# cursor.execute('''
# CREATE TABLE IF NOT EXISTS users (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     username TEXT UNIQUE NOT NULL,
#     password TEXT NOT NULL,
#     name TEXT NOT NULL,
#     email TEXT UNIQUE NOT NULL
# )
# ''')

# conn.commit()
# conn.close()
# print("資料庫建立完成")


conn = sqlite3.connect('news.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    context TEXT,
    img TEXT,
    link TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP      
)
''')
conn.commit()
conn.close()
print("資料庫立完成")