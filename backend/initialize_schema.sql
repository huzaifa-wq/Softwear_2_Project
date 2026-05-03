CREATE TABLE IF NOT EXISTS game (
    id INT AUTO_INCREMENT PRIMARY KEY,
    difficulty VARCHAR(255),
    turns_total INT,
    turns_left INT,
    target_money INT,
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS player (
    id INT AUTO_INCREMENT PRIMARY KEY,
    game_id INT,
    name VARCHAR(255),
    money INT,
    fuel INT,
    home_airport_ident VARCHAR(40) COLLATE latin1_swedish_ci,
    current_airport_ident VARCHAR(40) COLLATE latin1_swedish_ci,
    FOREIGN KEY(game_id) REFERENCES game(id),
    FOREIGN KEY(home_airport_ident) REFERENCES airport(ident),
    FOREIGN KEY(current_airport_ident) REFERENCES airport(ident)
);

CREATE TABLE IF NOT EXISTS contract (
    id INT AUTO_INCREMENT PRIMARY KEY,
    game_id INT,
    origin_airport_ident VARCHAR(40) COLLATE latin1_swedish_ci,
    dest_airport_ident VARCHAR(40) COLLATE latin1_swedish_ci,
    reward INT,
    weather_type VARCHAR(50),
    distance_km FLOAT,
    fuel_required INT,
    created_turn INT,
    is_taken BOOLEAN,
    FOREIGN KEY(game_id) REFERENCES game(id),
    FOREIGN KEY(origin_airport_ident) REFERENCES airport(ident),
    FOREIGN KEY(dest_airport_ident) REFERENCES airport(ident)
);

CREATE TABLE IF NOT EXISTS action_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    game_id INT,
    player_id INT,
    turn_number INT,
    action_type VARCHAR(50),
    contract_id INT,
    from_airport_ident VARCHAR(40) COLLATE latin1_swedish_ci,
    to_airport_ident VARCHAR(40) COLLATE latin1_swedish_ci,
    weather_type VARCHAR(50),
    distance_km FLOAT,
    fuel_used INT,
    money_change INT,
    fuel_bought INT,
    fuel_price FLOAT,
    refuel_cost INT,
    FOREIGN KEY(game_id) REFERENCES game(id),
    FOREIGN KEY(player_id) REFERENCES player(id),
    FOREIGN KEY(contract_id) REFERENCES contract(id),
    FOREIGN KEY(from_airport_ident) REFERENCES airport(ident),
    FOREIGN KEY(to_airport_ident) REFERENCES airport(ident)
);

CREATE TABLE IF NOT EXISTS fuel_price (
    airport_ident VARCHAR(40) COLLATE latin1_swedish_ci,
    price_per_unit FLOAT,
    PRIMARY KEY(airport_ident),
    FOREIGN KEY(airport_ident) REFERENCES airport(ident)
);