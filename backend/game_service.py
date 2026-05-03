from db_connection import get_connection
from geopy.distance import geodesic
import random
import os


MAX_FUEL = 2000
TARGET_MONEY = 3000
TOTAL_TURNS = 15

def clear_screen():
    print("\033c", end="")

def make_bar(value, maximum, length=20):
    filled = int((value / maximum) * length)
    empty = length - filled
    return "█" * filled + "░" * empty

def initialize_fuel_prices():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT ident
        FROM airport
        WHERE continent = 'EU'
        AND type IN ('medium_airport','large_airport')
    """)

    airports = cursor.fetchall()

    cursor.execute("DELETE FROM fuel_price")

    for airport in airports:
        ident = airport[0]

        price = round(random.uniform(2, 5), 2)

        cursor.execute(f"""
            INSERT INTO fuel_price (airport_ident, price_per_unit)
            VALUES ('{ident}', {price})
        """)

    connection.commit()
    connection.close()

def create_game():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
        INSERT INTO game (difficulty, turns_total, turns_left, target_money, created_at)
        VALUES ('easy', {TOTAL_TURNS}, {TOTAL_TURNS}, {TARGET_MONEY}, NOW())
    """)

    connection.commit()

    game_id = cursor.lastrowid

    connection.close()

    return game_id


def create_player(game_id, name):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"""
        INSERT INTO player
        (game_id, name, money, fuel, home_airport_ident, current_airport_ident)
        VALUES ({game_id}, '{name}', 1000, 600, 'EFHK', 'EFHK')
    """)
    connection.commit()
    player_id = cursor.lastrowid
    connection.close()
    return player_id

def get_game_id_for_player(player_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT game_id FROM player WHERE id = %s", (player_id,))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None



def get_fuel_price(airport_ident):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
        SELECT price_per_unit
        FROM fuel_price
        WHERE airport_ident = '{airport_ident}'
    """)

    result = cursor.fetchone()

    connection.close()

    return result[0]

def show_player(player_id, turns_left, message=None):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
        SELECT name, money, fuel, current_airport_ident
        FROM player
        WHERE id = {player_id}
    """)

    player = cursor.fetchone()

    fuel_price = get_fuel_price(player[3])

    location_name = "Helsinki" if player[3] == "EFHK" else player[3]

    fuel_bar = make_bar(player[2], MAX_FUEL)
    money_bar = make_bar(player[1], TARGET_MONEY)
    turns_bar = make_bar(turns_left, TOTAL_TURNS)

    print()
    print(f"Fuel   [{fuel_bar}] {player[2]} / {MAX_FUEL}")
    print(f"Money  [{money_bar}] {player[1]} / {TARGET_MONEY}€")
    print(f"Turns  [{turns_bar}] {turns_left} / {TOTAL_TURNS}")

    print()
    print(f"Current location: {location_name} | Fuel price: {fuel_price:.2f} €/unit")

    if message:
        print(f"\n{message}")

    connection.close()

    return player


def get_current_airport(player_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
        SELECT current_airport_ident
        FROM player
        WHERE id = {player_id}
    """)

    result = cursor.fetchone()

    connection.close()

    return result[0]

def get_airport_coordinates(ident):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
        SELECT latitude_deg, longitude_deg
        FROM airport
        WHERE ident = '{ident}'
    """)

    result = cursor.fetchone()

    connection.close()

    return result


def get_candidate_airports(current_airport_ident):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
            SELECT ident, municipality, latitude_deg, longitude_deg
            FROM airport
            WHERE ident != '{current_airport_ident}'
              AND municipality IS NOT NULL
              AND municipality != ''
              AND latitude_deg IS NOT NULL
              AND longitude_deg IS NOT NULL
              AND continent = 'EU'
              AND type IN ('medium_airport', 'large_airport')
        """)

    airports = cursor.fetchall()

    connection.close()

    return airports


def get_contracts(player_id):
    current_airport_ident = get_current_airport(player_id)
    current_coordinates = get_airport_coordinates(current_airport_ident)
    airports = get_candidate_airports(current_airport_ident)

    airport_distances = []
    for airport in airports:
        ident = airport[0]
        city = airport[1]
        latitude = airport[2]
        longitude = airport[3]

        # ✅ keep float distance for accurate calculation
        distance = geodesic(
            (current_coordinates[0], current_coordinates[1]),
            (latitude, longitude)
        ).km

        airport_distances.append({
            "destination": ident,
            "destination_name": city,
            "distance": distance   # float value
        })

    # Difficulty buckets
    easy_airports = [a for a in airport_distances if a["distance"] < 1000]
    medium_airports = [a for a in airport_distances if 1000 <= a["distance"] < 2500]
    hard_airports = [a for a in airport_distances if a["distance"] >= 2500]

    # Fallbacks
    if not easy_airports: easy_airports = airport_distances
    if not medium_airports: medium_airports = airport_distances
    if not hard_airports: hard_airports = airport_distances

    # Pick one from each bucket
    easy_airport = random.choice(easy_airports)
    medium_airport = random.choice(medium_airports)
    hard_airport = random.choice(hard_airports)

    selected_airports = [easy_airport, medium_airport, hard_airport]

    contracts = []
    for airport in selected_airports:
        fuel_needed = round(airport["distance"] * 0.2)
        reward = round(airport["distance"] * 0.5)

        contracts.append({
            "from": current_airport_ident,
            "destination": airport["destination"],
            "destination_name": airport["destination_name"],
            "distance": round(airport["distance"]),   # ✅ show rounded km
            "fuel_needed": fuel_needed,
            "reward": reward
        })

    return contracts

def refuel_player(game_id, player_id, fuel_amount):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
        SELECT money, fuel, current_airport_ident
        FROM player
        WHERE id = {player_id}
    """)
    player = cursor.fetchone()
    money, fuel, current_airport_ident = player
    connection.close()

    if fuel_amount <= 0:
        return "Fuel amount must be greater than 0."
    if fuel >= MAX_FUEL:
        return f"Fuel tank is already full. Maximum fuel is {MAX_FUEL}."
    if fuel + fuel_amount > MAX_FUEL:
        return f"You cannot exceed the maximum fuel capacity of {MAX_FUEL}. You can only buy {MAX_FUEL - fuel} more fuel."

    # ✅ Use get_fuel_price() from game_service
    fuel_price = get_fuel_price(current_airport_ident)
    total_cost = fuel_amount * fuel_price

    if money < total_cost:
        connection.close()
        return "Not enough money to buy that much fuel."

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"""
        UPDATE player
        SET
            money = money - {total_cost},
            fuel = fuel + {fuel_amount}
        WHERE id = {player_id}
    """)
    connection.commit()
    connection.close()

    log_action(game_id, player_id, "REFUEL", fuel_bought=fuel_amount, fuel_price=fuel_price)

    # ✅ Message includes fuel price
    return f"Refueled {fuel_amount} units at {fuel_price:.2f} €/unit. Cost: {total_cost:.2f}€."


