# Oracle Python
# pip install cx_oracle

import cx_Oracle
dsn = cx_Oracle.makedsn(
    'localhost', 
    '1521', 
    service_name='orcl'
)
conn = cx_Oracle.connect(
    user='test', 
    password='test', 
    dsn=dsn
)
c = conn.cursor()
c.execute('SELECT * FROM employees WHERE ROWNUM <= 10')
for row in c: print(row)
conn.close()


# SQL Server Python
# pip install pyodbc

import pyodbc
conn = pyodbc.connect(
    'Driver={SQL Server};'
    'Server=DESKTOP-ABC\SQLEXPRESS;'
    'Database=mytestdb;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()
cursor.execute('SELECT TOP 5 * FROM dbo.employees')
for row in cursor: print(row)
conn.close()

# MySQL Python

import mysql.connector
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    passwd='1234'
)
cursor = conn.cursor()
cursor.execute('SELECT * FROM test.employees LIMIT 5')
for row in cursor: print(row)
conn.close()

# SQL Server Python
# pip install psycopg2

import psycopg2
conn = psycopg2.connect(
    user='postgres',
    password='1234',
    host='127.0.0.1',
    port='5432',
    database='mytestdb'
)
cursor = conn.cursor()
cursor.execute('SELECT * FROM actor employees 10')
for row in cursor: print(row)
conn.close()

# SQLite Python

import sqlite3
conn = sqlite3.connect('myitems.db') # or use temp / memory ':memory:'
c = conn.cursor()
c.execute("SELECT * FROM employees")
print(c.fetchall())
conn.close()