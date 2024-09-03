import mysql.connector
from mysql.connector import errorcode
import json
import config  # Import the config file to access credentials

# Data to be used to populate the database 
teams = [
    ('Besaid Aurochs',),
    ('Luca Goers',),
    ('Kilika Beasts',),
    ('Al Bhed Psyches',),
    ('Ronso Fangs',),
    ('Guado Glories',),
    ('Free Agent',),
    ('Custom Team',)
]
techniques = 'data/techniques.json'
players = 'data/players.json'

# Define functions for pulling in data from the JSON files 
def load_techniques_from_json(json_file):
    """
    Function to load techniques from a JSON file and insert them into the techniques table.
    """
    with open(json_file, 'r') as file:
        techniques_data = json.load(file)

    techniques_to_insert = [
        (technique['technique_name'], technique['hp_cost'], technique['chance'], technique['description'])
        for technique in techniques_data['techniques']
    ]
    
    cursor.executemany("""
        INSERT IGNORE INTO techniques (technique_name, hp_cost, chance, description)
        VALUES (%s, %s, %s, %s)
    """, techniques_to_insert)
    db.commit()
    print("Techniques have been added to the database.")

def load_players_from_json(json_file):
    """
    Function to load players and their stats from a JSON file and insert them into the players and player_stats tables.
    """
    with open(json_file, 'r') as file:
        players_data = json.load(file)

    for player in players_data['players']:
        # Insert player into the players table
        cursor.execute("""
            INSERT INTO players (name, key_techniques, location, starting_team)
            VALUES (%s, %s, %s, %s)
        """, (player['name'], ', '.join(player['key_techniques']), player['location'], player['starting_team']))
        player_id = cursor.lastrowid

        # Ensure player_id is fetched correctly
        if player_id is None:
            print(f"Error: Could not retrieve player_id for {player['name']}")
            continue

        # Insert player stats into the player_stats table
        stats_to_insert = [
            (player_id, stat['level'], stat['hp'], stat['speed'], stat['endurance'], stat['attack'],
             stat['pass'], stat['block'], stat['shot'], stat['catch'])
            for stat in player['stats']
        ]
        cursor.executemany("""
            INSERT INTO player_stats (player_id, level, hp, speed, endurance, attack, pass, block, shot, catch)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, stats_to_insert)

    db.commit()
    print("Players and their stats have been added to the database.")

# Establish connection to MySQL
try:
    db = mysql.connector.connect(
        host="localhost",
        user=config.DB_USER,       # MySQL username from config file
        password=config.DB_PASSWORD  # MySQL password from config file
    )
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
else:
    cursor = db.cursor()

    # Create database
    cursor.execute("CREATE DATABASE IF NOT EXISTS blitzball_db")
    cursor.execute("USE blitzball_db")

    # Create tables
    #players
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            key_techniques VARCHAR(255),
            location VARCHAR(100),
            starting_team VARCHAR(100)
        )
    """)

    #players_stats
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            stat_id INT AUTO_INCREMENT PRIMARY KEY,
            player_id INT,
            level INT,
            hp INT,
            speed INT,
            endurance INT,
            attack INT,
            pass INT,
            block INT,
            shot INT,
            catch INT,
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )
    """)

    #teams
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INT AUTO_INCREMENT PRIMARY KEY,
            team_name VARCHAR(100) NOT NULL UNIQUE
        )
    """)
    cursor.executemany("INSERT IGNORE INTO teams (team_name) VALUES (%s)", teams)

    #techniques
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS techniques (
            technique_id INT AUTO_INCREMENT PRIMARY KEY,
            technique_name VARCHAR(100) NOT NULL UNIQUE,
            hp_cost INT,
            chance VARCHAR(10),
            description TEXT
        )
    """)

    db.commit()
    print("Tables have been added to the database.")

    load_techniques_from_json(techniques)
    load_players_from_json(players)

    # Close the cursor and the connection
    cursor.close()
    db.close()
