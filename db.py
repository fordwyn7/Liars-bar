import sqlite3
import asyncio
import random
import re
from config import bot, dp
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from keyboards.keyboard import get_main_menu
from datetime import datetime, timezone, timedelta


def connect_db():
    return sqlite3.connect("users_database.db")


def is_user_in_tournament_and_active(user_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT tournament_id, user_status FROM tournament_users WHERE user_id = ?",
        (user_id,),
    )
    tournament_data = cursor.fetchone()
    if not tournament_data:
        conn.close()
        return False
    tournament_id, user_status = tournament_data
    if user_status != "alive":
        conn.close()
        return False

    cursor.execute(
        "SELECT tournament_start_time, tournament_end_time FROM tournaments_table WHERE tournament_id = ?",
        (tournament_id,),
    )
    tournament = cursor.fetchone()

    if not tournament:
        conn.close()
        return False

    tournament_start, tournament_end = tournament
    uzbekistan_tz = timezone(timedelta(hours=5))
    try:
        tournament_start = datetime.strptime(
            tournament_start, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=uzbekistan_tz)
    except ValueError:
        tournament_start = datetime.strptime(
            tournament_start, "%Y-%m-%d %H:%M"
        ).replace(tzinfo=uzbekistan_tz)
    try:
        tournament_end = datetime.strptime(tournament_end, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=uzbekistan_tz
        )
    except ValueError:
        tournament_end = datetime.strptime(tournament_end, "%Y-%m-%d %H:%M").replace(
            tzinfo=uzbekistan_tz
        )
    current_time = datetime.now(uzbekistan_tz)

    # Compare the timezone-aware datetimes
    if tournament_start <= current_time <= tournament_end:
        conn.close()
        return True

    conn.close()
    return False


def register_user(user_id, username, first_name, last_name, preferred_name):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO users_database (user_id, username, first_name, last_name, nfgame, registration_date)
                VALUES (?, ?, ?, ?, ?, datetime('now',  '+5 hours'))
                """,
                (user_id, username, first_name, last_name, preferred_name),
            )
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error registering user: {e}")


def is_user_registered(user_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users_database WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
        return user
    except sqlite3.Error as e:
        print(f"Error checking if user is registered: {e}")
        return None


def add_admin(user_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_alive_number(game_id):
    players = get_all_players_in_game(game_id)
    alive = []
    for i in players:
        if not i or is_player_dead(game_id, i):
            continue
        alive.append(i)
    if len(alive) == 1:
        return alive[0]
    return 0


def get_game_inviter_id(game_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT inviter_id FROM invitations WHERE game_id = ?", (game_id,)
            )
            inviter_id = cursor.fetchone()
        return inviter_id[0] if inviter_id else None
    except sqlite3.Error as e:
        print(f"Error retrieving inviter ID: {e}")
        return None


def insert_invitation(inviter_id, invitee_id, game_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invitations (inviter_id, invitee_id, game_id)
                VALUES (?, ?, ?)
                """,
                (inviter_id, invitee_id, game_id),
            )
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting invitation: {e}")


def get_player_count(game_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM invitations WHERE game_id = ?", (game_id,)
            )
            player_count = cursor.fetchone()[0]
        return player_count
    except sqlite3.Error as e:
        print(f"Error getting player count: {e}")
        return 0


def is_user_in_game(game_id, user_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT invitee_id FROM invitations WHERE game_id = ? AND invitee_id = ?",
                (game_id, user_id),
            )
            result = cursor.fetchone()
        return result is not None
    except sqlite3.Error as e:
        print(f"Error checking if user is in game: {e}")
        return False


def get_user_nfgame(user_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nfgame FROM users_database WHERE user_id = ?", (user_id,)
            )
            result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Error retrieving user 'nfgame': {e}")
        return None


def has_incomplete_games(user_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT game_id FROM invitations WHERE inviter_id = ? AND invitee_id IS NULL",
                (user_id,),
            )
            creator_game = cursor.fetchone()

            cursor.execute(
                "SELECT game_id FROM invitations WHERE invitee_id = ?", (user_id,)
            )
            participant_game = cursor.fetchone()

        return bool(creator_game or participant_game)
    except sqlite3.Error as e:
        print(f"Error checking incomplete games: {e}")
        return False


def delete_user_from_all_games(user_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM invitations WHERE inviter_id = ? AND invitee_id IS NULL",
                (user_id,),
            )
            cursor.execute("DELETE FROM invitations WHERE invitee_id = ?", (user_id,))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting user from games: {e}")


