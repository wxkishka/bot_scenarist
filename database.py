import sqlite3
from config import DB_NAME


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
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                subject TEXT,
                level TEXT,
                task TEXT,
                answer TEXT);
        '''
        cur.execute(sql)
    except sqlite3.Error as e:
        print('Ошибка при создании таблицы users.', e)
    finally:
        con.close()


def insert_data(user_id, subject):
    """Функция сохранения user_id и предмета задачи в БД."""
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        sql = f'INSERT INTO users(user_id, subject) VALUES(?,?);'
        cur.execute(sql, (user_id, subject))
        con.commit()
    except sqlite3.Error as e:
        print('Ошибка записи в таблицу users', e)
    finally:
        con.close()


def update_data(user_id, column, value):
    """Функция сохраненя изменений данных пользователя в БД."""
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        sql = f'UPDATE users SET {column} = ? WHERE user_id = ?;'
        cur.execute(sql, (value, user_id))
        con.commit()
    except sqlite3.Error as e:
        print('Ошибка изменения в таблице users', e)
    finally:
        con.close()


def delete_data(user_id):
    """Функция удаления из БД данных пользователя."""
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    sql = 'DELETE FROM users WHERE user_id = ?;'
    cur.execute(sql, (user_id,))
    con.commit()
    con.close()


def select_data(user_id, column):
    """Функция выводит данные о пользователе по user_id."""
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        sql = f'SELECT {column} FROM users WHERE user_id = ? LIMIT 1;'
        cur.execute(sql, (user_id,))
        res = cur.fetchone()
        return res
    except sqlite3.Error as e:
        print('Ошибка обращения к таблице users', e)
    finally:
        con.close()


def user_exists(user_id):
    """Функция определяет есть ли данные пользователя в БД."""
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    sql = 'SELECT count(*) FROM users WHERE user_id = ?;'
    cur.execute(sql, (user_id,))
    res = cur.fetchone()[0]
    con.close()
    return res != 0
