import sqlite3
from config import DB_NAME, MAX_USERS, MAX_SESSIONS


def create_db():
    """Функция для создания базы данных."""
    con = sqlite3.connect(DB_NAME)
    con.close()


def create_table():
    """Функция для создания таблицы хранения данных пользователя."""
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        sql = '''
            CREATE TABLE IF NOT EXISTS prompts(
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                date DATETIME,
                session_id INTEGER,
                role TEXT,
                content TEXT,
                tokens INTEGER,
                );
        '''
        cur.execute(sql)
    except sqlite3.Error as e:
        print('Ошибка при создании таблицы prompts.', e)
    finally:
        con.close()


def insert_data_into_db(user_id, date, session_id, role, content, tokens):
    """Функция сохранения user_id и предмета задачи в БД."""
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        sql = (f'INSERT INTO prompts(user_id, date, session_id,'
               'role, content, tokens) VALUES(?,?,?,?,?,?);')
        cur.execute(sql, (user_id, date, session_id, role, content, tokens,))
        con.commit()
    except sqlite3.Error as e:
        print('Ошибка записи в таблицу prompts', e)
    finally:
        con.close()


def update_data(user_id, column, value):
    """Функция сохраненя изменений данных пользователя в БД."""
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        sql = f'UPDATE prompts SET {column} = ? WHERE user_id = ?;'
        cur.execute(sql, (value, user_id))
        con.commit()
    except sqlite3.Error as e:
        print('Ошибка изменения в таблице prompts', e)
    finally:
        con.close()


# def delete_data(user_id):
#     """Функция удаления из БД данных пользователя."""
#     con = sqlite3.connect(DB_NAME)
#     cur = con.cursor()
#     sql = 'DELETE FROM users WHERE user_id = ?;'
#     cur.execute(sql, (user_id,))
#     con.commit()
#     con.close()


def select_role_content(user_id, session_id):
    """Функция выводит данные о пользователе по user_id."""
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        sql = f'SELECT role, content FROM prompts WHERE user_id = ? and session_id = ?;'
        cur.execute(sql, (user_id, session_id, ))
        res = cur.fetchall()
        return res
    except sqlite3.Error as e:
        print('Ошибка обращения к таблице prompts', e)
    finally:
        con.close()


def user_exists(user_id):
    """Функция определяет есть ли данные пользователя в БД."""
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    sql = 'SELECT count(*) FROM prompts WHERE user_id = ?;'
    cur.execute(sql, (user_id,))
    res = cur.fetchone()[0]
    con.close()
    return res != 0


def is_limit_users():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    sql = 'SELECT count(DISTINCT user_id) FROM prompts;'
    res = cur.execute(sql)
    con.close()
    return res > MAX_USERS


def is_limit_sessions(user_id):
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    sql = 'SELECT count(session_id) FROM prompts WHERE user_id = ?;'
    res = cur.execute(sql, (user_id,))
    con.close()
    return res > MAX_SESSIONS


def session_counter(user_id):
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    sql = 'SELECT count(session_id) FROM prompts WHERE user_id = ?;'
    res = cur.execute(sql, (user_id,))
    res += 1
    con.close()
    return res


def current_session(user_id):
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    sql = 'SELECT max(session_id) FROM prompts WHERE user_id = ?;'
    res = cur.execute(sql, (user_id,))
    con.close()
    return res