def delete_invitation(invitee_id, game_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM invitations
                WHERE invitee_id = ? AND game_id = ?
                """,
                (invitee_id, game_id),
            )
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting invitation: {e}")


def get_all_players_in_game(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT inviter_id, invitee_id
            FROM invitations
            WHERE game_id = ?
            """,
            (game_id,),
        )
        result = cursor.fetchall()
        players = {row[0] for row in result} | {row[1] for row in result}
        players = list(players)
        for i in players:
            if not i or is_player_dead(game_id, i):
                players.remove(i)
        return players


def delete_game(game_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invitations WHERE game_id = ?", (game_id,))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting game: {e}")


def get_games_by_user(user_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT game_id, inviter_id FROM invitations WHERE invitee_id = ? OR inviter_id = ?",
                (
                    user_id,
                    user_id,
                ),
            )
            games = cursor.fetchall()
        return [{"game_id": game[0], "creator_id": game[1]} for game in games]
    except sqlite3.Error as e:
        print(f"Error getting games for user {user_id}: {e}")
        return []


def get_game_id_by_user(user_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT game_id FROM invitations WHERE inviter_id = ?", (user_id,)
        )
        game_id = cursor.fetchone()
        if game_id:
            return game_id[0]
        cursor.execute(
            "SELECT game_id FROM invitations WHERE invitee_id = ?", (user_id,)
        )
        game_id = cursor.fetchone()
        if game_id:
            return game_id[0]
    return None


def get_id_by_nfgame(nfgame):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users_database WHERE nfgame = ?", (nfgame,))
        result = cursor.fetchone()
        if result:
            return result[0]
    return None


def get_needed_players(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT needed_players
            FROM invitations
            WHERE game_id = ? AND inviter_id IS NOT NULL
            LIMIT 1
            """,
            (game_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else 0


def get_game_creator_id(game_id):
    """Fetch the creator's user ID for a specific game."""
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT inviter_id 
            FROM invitations 
            WHERE game_id = ?
            LIMIT 1
        """,
            (game_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else None


async def send_message_to_all_players(game_id, message):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT invitee_id FROM invitations WHERE game_id = ? AND invitee_id IS NOT NULL",
            (game_id,),
        )
        players = cursor.fetchall()
        cr_id = get_game_creator_id(game_id)
        if not cr_id in players:
            players.append((cr_id,))
        for player in players:
            player_id = player[0]
            if not player_id or is_player_dead(game_id, player_id):
                continue
            try:
                msg = await bot.send_message(player_id, message)
                await save_message(player_id, game_id, msg.message_id)
            except Exception as e:
                print(f"Failed to send message to player {player_id}: {e}")


def set_game_started(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE invitations SET is_started = 1 WHERE game_id = ?", (game_id,)
        )
        conn.commit()


def is_game_started(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_started FROM invitations WHERE game_id = ?", (game_id,)
        )
        result = cursor.fetchone()
        return result[0] == 1 if result else False


def mark_game_as_started(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE invitations SET is_started = 1 WHERE game_id = ?", (game_id,)
        )
        conn.commit()


def is_name_valid(name):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users_database WHERE nfgame = ?", (name,))
    if cursor.fetchone()[0] > 0:
        return 2
    if len(name) > 30 or len(name) < 1:
        return 0
    if re.match(r"^[a-zA-Z0-9_]+$", name[1:]) and name[0] == "@":
        return 1
    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        return 0
    return 1


def get_all_players_nfgame(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.nfgame 
            FROM users_database u
            INNER JOIN invitations i ON u.user_id = i.invitee_id
            WHERE i.game_id = ?
        """,
            (game_id,),
        )
        s = []
        for row in cursor.fetchall():
            s.append(row[0])
        cr_name = get_user_nfgame(get_game_creator_id(game_id))
        if not cr_name in s:
            s.append(cr_name)
        return s


def ensure_column_exists():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(invitations);")
        columns = cursor.fetchall()
        if not any(column[1] == "current_turn_user_id" for column in columns):
            cursor.execute(
                "ALTER TABLE invitations ADD COLUMN current_turn_user_id INTEGER;"
            )
            conn.commit()


def set_current_turn(game_id, user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE invitations SET current_turn_user_id = ? WHERE game_id = ?",
            (user_id, game_id),
        )
        conn.commit()


def insert_number_of_cards(game_id, number_of_cards):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE invitations
            SET number_of_cards = ?
            WHERE game_id = ?
            """,
            (number_of_cards, game_id),
        )

        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO invitations (game_id, number_of_cards)
                VALUES (?, ?)
                """,
                (game_id, number_of_cards),
            )

        conn.commit()


