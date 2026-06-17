from asyncio.windows_events import NULL
import json
from pathlib import Path
from numpy import NaN
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

        # Include a fallback in case I'm stupid and forget to start the postgres server
        print("Connection not found!")
        valid_connection = 0

    # Execute only if the connection is established
    if valid_connection != 0:
        with connection.cursor() as cur:
            
            # Creates a
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    name TEXT DEFAULT NULL,
                    language TEXT DEFAULT NULL,
                    id VARCHAR(16) PRIMARY KEY,
                    bio TEXT DEFAULT NULL,
                    version FLOAT DEFAULT NULL
                );
            """)

            with open(working_file, "r") as read_file:

                if file_extension == "json":
                    
                    # Open json file 
                    json_file = json.load(read_file)

                    # Create format to insert users
                    insert_user = "INSERT INTO user_profiles (name, language, id, bio, version) VALUES (%s, %s, %s, %s, %s);"

                    # Loop through all users and insert any non-duplicates with a valid ID
                    for user in json_file:
                        
                        # Set defaults for all fields then replace with values 
                        name, language, id, bio, version = NULL, NULL, NULL, NULL, NULL

                        if "name" in user:
                            name = user["name"]
                        if "language" in user:
                            language = user["language"]
                        if "id" in user:
                            id = user["id"]
                        if "bio" in user:
                            bio = user["bio"]
                        if "version" in user:
                            version = user["version"]

                        # For all non-null values, insert the entry into the table
                        if id != NULL:
                            try:
                                cur.execute(insert_user, (name, language, id, bio, version))
                            except UniqueViolation as e:
                                print(f"Error: User ID {id} already exists. ({e})")
                        else:
                            print("Skipping row with missing ID.")

                        connection.commit()
                    
                elif file_extension == "csv":

                    # Convert the CSV file into a Pandas DataFrame
                    csv_df = pd.read_csv(read_file)

                    # Set default values for all columns of the DataFrame
                    csv_df = csv_df.replace(NaN, NULL)
                    csv_df_fill = csv_df.fillna({"name": NULL, "language": NULL, "id": NULL, "bio": NULL, "version": NULL})

                    # Transform above DataFrame into a NumPy array
                    csv_records = csv_df_fill.to_records(index = False)
                    
                    # For each entry in the CSV file, ensure the ID column is not empty, and if so attempt to insert. The only exception will be if the user's ID is already present.
                    for row in csv_records:
                        if row[2] != NULL:
                            try:
                                cur.execute("""
                                    INSERT INTO user_profiles (name, language, id, bio, version) VALUES (%s, %s, %s, %s, %s);
                                """, tuple(row)) 
                            except UniqueViolation as e:
                                print(f"Error: That user ID already exists. ({e})")
                        else:
                            print("Skipping row with missing ID.")

                        connection.commit()

            cur.close()
            connection.close()

# import_file("single_example.csv")
# import_file("first5.json")