def choose_contract(game_id, player_id):
    message = None

    while True:
        clear_screen()
        turns_left = get_turns_left(game_id)
        show_player(player_id, turns_left, message)

        contracts = get_contracts(player_id)

        print("\nAvailable contracts:")
        print(f"1. {contracts[0]['destination_name']} | Distance {contracts[0]['distance']} km | Reward {contracts[0]['reward']}€ | Fuel needed {contracts[0]['fuel_needed']}")
        print(f"2. {contracts[1]['destination_name']} | Distance {contracts[1]['distance']} km | Reward {contracts[1]['reward']}€ | Fuel needed {contracts[1]['fuel_needed']}")
        print(f"3. {contracts[2]['destination_name']} | Distance {contracts[2]['distance']} km | Reward {contracts[2]['reward']}€ | Fuel needed {contracts[2]['fuel_needed']}")

        print("\nType 1, 2, 3 to take a contract")
        print(f"Type R amount to refuel (example: R 100, max fuel: {MAX_FUEL})")
        print("Type S to refresh player status")

        command = input("> ").upper().strip()
        message = None

        if command == "S":
            continue

        if command in ["1", "2", "3"]:
            selected_contract = contracts[int(command) - 1]

            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(f"""
                SELECT fuel
                FROM player
                WHERE id = {player_id}
            """)
            fuel = cursor.fetchone()[0]
            connection.close()

            if fuel < selected_contract["fuel_needed"]:
                message = "Not enough fuel for this flight."
                continue

            return selected_contract

        if command.startswith("R"):
            parts = command.split()

            if len(parts) == 2 and parts[1].isdigit():
                fuel_amount = int(parts[1])
                message = refuel_player(game_id, player_id, fuel_amount)
            else:
                message = "Invalid refuel command. Example: R 100"
            continue

        message = "Invalid command."


def log_action(game_id, player_id, action_type, contract=None, fuel_bought=None, fuel_price=None):

    connection = get_connection()
    cursor = connection.cursor()

    if action_type == "CONTRACT":

        cursor.execute(f"""
        INSERT INTO action_log
        (game_id, player_id, action_type, from_airport_ident, to_airport_ident,
         distance_km, fuel_used, money_change)
        VALUES (
            {game_id},
            {player_id},
            'CONTRACT',
            '{contract["from"]}',
            '{contract["destination"]}',
            {contract["distance"]},
            {contract["fuel_needed"]},
            {contract["reward"]}
        )
        """)

    if action_type == "REFUEL":

        cursor.execute(f"""
        INSERT INTO action_log
        (game_id, player_id, action_type, fuel_bought, fuel_price, refuel_cost)
        VALUES (
            {game_id},
            {player_id},
            'REFUEL',
            {fuel_bought},
            {fuel_price},
            {fuel_bought * fuel_price}
        )
        """)

    connection.commit()
    connection.close()

def update_player_after_contract(game_id, player_id, contract):
    connection = get_connection()
    cursor = connection.cursor()

    reward = int(contract['reward'])
    fuel_used = int(contract['fuel_needed'])

    # Check fuel availability
    cursor.execute(f"SELECT fuel, money FROM player WHERE id = {player_id}")
    fuel, money = cursor.fetchone()
    if fuel < fuel_used:
        connection.close()
        return "Not enough fuel to deliver this contract. Please refuel first."

    #terms cheak
    turns_left = get_turns_left(game_id)


    cursor.execute(f"""
        UPDATE player
        SET
            money = money + {reward},
            fuel = fuel - {fuel_used},
            current_airport_ident = '{contract['destination']}'
        WHERE id = {player_id}
    """)
    connection.commit()

    cursor.execute(f"SELECT money FROM player WHERE id = {player_id}")
    current_money = cursor.fetchone()[0]
    connection.close()

    if current_money >= TARGET_MONEY:
        return f"🎉 Congratulations! You reached {current_money}€ and won the game!"
    elif turns_left <= 0:  # ✅ lose only when zero
        return "Game Over!\nYour turns are run out\nYou lose the game!"

    else:
        return f"Flight completed! You earned {reward}€ and used {fuel_used} fuel."



def reduce_turn(game_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
        UPDATE game
        SET turns_left = turns_left - 1
        WHERE id = {game_id}
    """)

    connection.commit()
    connection.close()


def get_turns_left(game_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(f"""
        SELECT turns_left
        FROM game
        WHERE id = {game_id}
    """)

    result = cursor.fetchone()

    connection.close()

    return result[0]