def set_current_table(game_id, current_table):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(game_state)")
        columns = [row[1] for row in cursor.fetchall()]
        if "current_table" not in columns:
            cursor.execute(
                """
                ALTER TABLE game_state
                ADD COLUMN current_table TEXT
                """
            )
            conn.commit()

        cursor.execute(
            """
            INSERT OR IGNORE INTO game_state (game_id)
            VALUES (?)
            """,
            (game_id,),
        )

        cursor.execute(
            """
            UPDATE game_state
            SET current_table = ?
            WHERE game_id = ?
            """,
            (current_table, game_id),
        )
        conn.commit()

    return current_table


def get_current_table(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(game_state)")
        columns = [row[1] for row in cursor.fetchall()]
        if "current_table" not in columns:
            raise ValueError(
                "The 'current_table' column does not exist in the game_state table."
            )
        cursor.execute(
            """
            SELECT current_table
            FROM game_state
            WHERE game_id = ?
            """,
            (game_id,),
        )
        result = cursor.fetchone()
        if result is None:
            print(f"No entry found for game_id: {game_id}.")
        elif result[0] is None:
            print(f"'current_table' is not set for game_id: {game_id}.")
        return result[0] if result else None


async def periodically_edit_message(
    chat_id,
    message_id,
    s_message_id,
    lent,
    cur_table,
    interval,
):
    try:
        seconds = ["2️⃣", "1️⃣"]
        for i in range(2):
            new_text = seconds[i]
            await bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=new_text
            )
            await asyncio.sleep(interval)

        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        await bot.delete_message(chat_id=chat_id, message_id=s_message_id)
        if lent == 2:
            number = 19
        elif lent == 3:
            number = 23
        else:
            number = 27
        game_id = get_game_id_by_user(chat_id)
        insert_number_of_cards(game_id, number)
        mark_game_as_started(game_id)
        massiv = get_all_players_nfgame(game_id)
        s = ""
        rang = ["🔴", "🟠", "🟡", "🟢", "⚪️"]
        for row in range(len(massiv)):
            s += rang[row] + " " + massiv[row] + "\n"
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"Game has started. 🚀🚀🚀\n"
                f"There are {number} cards in the game.\n"
                f"{number//4} hearts — ♥️\n"
                f"{number//4} diamonds — ♦️\n"
                f"{number//4} spades — ♠️\n"
                f"{number//4} clubs — ♣️\n"
                f"2 universals — 🎴\n"
                f"1 Joker — 🃏\n\n"
                f"Players in the game: \n{s}\n"
                f"Current table for cards: {cur_table}\n\n"
            ),
        )
    except Exception as e:
        await bot.send_message(
            chat_id,
            f"Something went wrong. Plase try again.",
            reply_markup=get_main_menu(chat_id),
        )
        print(f"An error occurred: {e}")


def get_number_of_cards(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT number_of_cards 
            FROM invitations 
            WHERE game_id = ?
            """,
            (game_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else 0


def generate_random_cards(deck):
    random_cards = random.sample(deck, 5)
    for card in random_cards:
        deck.remove(card)
    return random_cards


def delete_all_players_cards(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM game_state
            WHERE game_id = ?
        """,
            (game_id,),
        )
        conn.commit()
    print(f"Cleared all cards for game {game_id}")


def create_cards(game_id):
    nm = get_number_of_cards(game_id)
    cards = ["❤️", "♦️", "♠️", "♣️"]
    deck = cards * (nm // 4)
    deck.append("🃏")
    deck.append("🎴")
    deck.append("🎴")
    return deck


def save_player_cards(game_id):
    players = get_all_players_in_game(game_id)
    if not players:
        print("No players found for this game.")
        return
    players = [
        player for player in players if player and not is_player_dead(game_id, player)
    ]

    deck = create_cards(game_id)
    if len(deck) < len(players) * 5:
        print("Not enough cards remaining in the deck for all players.")
        return
    player_cards = {player: generate_random_cards(deck) for player in players}
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        for player, cards in player_cards.items():
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM game_state
                WHERE game_id = ? AND player_id = ?
                """,
                (game_id, player),
            )
            exists = cursor.fetchone()[0] > 0

            if exists:
                cursor.execute(
                    """
                    UPDATE game_state
                    SET cards = ?
                    WHERE game_id = ? AND player_id = ?
                    """,
                    (",".join(cards), game_id, player),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO game_state (game_id, player_id, cards)
                    VALUES (?, ?, ?)
                    """,
                    (game_id, player, ",".join(cards)),
                )
        conn.commit()

    print(f"Cards saved for game {game_id}: {player_cards}")


