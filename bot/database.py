import sqlite3 as sql
import typing as ty


path = str

def connect(path: path) -> ty.Tuple[sql.Connection, sql.Cursor]:
    c = sql.connect(database=path)
    return c, c.cursor()


def create_tables(connection: sql.Connection, cursor: sql.Cursor) -> None:
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            name varchar(255),
            surename varchar(255),
            login varchar(255),
            password varchar(255),
            logged_account_id integer
        )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS hmtable (
            timestamp float,
            sended boolean,
            logged_account_id_ integer
        )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS newsletter(
            user_id integer,
            newsletter_sended boolean
        )""")
    connection.commit()