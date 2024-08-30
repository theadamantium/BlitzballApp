import mysql.connector

# Establish connection to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",       # Replace with your MySQL username
    password="tK9NdHocRAHyr8xasKBm"    # Replace with your MySQL password
)

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

# Check if "Jassu" exists in the players table
cursor.execute("SELECT COUNT(*) FROM players WHERE name = %s", ("Jassu",))
jassu_exists = cursor.fetchone()[0]

if jassu_exists == 0:
    # Insert sample player "Jassu" and his statistics if he doesn't exist
    cursor.execute("""
        INSERT INTO players (name, key_techniques, location, starting_team)
        VALUES (%s, %s, %s, %s)
    """, ("Jassu", "Wither Tackle, Wither Tackle 2, Nap Tackle 2", "Luca -- Aurochs Locker room", "Besaid Aurochs"))

    jassu_id = cursor.lastrowid

    # Insert sample statistics for "Jassu"
    jassu_stats = [
        (jassu_id, 1, 100, 63, 7, 10, 7, 5, 1, 1),
        (jassu_id, 10, 448, 63, 13, 12, 10, 7, 3, 3),
        (jassu_id, 20, 982, 64, 19, 15, 14, 10, 5, 5),
        (jassu_id, 30, 1672, 64, 24, 18, 18, 13, 7, 7),
        (jassu_id, 40, 2518, 65, 28, 21, 23, 17, 9, 9),
        (jassu_id, 50, 3520, 65, 31, 25, 27, 21, 11, 11),
        (jassu_id, 60, 4678, 66, 34, 29, 32, 25, 13, 13),
        (jassu_id, 70, 5992, 66, 36, 34, 37, 29, 15, 15),
        (jassu_id, 80, 7462, 67, 37, 39, 42, 34, 17, 17),
        (jassu_id, 90, 9088, 67, 37, 45, 47, 39, 19, 19),
        (jassu_id, 99, 9999, 67, 37, 50, 52, 44, 20, 20),
    ]

    cursor.executemany("""
        INSERT INTO player_stats (player_id, level, hp, speed, endurance, attack, pass, block, shot, catch)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, jassu_stats)

    db.commit()
    print("Jassu and his statistics have been added to the database.")

else:
    # Return the count of players in the database if "Jassu" exists
    cursor.execute("SELECT COUNT(*) FROM players")
    player_count = cursor.fetchone()[0]
    print("Jassu already exists in the database. Total number of players: " + str(player_count))

# Close the cursor and the connection
cursor.close()
db.close()