def set_real_bullet_for_player(game_id, player_id):
    cards = ["blank"] * 5 + ["real"]
    random.shuffle(cards)
    real_bullet = cards.index("real")

    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA table_info(game_state)")
            columns = [row[1] for row in cursor.fetchall()]

            if "player_id" not in columns:
                cursor.execute(
                    """
                    ALTER TABLE game_state
                    ADD COLUMN player_id TEXT
                    """
                )
                conn.commit()
                print("Added 'player_id' column to game_state table.")

            if "real_bullet" not in columns:
                cursor.execute(
                    """
                    ALTER TABLE game_state
                    ADD COLUMN real_bullet INTEGER
                    """
                )
                conn.commit()
                print("Added 'real_bullet' column to game_state table.")

            if "blanks_count" not in columns:
                cursor.execute(
                    """
                    ALTER TABLE game_state
                    ADD COLUMN blanks_count INTEGER DEFAULT 0
                    """
                )
                conn.commit()
                print("Added 'blanks_count' column to game_state table.")
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM game_state
                WHERE game_id = ? AND player_id = ?
                """,
                (game_id, player_id),
            )
            exists = cursor.fetchone()[0] > 0

            if exists:
                cursor.execute(
                    """
                    UPDATE game_state
                    SET real_bullet = ?, blanks_count = 0
                    WHERE game_id = ? AND player_id = ?
                    """,
                    (real_bullet, game_id, player_id),
                )
            else:
                # Insert new record
                cursor.execute(
                    """
                    INSERT INTO game_state (game_id, player_id, real_bullet, blanks_count)
                    VALUES (?, ?, ?, 0)
                    """,
                    (game_id, player_id, real_bullet),
                )
            conn.commit()
            print(
                f"Set 'real_bullet' for player {player_id} in game {game_id} to {real_bullet}."
            )
            return real_bullet

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return None


def ensure_life_status_column():
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(game_state)")
        columns = [row[1] for row in cursor.fetchall()]
        if "life_status" not in columns:
            cursor.execute(
                """
                ALTER TABLE game_state
                ADD COLUMN life_status TEXT DEFAULT 'alive'
                """
            )
            conn.commit()


def is_player_dead(game_id, player_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT life_status
            FROM game_state
            WHERE game_id = ? AND player_id = ?
            """,
            (game_id, player_id),
        )
        result = cursor.fetchone()
        if result and result[0] == "dead":
            return True
    return False


def set_user_status(user_id, status):
    if is_user_in_tournament_and_active(user_id):
        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tournament_users SET user_status = ? WHERE user_id = ?",
            (status, user_id),
        )
        conn.commit()
        conn.close()


async def shoot_self(game_id, player_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT real_bullet, blanks_count
            FROM game_state
            WHERE game_id = ? AND player_id = ?
            """,
            (game_id, player_id),
        )
        result = cursor.fetchone()
        if result is None:
            return None

        real_bullet_position, blanks_count = result
        if int(blanks_count) == int(real_bullet_position):
            if is_user_turn(player_id, game_id):
                update_current_turn(game_id)
            cursor.execute(
                """
                UPDATE game_state
                SET life_status = 'dead'
                WHERE game_id = ? AND player_id = ?
                """,
                (game_id, player_id),
            )
            conn.commit()
            if get_tournament_id_by_user(player_id) and is_user_in_tournament(
                get_tournament_id_by_user(player_id), player_id
            ):
                set_user_status(player_id, "died")
            return True
        else:
            blanks_count += 1
            cursor.execute(
                """
                UPDATE game_state
                SET blanks_count = ?
                WHERE game_id = ? AND player_id = ?
                """,
                (blanks_count, game_id, player_id),
            )
            conn.commit()
            elimination_chance = blanks_count
            return elimination_chance


def is_user_turn(user_id, game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT current_turn_user_id FROM invitations WHERE game_id = ?",
            (game_id,),
        )
        result = cursor.fetchone()
        return result[0] == user_id if result else False


def update_current_turn(game_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        players = get_all_players_in_game(game_id)
        cursor.execute(
            "SELECT current_turn_user_id FROM invitations WHERE game_id = ?", (game_id,)
        )
        current_turn = cursor.fetchone()
        if not current_turn or len(players) == 0:
            print("erooooooooooooooooooooooooooooooooooooooooooooor")
            return
        next_index = (players.index(current_turn[0]) + 1) % len(players)
        next_turn = players[next_index]
        cursor.execute(
            "UPDATE invitations SET current_turn_user_id = ? WHERE game_id = ?",
            (next_turn, game_id),
        )
        conn.commit()


def get_player_status(game_id, player_id):
    with sqlite3.connect("users_database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT life_status
            FROM game_state
            WHERE game_id = ? AND player_id = ?
            """,
            (game_id, player_id),
        )
        result = cursor.fetchone()
        if result:
            return result[0]
    return "alive"


