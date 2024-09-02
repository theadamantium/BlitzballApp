import mysql.connector
from mysql.connector import errorcode
import json
import config  # Import the config file to access credentials

# define functions for pulling in data from the JSON files 
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

    # Create players table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            key_techniques VARCHAR(255),
            location VARCHAR(100),
            starting_team VARCHAR(100)
        )
    """)

    # Create player_stats table
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

    # Create teams table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INT AUTO_INCREMENT PRIMARY KEY,
            team_name VARCHAR(100) NOT NULL UNIQUE
        )
    """)

    # Add sample teams
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
    cursor.executemany("INSERT IGNORE INTO teams (team_name) VALUES (%s)", teams)

    # Create techniques table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS techniques (
            technique_id INT AUTO_INCREMENT PRIMARY KEY,
            technique_name VARCHAR(100) NOT NULL UNIQUE,
            hp_cost INT,
            chance VARCHAR(10),
            description TEXT
        )
    """)

    # Load techniques from JSON file
    load_techniques_from_json('techniques.json')

    # Create player_key_techniques table for many-to-many relationship between players and techniques
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_key_techniques (
            player_id INT,
            technique_id INT,
            FOREIGN KEY (player_id) REFERENCES players(player_id),
            FOREIGN KEY (technique_id) REFERENCES techniques(technique_id),
            PRIMARY KEY (player_id, technique_id)
        )
    """)

    # Commit changes for teams and techniques
    db.commit()

    # Check if there are players in the table
    cursor.execute("SELECT COUNT(*) FROM players")
    player_count = cursor.fetchone()[0]

    if player_count == 0:
        create_team = input("No players found in the database. Would you like to create the Besaid Aurochs team? (Y/N): ").strip().lower()
        if create_team == 'y':
            # Functions to add players, techniques, and stats
            def add_player(cursor, name, location, starting_team):
                """Add a player to the players table."""
                cursor.execute("""
                    INSERT INTO players (name, location, starting_team)
                    VALUES (%s, %s, %s)
                """, (name, location, starting_team))
                return cursor.lastrowid

            def add_key_techniques(cursor, player_id, technique_names):
                """Add key techniques for a player to the player_key_techniques table."""
                technique_ids = []
                for name in technique_names:
                    cursor.execute("SELECT technique_id FROM techniques WHERE technique_name = %s", (name,))
                    technique_id = cursor.fetchone()
                    if technique_id:
                        technique_ids.append((player_id, technique_id[0]))

                cursor.executemany("""
                    INSERT INTO player_key_techniques (player_id, technique_id)
                    VALUES (%s, %s)
                """, technique_ids)

            def add_player_stats(cursor, player_id, stats):
                """Add stats for a player to the player_stats table."""
                cursor.executemany("""
                    INSERT INTO player_stats (player_id, level, hp, speed, endurance, attack, pass, block, shot, catch)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [(player_id, *stat) for stat in stats])

            # Sample player data in JSON format
            sample_players = [
                {
                    "name": "Jassu",
                    "location": "Luca -- Aurochs Locker room",
                    "starting_team": "Besaid Aurochs",
                    "key_techniques": ["Wither Tackle", "Wither Tackle 2", "Nap Tackle 2"],
                    "stats": [
                        (1, 100, 63, 7, 10, 7, 5, 1, 1),
                        (10, 448, 63, 13, 12, 10, 7, 3, 3),
                        (20, 982, 64, 19, 15, 14, 10, 5, 5),
                        (30, 1672, 64, 24, 18, 18, 13, 7, 7),
                        (40, 2518, 65, 28, 21, 23, 17, 9, 9),
                        (50, 3520, 65, 31, 25, 27, 21, 11, 11),
                        (60, 4678, 66, 34, 29, 32, 25, 13, 13),
                        (70, 5992, 66, 36, 34, 37, 29, 15, 15),
                        (80, 7462, 67, 37, 39, 42, 34, 17, 17),
                        (90, 9088, 67, 37, 45, 47, 39, 19, 19),
                        (99, 9999, 67, 37, 50, 52, 44, 20, 20),
                    ]
                },
                # Add other players here in the same format
                # {
                #     "name": "Tidus",
                #     "location": "",
                #     "starting_team": "Besaid Aurochs",
                #     "key_techniques": ["Jecht Shot", "Sphere Shot", "Invisible Shot"],
                #     "stats": [(1, ...), (10, ...), ...]
                # },
            ]

            # Add players and their data
            for player in sample_players:
                player_id = add_player(cursor, player["name"], player["location"], player["starting_team"])
                add_key_techniques(cursor, player_id, player["key_techniques"])
                add_player_stats(cursor, player_id, player["stats"])

            db.commit()
            print("Besaid Aurochs players have been added to the database.")

    # Close the cursor and the connection
    cursor.close()
    db.close()
