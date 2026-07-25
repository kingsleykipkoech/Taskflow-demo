-- Categories table: stores event types like Classes, Assignments, etc.
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50)
);

-- Events table: stores each event the user creates.
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    event_date VARCHAR(10),
    event_time VARCHAR(20),
    details VARCHAR(500),
    status VARCHAR(20),
    category_id INT,
    created_by VARCHAR(50)
);

-- Attendees table: stores emails of people who should be reminded.
CREATE TABLE IF NOT EXISTS attendees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT,
    email VARCHAR(200)
);