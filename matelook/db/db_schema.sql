drop table if exists users;
create table users (
    'zid' text primary key not null,
    'email' text not null,
    'password' text not null
);


-- 'full_name', 'mates', 'birthday',  'profile_img', 
-- 'program', 'courses', 
-- 'home_suburb', 'home_longitude', 'home_latitude'
drop table if exists user_profile;
create table user_profile (
    'zid' text primary key not null,

    'full_name' text, 
    'mates' text, 
    'birthday' text, 
    'profile_img' text, 

    'program' text, 
    'courses' text, 

    'home_suburb' text, 
    'home_longitude' text, 
    'home_latitude' text
);