def get_total_users():
    try:
        with sqlite3.connect("users_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users_database")
            total_users = cursor.fetchone()[0]
            return total_users
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return 0


async def save_message(user_id, game_id, message_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO user_game_messages (user_id, game_id, message_id)
            VALUES (?, ?, ?)
            """,
            (user_id, game_id, message_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


async def delete_all_game_messages(game_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT user_id, message_id FROM user_game_messages WHERE game_id = ?
            """,
            (game_id,),
        )
        rows = cursor.fetchall()
        for row in rows:
            user_id, message_id = row
            try:
                await bot.delete_message(chat_id=user_id, message_id=message_id)
            except Exception as e:
                print(f"Error deleting message {message_id} for user {user_id}: {e}")
        cursor.execute(
            """
            DELETE FROM user_game_messages WHERE game_id = ?
            """,
            (game_id,),
        )
        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


async def delete_user_messages(game_id, userid):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT user_id, message_id FROM user_game_messages WHERE game_id = ?
            """,
            (game_id,),
        )
        rows = cursor.fetchall()
        for row in rows:
            user_id, message_id = row
            if user_id == userid:
                try:
                    await bot.delete_message(chat_id=user_id, message_id=message_id)
                except Exception as e:
                    print(
                        f"Error deleting message {message_id} for user {user_id}: {e}"
                    )
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def get_all_user_ids():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM users_database")
        user_ids = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
        user_ids = []
    finally:
        conn.close()
    return user_ids



    return stats_message


def create_game_record_if_not_exists(game_id: str, user_id: int):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        try:
            start_time = (datetime.now() + timedelta(hours=5)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except ValueError:
            start_time = (datetime.now() + timedelta(hours=5)).strftime(
                "%Y-%m-%d %H:%M"
            )

        cursor.execute(
            """
            INSERT INTO game_archive (game_id, user_id, game_start_time)
            VALUES (?, ?, ?)
            """,
            (game_id, user_id, start_time),
        )
        conn.commit()
        print(f"Game record created for {user_id}, game_id: {game_id}")
    except sqlite3.Error as e:
        print(f"❌ Database error occurred while creating game record: {e}")
    finally:
        conn.close()


def update_game_details(game_id: str, user_id: int, winner: str):
    try:
        end_time = (datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        end_time = (datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M")
    try:
        conn = sqlite3.connect("users_database.db")
        cursor = conn.cursor()

        if not winner:
            winner = "Game had not been finished"

        cursor.execute(
            """
            UPDATE game_archive 
            SET game_end_time = ?, game_winner = ?
            WHERE game_id = ? AND user_id = ?
            """,
            (end_time, winner, game_id, user_id),
        )

        conn.commit()
        if cursor.rowcount == 0:
            print("❌ Failed to update game details for ID '{game_id}'.")
            return f"❌ Failed to update game details for ID '{game_id}'."

        print(f"Game details updated for {user_id}, game_id: {game_id}")
        return "Game details updated successfully."

    except sqlite3.Error as e:
        print("❌ Database error occurred: {e}")
        return f"❌ Database error occurred: {e}"
    finally:
        conn.close()


def get_upcoming_tournaments():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, tournament_id, tournament_prize, tournament_start_time, tournament_end_time 
            FROM tournaments_table
            WHERE tournament_start_time > datetime('now',  '+5 hours')
            """
        )
        tournaments = [
            {
                "id": row[0],
                "name": row[1],
                "prize": row[2],
                "start_time": row[3],
                "end_time": row[4]
            }
            for row in cursor.fetchall()
        ]
        return tournaments
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return []
    finally:
        conn.close()


def get_tournament_id_by_user(user_id: int):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT tournament_id
            FROM tournament_rounds_users
            WHERE round_user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

import sqlite3
from datetime import datetime, timedelta

