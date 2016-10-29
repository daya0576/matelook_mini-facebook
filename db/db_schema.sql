-- zid, email, password
-- 'full_name', 'mates', 'birthday',  'profile_img', 
-- 'program', 'courses', 
-- 'home_suburb', 'home_longitude', 'home_latitude'
DROP TABLE IF EXISTS USER;
CREATE TABLE USER (
  'zid'            TEXT PRIMARY KEY NOT NULL,
  'email'          TEXT,
  'password'       TEXT             NOT NULL,

  'full_name'      TEXT,
  -- 'mates' text,
  'birthday'       TEXT,
  'profile_img'    TEXT,

  'program'        TEXT,
  -- 'courses' text,

  'home_suburb'    TEXT,
  'home_longitude' TEXT,
  'home_latitude'  TEXT,


  'profile_text'   TEXT,
  'confirmed'      INTEGER
);


DROP TABLE IF EXISTS MATES;
CREATE TABLE MATES (
  id        INTEGER PRIMARY KEY   AUTOINCREMENT,
  user_zid  TEXT REFERENCES USER (zid),
  mate_zid  TEXT,
  confirmed INTEGER
);

DROP TABLE IF EXISTS ENROLLMENT;
CREATE TABLE ENROLLMENT
(
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  zid    TEXT REFERENCES USER (zid),
  course TEXT
);


DROP TABLE IF EXISTS POST;
CREATE TABLE POST
(
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  zid       TEXT REFERENCES USER (zid),
  time      TEXT,
  latitude  TEXT,
  longitude TEXT,
  message   TEXT,

  privacy   TEXT
);

DROP TABLE IF EXISTS COMMENT;
CREATE TABLE COMMENT
(
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER REFERENCES POST (id),
  zid     TEXT REFERENCES USER (zid),

  time    TEXT,
  message TEXT
);

DROP TABLE IF EXISTS REPLY;
CREATE TABLE REPLY
(
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  comment_id INTEGER REFERENCES COMMENT (id),
  zid        TEXT REFERENCES USER (zid),

  time       TEXT,
  message    TEXT
);

