DROP TABLE srs;
CREATE TABLE srs (
    card_id INT REFERENCES cards2(card_id),
    deck_id INT REFERENCES decks(deck_id),
    user_id INT REFERENCES users(user_id),
    due DATETIME,
    stability FLOAT,
    difficulty FLOAT,
    scheduled_days INT,
    reps INT,
    lapses INT,
    state VARCHAR(10),
    last_review DATETIME
);