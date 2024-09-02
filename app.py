from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import config  # Import the config file to access credentials

app = Flask(__name__)

# Database connection function
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user=config.DB_USER,       # MySQL username from config file
        password=config.DB_PASSWORD,  # MySQL password from config file
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
               player_stats.level, player_stats.hp, player_stats.speed, player_stats.endurance, player_stats.attack,
               player_stats.pass, player_stats.block, player_stats.shot, player_stats.catch
        FROM players
        LEFT JOIN player_stats ON players.player_id = player_stats.player_id
        ORDER BY players.player_id, player_stats.level
    """)
    players_raw = cursor.fetchall()

    # Preparing data structure for stats_table
    players = {}
    for player in players_raw:
        player_id = player['player_id']
        if player_id not in players:
            # Initialize the player's data
            players[player_id] = {
                'player_id': player_id,
                'name': player['name'],
                # 'key_techniques': player['key_techniques'],
                'location': player['location'],
                'starting_team': player['starting_team'],
                'stats_dict': {
                    'HP': {lvl: '' for lvl in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]},
                    'SP': {lvl: '' for lvl in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]},
                    'EN': {lvl: '' for lvl in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]},
                    'AT': {lvl: '' for lvl in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]},
                    'PA': {lvl: '' for lvl in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]},
                    'BL': {lvl: '' for lvl in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]},
                    'SH': {lvl: '' for lvl in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]},
                    'CA': {lvl: '' for lvl in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]},
                }
            }

        # Fill in the available stats
        if player['level'] in players[player_id]['stats_dict']['HP']:  # Ensure the level exists in the dictionary
            stats_dict = players[player_id]['stats_dict']
            stats_dict['HP'][player['level']] = player['hp'] if player['hp'] is not None else ''
            stats_dict['SP'][player['level']] = player['speed'] if player['speed'] is not None else ''
            stats_dict['EN'][player['level']] = player['endurance'] if player['endurance'] is not None else ''
            stats_dict['AT'][player['level']] = player['attack'] if player['attack'] is not None else ''
            stats_dict['PA'][player['level']] = player['pass'] if player['pass'] is not None else ''
            stats_dict['BL'][player['level']] = player['block'] if player['block'] is not None else ''
            stats_dict['SH'][player['level']] = player['shot'] if player['shot'] is not None else ''
            stats_dict['CA'][player['level']] = player['catch'] if player['catch'] is not None else ''

    cursor.close()
    conn.close()
    return render_template('home.html', players=list(players.values()))  # Convert to list for Jinja2 compatibility

# Route for the edit player page
@app.route('/edit_player', methods=['GET', 'POST'])
def edit_player():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
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

    # Handle GET requests to display forms
    cursor.execute("SELECT player_id, name FROM players")
    players = cursor.fetchall()
    
    return render_template('edit_player.html', players=players)

@app.route('/get_player_data/<int:player_id>', methods=['GET'])
def get_player_data(player_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch player details
    cursor.execute("""
        SELECT player_id, name, key_techniques, location, starting_team
        FROM players
        WHERE player_id = %s
    """, (player_id,))
    player = cursor.fetchone()

    if not player:
        return jsonify({'error': 'Player not found'}), 404

    # Fetch player stats for all levels
    cursor.execute("""
        SELECT level, hp, speed, endurance, attack, pass, block, shot, catch
        FROM player_stats
        WHERE player_id = %s
        ORDER BY level
    """, (player_id,))
    stats = cursor.fetchall()

    # Prepare the stats in the desired format
    stats_list = []
    for stat in stats:
        stats_list.append({
            'level': stat['level'],
            'values': [
                stat['hp'] if stat['hp'] is not None else '',
                stat['speed'] if stat['speed'] is not None else '',
                stat['endurance'] if stat['endurance'] is not None else '',
                stat['attack'] if stat['attack'] is not None else '',
                stat['pass'] if stat['pass'] is not None else '',
                stat['block'] if stat['block'] is not None else '',
                stat['shot'] if stat['shot'] is not None else '',
                stat['catch'] if stat['catch'] is not None else ''
            ]
        })

    # Combine player info with stats
    player_data = {
        'player_id': player['player_id'],
        'name': player['name'],
        'key_techniques': player['key_techniques'],
        'location': player['location'],
        'starting_team': player['starting_team'],
        'stats': stats_list
    }

    cursor.close()
    conn.close()

    return jsonify(player_data)

# Route for the analysis page
@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

if __name__ == '__main__':
    app.run(debug=True)
