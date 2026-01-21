import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_PASSWORD_HERE",   # Replace with your mysql password
        database="kyc_db"       # Enter your Database name
    )
