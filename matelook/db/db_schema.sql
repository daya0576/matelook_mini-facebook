-- zid, email, password
-- 'full_name', 'mates', 'birthday',  'profile_img', 
-- 'program', 'courses', 
-- 'home_suburb', 'home_longitude', 'home_latitude'
drop table if exists USER;
create table USER (
    'zid' text primary key not null,
    'email' text,
    'password' text not null,

    'full_name' text, 
    -- 'mates' text, 
    'birthday' text, 
    'profile_img' text, 

    'program' text, 
    -- 'courses' text, 

    'home_suburb' text, 
    'home_longitude' text, 
    'home_latitude' text
);

drop table if exists MATES;
CREATE TABLE MATES (
    id INTEGER PRIMARY KEY   AUTOINCREMENT,
    user_zid TEXT REFERENCES USER(zid),
    mate_zid TEXT
);

drop table if exists ENROLLMENT;
CREATE TABLE ENROLLMENT
(
    id INTEGER PRIMARY KEY   AUTOINCREMENT,
    zid TEXT  REFERENCES USER(zid),
    course TEXT
);



drop table if exists POST;
CREATE TABLE POST
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zid TEXT  REFERENCES USER(zid),
    time TEXT,
    latitude TEXT,
    longitude TEXT,
    message TEXT
);