def set_tournament_end_time(tournament_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        end_time = datetime.now(timezone.utc) + timedelta(hours=5)
        formatted_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            UPDATE tournaments_table
            SET tournament_end_time = ?
            WHERE tournament_id = ?
            """,
            (formatted_time, tournament_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

def get_tournament_archive():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, tournament_prize, tournament_winner, tournament_start_time, tournament_end_time
            FROM tournaments_table
            WHERE tournament_end_time <= datetime('now',  '+5 hours')
            """
        )
        tournaments = [
            {
                "id": row[0],
                "prize": row[1],
                "winner": row[2],
                "start_time": row[3],
                "end_time": row[4],
            }
            for row in cursor.fetchall()
        ]
        return tournaments
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return []
    finally:
        conn.close()


def is_user_in_tournament(tournament_id: str, user_id: int) -> bool:
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 1 FROM tournament_users
            WHERE tournament_id = ? AND user_id = ?
            """,
            (tournament_id, user_id),
        )
        result = cursor.fetchone()
        return result is not None
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        conn.close()


def add_user_to_tournament(tournament_id: str, user_id: int):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tournament_users (tournament_id, user_id)
            VALUES (?, ?)
            """,
            (tournament_id, user_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        raise
    finally:
        conn.close()


def get_current_players(tournament_id: str) -> int:
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM tournament_users
            WHERE tournament_id = ?
            """,
            (tournament_id,),
        )
        current_players = cursor.fetchone()[0]
        return current_players
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return 0
    finally:
        conn.close()

import sqlite3

def get_tournament_users_list(tournament_id: str) -> list:
    """Fetch a list of user IDs participating in a tournament."""
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT user_id 
            FROM tournament_users
            WHERE tournament_id = ?
            """,
            (tournament_id,),
        )
        users = [row[0] for row in cursor.fetchall()]
        return users
    
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return []
    
    finally:
        conn.close()


def delete_tournament(tournament_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT user_id FROM tournament_users WHERE tournament_id = ?",
            (tournament_id,),
        )
        users = cursor.fetchall()

        for user in users:
            user_id = user[0]
            delete_user_from_all_games(user_id)

        cursor.execute(
            "DELETE FROM tournament_users WHERE tournament_id = ?", (tournament_id,)
        )
        cursor.execute(
            "DELETE FROM tournaments_table WHERE tournament_id = ?", (tournament_id,)
        )

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def get_ongoing_tournaments():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT t.id, t.tournament_id, t.tournament_prize, t.tournament_start_time, t.tournament_end_time, 
                   (SELECT COUNT(*) FROM tournament_users tu WHERE tu.tournament_id = t.tournament_id) AS current_players
            FROM tournaments_table t
            WHERE t.tournament_start_time <= datetime('now', '+5 hours') 
              AND t.tournament_end_time >= datetime('now',  '+5 hours')
            """
        )
        tournaments = [
            {
                "id": row[0],
                "name": row[1],
                "prize": row[2],
                "start_time": row[3],
                "end_time": row[4],
            }
            for row in cursor.fetchall()
        ]
        return tournaments
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return []
    finally:
        conn.close()


def determine_round_winners(tournament_id, round_number):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT round_winner
            FROM tournament_rounds_users
            WHERE tournament_id = ? AND round_number = ?
            """,
            (tournament_id, round_number),
        )
        winners = cursor.fetchall()
        if winners:
            winners_ids = list(set([winner[0] for winner in winners if winner]))
            return winners_ids
        else:
            print(
                f"No winners found for round {round_number} in tournament {tournament_id}."
            )
            return []
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()


def save_tournament_round_info(
    tournament_id: str, round_number: str, round_user_id: str, group_number: str
):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tournament_rounds_users (tournament_id, round_number, round_user_id, group_number, round_winner)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (tournament_id, round_number, round_user_id, group_number),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


async def save_round_winner(tournament_id: str, round_user_id, round_winner):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT round_number, group_number
            FROM tournament_rounds_users
            WHERE tournament_id = ? AND round_user_id = ?
            ORDER BY round_number DESC
            LIMIT 1
            """,
            (tournament_id, round_user_id),
        )
        result = cursor.fetchone()
        if result:
            round_number, group_number = result
            # await bot.send_message(chat_id=1155076760, text=f"rn: {round_number}\ngn: {group_number}")
            group_number = int(group_number)
            cursor.execute(
                """
                UPDATE tournament_rounds_users
                SET round_winner = ?
                WHERE tournament_id = ? AND round_number = ? AND group_number = ?
                """,
                (round_winner, tournament_id, round_number, group_number),
            )
            conn.commit()
        else:
            print("Round and group not found for the given user.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def get_current_round_number(tournament_id: str) -> str:
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT round_number
            FROM tournament_rounds_users
            WHERE tournament_id = ?
            ORDER BY CAST(round_number AS INTEGER) DESC
            LIMIT 1
            """,
            (tournament_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else "0"
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "0"
    finally:
        conn.close()


def get_number_of_winners(tournament_id: str, round_number: str) -> int:
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(DISTINCT round_winner)
            FROM tournament_rounds_users
            WHERE tournament_id = ? AND round_number = ? AND round_winner IS NOT NULL
            """,
            (tournament_id, round_number),
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0
    finally:
        conn.close()


def get_all_users_in_tournament(tournament_id: str) -> list:
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT user_id
            FROM tournament_users
            WHERE tournament_id = ?
            """,
            (tournament_id,),
        )
        result = cursor.fetchall()
        return len(result)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()


