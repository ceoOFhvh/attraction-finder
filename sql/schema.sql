-- ПР7. Одна категория содержит много достопримечательностей.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    name_key TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS attractions (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    search_name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    open_hour INTEGER NOT NULL CHECK (open_hour BETWEEN 0 AND 23),
    close_hour INTEGER NOT NULL CHECK (close_hour BETWEEN 1 AND 24),
    price REAL NOT NULL DEFAULT 0 CHECK (price >= 0),
    description TEXT DEFAULT NULL,
    CHECK (open_hour < close_hour),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_attractions_category
    ON attractions(category_id);
CREATE INDEX IF NOT EXISTS idx_attractions_price ON attractions(price);
