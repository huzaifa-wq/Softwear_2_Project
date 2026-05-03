from flask import Flask, jsonify, request, send_from_directory
from db_initializer import initialize_database
from game_service import (
    initialize_fuel_prices,
    create_game,
    create_player,
    show_player,
    get_turns_left,
    get_contracts,
    update_player_after_contract,
    get_fuel_price,
    refuel_player,
    reduce_turn,
    get_airport_coordinates,
    get_game_id_for_player
)



app = Flask(__name__)

# Serve frontend files
@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# Start a new game
@app.route('/start_game', methods=['POST'])
def start_game():
    initialize_database()
    initialize_fuel_prices()
    game_id = create_game()
    player_name = request.json.get("name", "Captain")  # frontend sends name
    player_id = create_player(game_id, player_name)
    return jsonify({"game_id": game_id, "player_id": player_id, "player_name": player_name})


# Get player status
@app.route('/status/<int:player_id>', methods=['GET'])
def status(player_id):
    game_id = get_game_id_for_player(player_id)
    if not game_id:
        # create new game + player
        game_id = create_game()
        new_player_id = create_player(game_id, f"Player{player_id}")
        return jsonify({"message":"New player created","player_id":new_player_id,})

    turns_left = get_turns_left(game_id)
    player = show_player(player_id, turns_left)

    #  Get fuel price for current airport
    current_airport_ident = player[3]   # location = airport ident
    fuel_price = get_fuel_price(current_airport_ident)

    latitude, longitude = get_airport_coordinates(current_airport_ident)

    return jsonify({
        "name": player[0],
        "money": player[1],
        "fuel": player[2],
        "location": current_airport_ident,
        "turns_left": turns_left,
        "fuel_price": fuel_price,
        "latitude": latitude,
        "longitude": longitude
    })



# Get available contracts
@app.route('/contracts/<int:player_id>', methods=['GET'])
def contracts(player_id):
    contracts = get_contracts(player_id)
    enriched_contracts = []

    for c in contracts:
        lat, lon = get_airport_coordinates(c['destination'])
        c['latitude'] = lat
        c['longitude'] = lon
        enriched_contracts.append(c)

    return jsonify(enriched_contracts)


# Deliver cargo (choose contract)
@app.route('/deliver/<int:player_id>', methods=['POST'])
def deliver(player_id):
    contract = request.json
    game_id = get_game_id_for_player(player_id)   #  dynamic game_id
    message = update_player_after_contract(game_id, player_id, contract)
    reduce_turn(game_id)
    return jsonify({"message": message})




# Refuel
@app.route('/refuel/<int:player_id>', methods=['POST'])
def refuel(player_id):
    fuel_amount = request.json.get("fuel_amount")
    game_id = get_game_id_for_player(player_id)   #  dynamic game_id
    message = refuel_player(game_id, player_id, fuel_amount)
    return jsonify({"message": message})



if __name__ == '__main__':
    app.run(debug=True)
