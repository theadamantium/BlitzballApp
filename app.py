from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# Database connection function
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",       # Replace with your MySQL username
        password="tK9NdHocRAHyr8xasKBm",   # Replace with your MySQL password
        database="blitzball_db"
    )
    return connection

# Route for the home page (player search, filtering, and team builder)
@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Retrieve players and their statistics
    cursor.execute("""
        SELECT players.player_id, players.name, players.key_techniques, players.location, players.starting_team,
               GROUP_CONCAT(CONCAT(player_stats.level, ': ', 'HP: ', player_stats.hp, ', SP: ', player_stats.speed, 
                                  ', EN: ', player_stats.endurance, ', AT: ', player_stats.attack, 
                                  ', PA: ', player_stats.pass, ', BL: ', player_stats.block, 
                                  ', SH: ', player_stats.shot, ', CA: ', player_stats.catch) 
                           ORDER BY player_stats.level ASC SEPARATOR ' | ') AS stats
        FROM players
        LEFT JOIN player_stats ON players.player_id = player_stats.player_id
        GROUP BY players.player_id
    """)
    players = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('home.html', players=players)

# Route for the edit player page
@app.route('/edit_player', methods=['GET', 'POST'])
def edit_player():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Handle form submission to add/edit player
        player_id = request.form.get('player_id')
        name = request.form['name']
        key_techniques = request.form['key_techniques']
        location = request.form['location']
        starting_team = request.form['starting_team']

        if player_id:
            # Update existing player
            cursor.execute("""
                UPDATE players 
                SET name = %s, key_techniques = %s, location = %s, starting_team = %s
                WHERE player_id = %s
            """, (name, key_techniques, location, starting_team, player_id))
        else:
            # Insert new player
            cursor.execute("""
                INSERT INTO players (name, key_techniques, location, starting_team)
                VALUES (%s, %s, %s, %s)
            """, (name, key_techniques, location, starting_team))
            player_id = cursor.lastrowid

        # Handle player statistics
        stats = request.form.getlist('stats[]')
        levels = request.form.getlist('levels[]')

        for i in range(len(levels)):
            if stats[i]:
                level = int(levels[i])
                stat_values = [int(value) if value else None for value in stats[i].split(',')]
                cursor.execute("""
                    INSERT INTO player_stats (player_id, level, hp, speed, endurance, attack, pass, block, shot, catch)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    hp = VALUES(hp), speed = VALUES(speed), endurance = VALUES(endurance),
                    attack = VALUES(attack), pass = VALUES(pass), block = VALUES(block),
                    shot = VALUES(shot), catch = VALUES(catch)
                """, [player_id, level] + stat_values)

        conn.commit()
        return redirect('/')

    cursor.close()
    conn.close()
    return render_template('edit_player.html')

# Route for the analysis page
@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

if __name__ == '__main__':
    app.run(debug=True)
