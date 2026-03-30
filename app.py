"""
Kehlosastra - Campus Sports Coordination Platform
Flask backend with SQLite database.
Restricts signups to @sastra.ac.in email addresses.
"""

import os
import sqlite3
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'kehlo-sastra-dev-secret-2024')

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

# ──────────────────────────────────────────────
# Database helpers
# ──────────────────────────────────────────────

def get_db():
    """Open a new database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row   # return rows as dict-like objects
    return conn


def init_db():
    """Create tables if they do not exist."""
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')

    # Games table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            sport               TEXT    NOT NULL,
            date                TEXT    NOT NULL,
            time                TEXT    NOT NULL,
            gender              TEXT    NOT NULL,
            total_players       INTEGER NOT NULL,
            location            TEXT    NOT NULL,
            players_with_creator INTEGER NOT NULL DEFAULT 1,
            created_by          INTEGER NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # GamePlayers table (tracks who joined which game)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_players (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            UNIQUE (game_id, user_id),
            FOREIGN KEY (game_id) REFERENCES games(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# Auth helpers
# ──────────────────────────────────────────────

def is_sastra_email(email: str) -> bool:
    """Return True only for @sastra.ac.in addresses."""
    return email.strip().lower().endswith('@sastra.ac.in')


def logged_in() -> bool:
    """Return True when a user is stored in session."""
    return 'user_id' in session


# ──────────────────────────────────────────────
# Routes – Authentication
# ──────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page – @sastra.ac.in emails only."""
    if logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()

        if not name or not email:
            flash('Name and email are required.', 'error')
            return render_template('register.html')

        if not is_sastra_email(email):
            flash('Only @sastra.ac.in email addresses are allowed.', 'error')
            return render_template('register.html')

        conn = get_db()
        existing = conn.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone()

        if existing:
            conn.close()
            flash('This email is already registered. Please login.', 'error')
            return render_template('register.html')

        conn.execute(
            'INSERT INTO users (name, email) VALUES (?, ?)', (name, email)
        )
        conn.commit()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page – looks up user by email."""
    if logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not is_sastra_email(email):
            flash('Only @sastra.ac.in email addresses are allowed.', 'error')
            return render_template('login.html')

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()
        conn.close()

        if not user:
            flash('Email not found. Please register first.', 'error')
            return render_template('login.html')

        # Store user details in session
        session['user_id']    = user['id']
        session['user_name']  = user['name']
        session['user_email'] = user['email']

        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session and redirect to home."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ──────────────────────────────────────────────
# Routes – Games
# ──────────────────────────────────────────────

@app.route('/')
def index():
    """Home page – show all available games as cards."""
    conn = get_db()
    games = conn.execute('''
        SELECT
            g.*,
            u.name               AS creator_name,
            COUNT(gp.id)         AS players_joined
        FROM games g
        JOIN  users u        ON g.created_by = u.id
        LEFT JOIN game_players gp ON g.id    = gp.game_id
        GROUP BY g.id
        ORDER BY g.date ASC, g.time ASC
    ''').fetchall()
    conn.close()
    return render_template('index.html', games=games)


@app.route('/create')
def create():
    """Render the create-game form (login required)."""
    if not logged_in():
        flash('Please log in to create a game.', 'error')
        return redirect(url_for('login'))
    return render_template('create_game.html')


@app.route('/create_game', methods=['POST'])
def create_game():
    """Handle create-game form submission."""
    if not logged_in():
        flash('Please log in to create a game.', 'error')
        return redirect(url_for('login'))

    sport               = request.form.get('sport', '').strip()
    date                = request.form.get('date', '').strip()
    time                = request.form.get('time', '').strip()
    gender              = request.form.get('gender', '').strip()
    total_players       = request.form.get('total_players', '').strip()
    location            = request.form.get('location', '').strip()
    players_with_creator = request.form.get('players_with_creator', '1').strip()

    # Basic validation
    if not all([sport, date, time, gender, total_players, location]):
        flash('All fields are required.', 'error')
        return redirect(url_for('create'))

    try:
        total_players        = int(total_players)
        players_with_creator = int(players_with_creator)
    except ValueError:
        flash('Player counts must be numbers.', 'error')
        return redirect(url_for('create'))

    if total_players < 2:
        flash('Total players must be at least 2.', 'error')
        return redirect(url_for('create'))

    if players_with_creator < 1:
        players_with_creator = 1

    if players_with_creator >= total_players:
        flash('Players already with you must be less than the total players required.', 'error')
        return redirect(url_for('create'))

    conn = get_db()
    cur  = conn.cursor()

    # Insert the new game
    cur.execute('''
        INSERT INTO games
            (sport, date, time, gender, total_players, location, players_with_creator, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (sport, date, time, gender, total_players, location,
          players_with_creator, session['user_id']))

    game_id = cur.lastrowid

    # Creator automatically joins as first player
    cur.execute(
        'INSERT OR IGNORE INTO game_players (game_id, user_id) VALUES (?, ?)',
        (game_id, session['user_id'])
    )

    conn.commit()
    conn.close()

    flash('Game created successfully!', 'success')
    return redirect(url_for('game_details', id=game_id))


@app.route('/game/<int:id>')
def game_details(id):
    """Show details of a single game and the list of joined players."""
    conn = get_db()

    game = conn.execute('''
        SELECT
            g.*,
            u.name       AS creator_name,
            COUNT(gp.id) AS players_joined
        FROM games g
        JOIN  users u        ON g.created_by = u.id
        LEFT JOIN game_players gp ON g.id    = gp.game_id
        WHERE g.id = ?
        GROUP BY g.id
    ''', (id,)).fetchone()

    if not game:
        conn.close()
        flash('Game not found.', 'error')
        return redirect(url_for('index'))

    # All players who have joined
    players = conn.execute('''
        SELECT u.name, u.email
        FROM game_players gp
        JOIN users u ON gp.user_id = u.id
        WHERE gp.game_id = ?
        ORDER BY gp.id ASC
    ''', (id,)).fetchall()

    # Check whether the current user has already joined
    user_joined = False
    if logged_in():
        user_joined = conn.execute(
            'SELECT 1 FROM game_players WHERE game_id = ? AND user_id = ?',
            (id, session['user_id'])
        ).fetchone() is not None

    conn.close()
    return render_template(
        'game_details.html',
        game=game,
        players=players,
        user_joined=user_joined
    )


@app.route('/join/<int:id>', methods=['POST'])
def join_game(id):
    """Add the current user to a game (if slots remain)."""
    if not logged_in():
        flash('Please log in to join a game.', 'error')
        return redirect(url_for('login'))

    conn = get_db()

    game = conn.execute('''
        SELECT g.*, COUNT(gp.id) AS players_joined
        FROM games g
        LEFT JOIN game_players gp ON g.id = gp.game_id
        WHERE g.id = ?
        GROUP BY g.id
    ''', (id,)).fetchone()

    if not game:
        conn.close()
        flash('Game not found.', 'error')
        return redirect(url_for('index'))

    # Check if user already joined (before the full check so returning
    # members get a clear message even when the game is now full)
    already = conn.execute(
        'SELECT 1 FROM game_players WHERE game_id = ? AND user_id = ?',
        (id, session['user_id'])
    ).fetchone()

    if already:
        conn.close()
        flash('You have already joined this game!', 'warning')
        return redirect(url_for('game_details', id=id))

    # Check if game is full
    if game['players_joined'] >= game['total_players']:
        conn.close()
        flash('Sorry, this game is already full!', 'error')
        return redirect(url_for('game_details', id=id))

    conn.execute(
        'INSERT INTO game_players (game_id, user_id) VALUES (?, ?)',
        (id, session['user_id'])
    )
    conn.commit()
    conn.close()

    flash('You have successfully joined the game!', 'success')
    return redirect(url_for('game_details', id=id))


# ──────────────────────────────────────────────
# App entry point
# ──────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    # Debug mode is controlled by the FLASK_DEBUG environment variable.
    # Never enable debug=True in production deployments.
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug)
