-- Initialize the database.
-- Drop any existing data and create empty tables.
USE max_database;

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) UNIQUE NOT NULL,
  password VARCHAR(256) NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title VARCHAR(64) NOT NULL,
  body VARCHAR(1024) NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title VARCHAR(64) NOT NULL,
  body VARCHAR(1024) NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);
