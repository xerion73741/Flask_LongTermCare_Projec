import sqlite3
from collections import defaultdict

DB_NAME = 'volunteers.db'
class volunteers_db:
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self._create_table()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        # 將讀出來的資料裝在 dict
        conn.row_factory = sqlite3.Row 
        return conn

    def _create_table(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            # 志工
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS volunteers(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,           
                    name TEXT NOT NULL,
                    account TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    address TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    phone TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')

            # 班表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shifts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    volunteer_id INTEGER NOT NULL,
                    shift_date DATE NOT NULL,
                    shift_time TEXT NOT NULL,
                    note TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(volunteer_id) REFERENCES volunteers(id) ON DELETE CASCADE
                )
            ''')


    def insert_volunteers(self, name, account, password, address, email, phone):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO volunteers(name, account, password, address, email, phone)
                VALUES(?, ?, ?, ?, ?, ?)
            ''', (name, account, password, address, email, phone))
            conn.commit()

    def query_volunteers(self, account=None, email=None, status=None, page=1, page_size=10):
        with self._connect() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM volunteers WHERE 1=1"
            params = []

            if account:
                query += " AND account = ?"
                params.append(account)
            if email:
                query += " AND email = ?"
                params.append(email)
            if status:
                query += " AND status = ?"
                params.append(status)

            offset = (page - 1) * page_size
            query += " LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            cursor.execute(query, params)
            return cursor.fetchall()

    def get_volunteer_by_account(self, account):
        result = self.query_volunteers(account=account, page=1, page_size=1)
        if result:
            return result[0]  # 取第一筆
        return None

    def update_volunteers(self, volunteer_id, account=None, address=None, email=None, phone=None, status=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            query = "UPDATE volunteers SET "
            fields = []
            params = []

            if account:
                fields.append("account = ?")
                params.append(account)
            if address:
                fields.append("address = ?")
                params.append(address)
            if email:
                fields.append("email = ?")
                params.append(email)
            if phone:
                fields.append("phone = ?")
                params.append(phone)
            if status:
                fields.append("status = ?")
                params.append(status)

            # 沒有任何值就直接結束
            if not fields: 
                return 

            query += ", ".join(fields)
            query += " WHERE id = ?"
            params.append(volunteer_id)

            cursor.execute(query, params)
            conn.commit()

    # 軟刪除
    def deactivate_volunteer(self, volunteer_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE volunteers SET status = 'inactive' WHERE id = ?", (volunteer_id,))
            conn.commit()
            return cursor.rowcount 
        
# ------- shifts -------------
    def insert_shifts(self ,volunteer_id, shift_date, shift_time, note=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO shifts(volunteer_id, shift_date, shift_time, note)
                VALUES (?, ?, ?, ?)
            ''', (volunteer_id, shift_date, shift_time, note))
            conn.commit()

    def query_shifts(self, volunteer_id=None, shift_date=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM shifts WHERE 1=1"
            params = []

            if volunteer_id:
                query += " AND volunteer_id = ?"
                params.append(volunteer_id)
            if shift_date:
                query += " AND shift_date = ?"
                params.append(shift_date)

            cursor.execute(query, params)
            return cursor.fetchall()

    def get_all_shifts(self, limit=7):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT v.name, s.shift_date, s.shift_time, s.note
                FROM shifts s
                JOIN volunteers v ON s.volunteer_id = v.id
                ORDER BY s.shift_date DESC, v.name
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        
    def query_personal_shifts(self, volunteer_id, shift_date=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            query = """
                SELECT v.name, s.shift_date, s.shift_time, s.note
                FROM shifts s
                JOIN volunteers v ON s.volunteer_id = v.id
                WHERE s.volunteer_id = ?
            """
            params = [volunteer_id]

            if shift_date:
                query += " AND shift_date = ?"
                params.append(shift_date)

            query += " ORDER BY shift_date ASC, shift_time ASC"
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def delete_shifts_for_date(self, volunteer_id, shift_date):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM shifts WHERE volunteer_id = ? AND shift_date = ?', (volunteer_id, shift_date))
            conn.commit()

    def get_shifts_grouped_by_date_time(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT v.name, s.shift_date, s.shift_time
                FROM shifts s
                JOIN volunteers v ON s.volunteer_id = v.id
                WHERE s.shift_date BETWEEN date('now') AND date('now', '+6 days')
            ''')
            rows = cursor.fetchall()

        shifts = defaultdict(lambda: defaultdict(list))
        for row in rows:
            shifts[row['shift_date']][row['shift_time']].append(row['name'])

        return shifts

    
if __name__ == '__main__':
    db = volunteers_db()
    shifts_7 = db.get_shifts_grouped_by_date_time()
    print(shifts_7)
    # db.insert_volunteers('藍藍', 'blue', '1234', '新北市', 'blue@blue.com', '1234')
    # print(db.query_volunteers())
    # db.update_volunteers(1, phone='0985511228')
    # db.deactivate_volunteer(1)

