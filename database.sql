-- DROP TABLE users;
-- DROP TABLE decks;
-- DROP TABLE cards2;
-- DROP TABLE reviews;
-- DROP TABLE images;
-- DROP TABLE srs;
CREATE TABLE users (
    user_id INT NOT NULL PRIMARY KEY,
    username VARCHAR(255),
    email VARCHAR(255),
    password VARCHAR(255),
    created DATETIME
);
CREATE TABLE decks (
    deck_id INT PRIMARY KEY NOT NULL,
    user_id INT REFERENCES users(user_id),
    name VARCHAR(1000),
    description VARCHAR(1000),
    created DATETIME
);
CREATE TABLE cards2 (
    card_id INT PRIMARY KEY NOT NULL,
    user_id INT REFERENCES users(user_id),
    deck_id INT REFERENCES deck(deck_id),
    front VARCHAR(1000),
    front_sub VARCHAR(1000),
    back VARCHAR(1000),
    back_sub VARCHAR(1000),
    back_sub2 VARCHAR(1000),
    tag VARCHAR(1000),
    created DATETIME
);
CREATE TABLE reviews (
    card_id INT REFERENCES cards2(card_id),
    deck_id INT REFERENCES decks(deck_id),
    user_id INT REFERENCES users(user_id),
    rating ENUM('Again', 'Hard', 'Good', 'Easy'),
    timestamp BIGINT,
    state INT
);
CREATE TABLE images (
    img_id INT PRIMARY KEY NOT NULL,
    deck_id INT REFERENCES deck(deck_id),
    extension VARCHAR(10)
);
CREATE TABLE srs (
    card_id INT REFERENCES cards2(card_id),
    deck_id INT REFERENCES decks(deck_id),
    user_id INT REFERENCES users(user_id),
    due DATETIME,
    stability FLOAT,
    difficulty FLOAT,
    elapsed_days INT,
    scheduled_days INT,
    reps INT,
    lapses INT,
    state INT,
    last_review DATETIME
);