async def notify_round_results(tournament_id: str, round_number: str):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT DISTINCT group_number, round_winner
            FROM tournament_rounds_users
            WHERE tournament_id = ? AND round_number = ?
            """,
            (tournament_id, round_number),
        )
        group_results = cursor.fetchall()
        if not group_results:
            return f"No results found for round {round_number} in tournament {tournament_id}."

        results_message = f"🏆 Round {round_number} Results 🏆\n"
        unique_groups = set()
        for group_number, winner_id in group_results:
            if group_number not in unique_groups:
                unique_groups.add(group_number)
                if winner_id:
                    results_message += f"| - Winner from Group {group_number}: {get_user_nfgame(winner_id)} (ID: {winner_id})\n"
                else:
                    results_message += f"| - Group {group_number}: No winner yet\n"

        cursor.execute(
            """
            SELECT user_id
            FROM tournament_users
            WHERE tournament_id = ?
            """,
            (tournament_id,),
        )
        all_users = cursor.fetchall()
        user_ids = [row[0] for row in all_users]
        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=results_message,
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Failed to send message to user {user_id}: {e}")

        return f"Round {round_number} results sent to all players in tournament {tournament_id}."

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return f"Error fetching round results for tournament {tournament_id}."
    finally:
        conn.close()


def get_number_of_players_in_round(tournament_id: str, round_number: str):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        # Count the number of players in the specific round
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM tournament_rounds_users
            WHERE tournament_id = ? AND round_number = ?
            """,
            (tournament_id, round_number),
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0
    finally:
        conn.close()


def get_number_of_groups_in_round(tournament_id: str, round_number: str):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(DISTINCT group_number)
            FROM tournament_rounds_users
            WHERE tournament_id = ? AND round_number = ?
            """,
            (tournament_id, round_number),
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0
    finally:
        conn.close()


def delete_tournament_from_tables(tournament_id: str):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        # cursor.execute(
        #     "DELETE FROM tournaments_table WHERE tournament_id = ?",
        #     (tournament_id,),
        # )
        cursor.execute(
            "DELETE FROM tournament_users WHERE tournament_id = ?",
            (tournament_id,),
        )
        cursor.execute(
            "DELETE FROM tournament_rounds_users WHERE tournament_id = ?",
            (tournament_id,),
        )
        conn.commit()
        print(f"Tournament with ID {tournament_id} has been deleted.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


async def update_tournament_winner_if_round_finished(
    tournament_id: str, round_number: str
):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(DISTINCT group_number)
            FROM tournament_rounds_users
            WHERE tournament_id = ? AND round_number = ?
            """,
            (tournament_id, round_number),
        )
        result = cursor.fetchone()
        if result and result[0] == 1:
            cursor.execute(
                """
                SELECT round_winner
                FROM tournament_rounds_users
                WHERE tournament_id = ? AND round_number = ? AND group_number = '1'
                LIMIT 1
                """,
                (tournament_id, round_number),
            )
            winner_result = cursor.fetchone()
            if winner_result:
                winner = winner_result[0]
                cursor.execute(
                    """
                    UPDATE tournaments_table
                    SET tournament_winner = ?
                    WHERE tournament_id = ?
                    """,
                    (winner, tournament_id),
                )
                conn.commit()
                # await bot.send_message(chat_id=1155076760, text=f"winner result: {winner_result}")
                await inform_all_users_tournament_ended(tournament_id, winner)
                print(f"Winner {winner} has been saved to the tournament.")
                return 12
            else:
                print("No winner found for this round.")
        else:
            print(
                "This round has more than one group, winner cannot be determined yet."
            )
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
    return 0


