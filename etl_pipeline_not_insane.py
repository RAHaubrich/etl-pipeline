from asyncio.windows_events import NULL
import json
from pathlib import Path
import psycopg
from psycopg.errors import UniqueViolation
import pandas as pd
from datetime import datetime
import numpy as np
from numpy import NaN

# Default path to the same location as this file.
current_directory = Path(__file__).resolve().parent

def log(log_message):
    # Crate a new Logs folder if it does not exist.
    Path("Logs").mkdir(exist_ok=True)

    # Fetch the current date and time.
    current_date_time = datetime.now()

    # Create or open a log file relevant to the current day.
    log_name = "log-" + str(current_date_time.date()) + ".txt"
    log_path = current_directory / "Logs" / log_name

    # Log whatever event occurred to said file, including the time of the event down to the millisecond.
    with open(log_path, "a") as log_file:
        log_file.write("[" + str(current_date_time.time()) + "] " + log_message + "\n")

def log_reject(rejected_message):
    # Crate a new Logs folder if it does not exist.
    Path("Logs").mkdir(exist_ok=True)

    # Fetch the current date and time.
    current_date_time = datetime.now()

    # Create or open a log file relevant to the current day.
    rejected_name = "rejected_rows.txt"
    rejected_path = current_directory / "Logs" / rejected_name

    # Log whatever event occurred to said file, including the time of the event down to the millisecond.
    with open(rejected_path, "a") as rejected_file:
        rejected_file.write("[" + str(current_date_time.time()) + "] " + rejected_message + "\n")

def commit_json(file, arrow, link):
    # Open json file 
    json_file = json.load(file)

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
            id = id[0:16]
        if "bio" in user:
            bio = user["bio"]
        if "version" in user:
            version = user["version"]
            if type(version) != float:
                version = None

        # For all non-null values, insert the entry into the table
        if id != NULL:
            try:
                arrow.execute(insert_user, (name, language, id, bio, version))
                log(f"Inserted row with ID {id}.")
            except UniqueViolation as e:
                log(f"Error: User ID {id} already exists.")
                log_reject(f"{user} Duplicate user ID.")
        else:
            log("Skipping row with missing ID.")
            log_reject(f"{user} Missing user ID.")

        link.commit()

def commit_csv(file, arrow, link):
    # Convert the CSV file into a Pandas DataFrame
    csv_df = pd.read_csv(file)

    if np.array_equal(csv_df.columns.values, np.array(['name', 'language', 'id', 'bio', 'version'])) == True:
        # Set default values for all columns of the DataFrame
        csv_df = csv_df.replace(NaN, NULL)
        csv_df_fill = csv_df.fillna({"name": NULL, "language": NULL, "id": NULL, "bio": NULL, "version": NULL})

        # Transform above DataFrame into a NumPy array
        csv_records = csv_df_fill.to_records(index = False)
        
        # For each entry in the CSV file, ensure the ID column is not empty, and if so attempt to insert. The only exception will be if the user's ID is already present.
        for row in csv_records:
            name = row[csv_df.columns.get_loc('name')]
            language = row[csv_df.columns.get_loc('language')]
            id = row[csv_df.columns.get_loc('id')]
            id = id[0:16]
            bio = row[csv_df.columns.get_loc('bio')]
            version = row[csv_df.columns.get_loc('version')]
            if type(version) != float:
                version = None

            row_tuple = (name, language, id, bio, version)

            if id != NULL:
                try:
                    arrow.execute("""
                        INSERT INTO user_profiles (name, language, id, bio, version) VALUES (%s, %s, %s, %s, %s);
                    """, row_tuple)
                    log(f"Inserted row with ID {id}.")
                except UniqueViolation as e:
                    log(f"Error: User ID already exists. ({e})")
                    log_reject(f"{row} Duplicate user ID.")
            else:
                log("Skipping row with missing user ID.")
                log_reject(f"{row} Missing user ID.")

            link.commit()
    else:
        log(f"Invalid columns in {file}, skipping file.")

def import_file(file_name):
    # Crate a new Logs folder if it does not exist.
    Path("Data").mkdir(exist_ok=True)

    # Set the working file to the user input
    working_file = current_directory / "Data" / str(file_name)

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
        log("Connected to server successfully.")
    except:
        # Include a fallback in case I'm stupid and forget to start the postgres server
        log("Unable to connect to server.")
        valid_connection = 0

    # Execute only if the connection is established
    if valid_connection != 0:        
        log(f"Reading from file {file_name}.")

        with connection.cursor() as cur:

            # Creates a table if no such table exists.
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
                    commit_json(read_file, cur, connection)
                    
                elif file_extension == "csv":
                    commit_csv(read_file, cur, connection)

                else:
                    log(f"Invalid file extension: {file_extension}.")

            cur.close()
            connection.close()
        
        log(f"Finished reading from file {file_name}.")

def test_return_none():
    csv_test = commit_csv("single_example.csv")
    json_test = commit_json("first5.json")
    import_test = import_file("single_example.csv")
    
    assert csv_test is None
    assert json_test is None
    assert import_test is None

print("Please enter the file name below:")
user_file = input(str)
user_file = str(user_file)
import_file(user_file)