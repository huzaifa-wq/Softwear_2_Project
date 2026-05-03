import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def initialize_database(sql_file='initialize_schema.sql'):

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
    )

    cursor = connection.cursor()

    with open(sql_file, 'r') as file:
        sql_script = file.read()

    for statement in sql_script.split(';'):
        if statement.strip():
            cursor.execute(statement)

    connection.commit()
    connection.close()