async def inform_all_users_tournament_ended(tournament_id: str, winner_id: int):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT user_id
            FROM tournament_users
            WHERE tournament_id = ?
            """,
            (tournament_id,),
        )
        users = cursor.fetchall()
        winner_name = get_user_nfgame(winner_id)
        message = (
            f"🏁 Tournament Ended! 🏆\n\n"
            f"Thank you for participating in a Tournament 🎮\n\n"
            f"🥇 The Winner is: {winner_name} (ID: {winner_id}) 🎉\n\n"
            f"Congrats to the champion! Stay tuned for more tournaments. 🏅"
        )
        for user in users:
            user_id = user[0]
            try:
                await bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                print(f"Error sending message to {user_id}: {e}")
        set_tournament_end_time(tournament_id)
        delete_tournament_from_tables(tournament_id)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def create_groups(participants):
    random.shuffle(participants)
    groups = []
    # if len(participants) == 4:
    #     groups.append(participants[:2])
    #     groups.append(participants[2:])
    #     return groups
    nmb = len(participants) % 4
    nmd = len(participants) // 4
    if nmb == 0:
        for i in range(0, len(participants), 4):
            groups.append(participants[i : i + 4])
    elif nmb == 1:
        for i in range(0, nmd - 1):
            groups.append(participants[: 4])
            participants = participants[4 :]
        groups.append(participants[:2])
        groups.append(participants[2:])
    else:
        for i in range(0, nmd):
            groups.append(participants[: 4])
            participants = participants[4 :]
        if participants:
            groups.append(participants)
    return groups


def get_users_in_round(tournament_id, round_number):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT DISTINCT round_user_id
            FROM tournament_rounds_users
            WHERE tournament_id = ? AND round_number = ?
            """,
            (tournament_id, round_number),
        )
        users = cursor.fetchall()
        return [int(user[0]) for user in users]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()


def get_round_results(tournament_id, round_number):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT DISTINCT group_number, round_winner
            FROM tournament_rounds_users
            WHERE tournament_id = ? AND round_number = ?
            """,
            (tournament_id, round_number),
        )
        group_results = cursor.fetchall()
        if not group_results:
            return f"No results found for round {round_number} in tournament {tournament_id}."

        results_message = f"🏆 Round {round_number} Results 🏆\n"
        unique_groups = set()
        for group_number, winner_id in group_results:
            if group_number not in unique_groups:
                unique_groups.add(group_number)
                if winner_id:
                    results_message += f"| - Winner from Group {group_number}: {get_user_nfgame(winner_id)} (ID: {winner_id})\n"
                else:
                    results_message += f"| - Group {group_number}: No winner yet\n"
        return results_message
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return f"Error fetching round results for tournament {tournament_id}."
    finally:
        conn.close()


def get_number_of_referrals(user_id):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) 
        FROM users_referral 
        WHERE referred_by = ?
        """,
        (user_id,),
    )

    result = cursor.fetchone()
    return result[0] if result else 0


def generate_referral_link(user_id):
    return f"https://t.me/liarsbar_game_robot?start={user_id}"

def get_top_referrals():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT referred_by, COUNT(*) AS referral_count
            FROM users_referral
            WHERE referred_by IS NOT NULL
            GROUP BY referred_by
            ORDER BY referral_count DESC
            LIMIT 10
        ''')
        top_referrals = cursor.fetchall()
        st = f""
        if not top_referrals:
            st += f"No referrals found."
            return st
        st += f"📌 Top {min(10, len(top_referrals))} Users with Most Referrals:\n"
        for rank, (user_id, count) in enumerate(top_referrals, start=1):
            st += f"{rank}. {get_user_nfgame(user_id)} - Referrals: {count}"
        return st
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

def update_unity_coin_referral(new_value):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE unity_coin_referral SET unity_coin_refferal = ?", (new_value,))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO unity_coin_referral (unity_coin_refferal) VALUES (?)", (new_value,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    
    finally:
        conn.close()

def get_unity_coin_referral():
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT unity_coin_refferal FROM unity_coin_referral LIMIT 1")
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None 
    
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return None
    
    finally:
        conn.close()

def set_tournament_status(tournament_id: str, is_begin: bool):
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO tournament_begin (tournament_id, is_begun)
            VALUES (?, ?)
            ON CONFLICT(tournament_id) DO UPDATE SET is_begun = excluded.is_begun
        ''', (tournament_id, is_begin))
        conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()

def get_tournament_status(tournament_id: str) -> bool:
    conn = sqlite3.connect("users_database.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT is_begun FROM tournament_begin WHERE tournament_id = ?
        ''', (tournament_id,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        conn.close()