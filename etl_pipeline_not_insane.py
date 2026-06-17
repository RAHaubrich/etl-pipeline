import json
from pathlib import Path
import psycopg
# from psycopg import sql
from psycopg.errors import UniqueViolation
import pandas as pd

# Default path to the same location as this file.
current_directory = Path(__file__).resolve().parent

def import_file(file_name):
    # Set the working file to the user input
    working_file = current_directory / str(file_name)

    parse_periods = file_name.split(".")
    file_extension = parse_periods[-1]

    valid_connection = 1

    try:
        
        # Establish connection to postgres server
        connection = psycopg.connect(
                dbname="postgres",
                user="postgres",
                password=")A*(7ubdiufh08B)",
                host="localhost",
                port="5432"
            )
    except:
        print("Connection not found!")
        valid_connection = 0

    if valid_connection != 0:
        with connection.cursor() as cur:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    name TEXT,
                    language TEXT,
                    id VARCHAR(16) PRIMARY KEY,
                    bio TEXT,
                    version FLOAT
                );
            """)

            with open(working_file, "r") as read_file:

                if file_extension == "json":

                    # Open json file 
                    json_file = json.load(read_file)

                    insert_user = "INSERT INTO user_profiles (name, language, id, bio, version) VALUES (%s, %s, %s, %s, %s);"

                    for user in json_file:
                        try:
                            cur.execute(insert_user, (user["name"], user["language"], user["id"], user["bio"], user["version"]))
                        except UniqueViolation as e:
                            print(f"Error: That user ID already exists. ({e})")

                        connection.commit()
                    
                elif file_extension == "csv":

                    print("meme currently under construction, please wait")
                    print("shoplifters when the shop is too heavy")

                    pd.options.display.max_rows = 25

                    csv_df = pd.read_csv(read_file)

                    csv_records = csv_df.to_records(index = False)
                    
                    for row in csv_records:
                        try:
                            cur.execute("""
                                INSERT INTO user_profiles (name, language, id, bio, version) VALUES (%s, %s, %s, %s, %s);
                            """, tuple(row)) 
                        except UniqueViolation as e:
                            print(f"Error: That user ID already exists. ({e})")

            cur.close()
            connection.close()

import_file("single_example.csv")
# import_file("first5.json") 