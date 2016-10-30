#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import os
import re
import sys
import sqlite3
from collections import defaultdict


def value2list(text):
    text = re.sub(r'(^\[|\]$)', '', text)
    value_list = text.split(',') if text != "" else []
    value_list = [value.strip() for value in value_list]

    return value_list


def text2pair(text):
    key, value = -1, -1
    text_items = text.split('=', maxsplit=1)
    if len(text_items) != 2:
        print("\n    error:\'{}\' --> split Len != 2".format(text))
    else:
        key = text_items[0]
        value = text_items[1]
        if re.findall(r"^\[.+\]$", value):
            value = value2list(value)

    return key, value


def constant_factory(value):
    return lambda: value


def dataset2dict(file_path):
    item_dict = defaultdict(constant_factory('null'))
    if not os.path.exists(file_path):
        print("error: {} does not exist".format(file_path))
        return
    else:
        with open(file_path, 'r') as f:
            read_lines = f.readlines()
            for line in read_lines:
                line = line.rstrip('\n')
                key, value = text2pair(line)
                if key != -1 and value != -1:
                    item_dict[key] = value
                else:
                    print("    {}\n".format(file_path))

    return item_dict


def check_dir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)


def get_user_dict(dataset, user):
    file_path = "{}/{}/user.txt".format(dataset, user)
    user_dict = dataset2dict(file_path)

    check_dir("../static/user/profile_img/{}/".format(dataset))
    check_dir("../static/user/profile_img/{}/{}/".format(dataset, user))

    img_path = "{}/{}/profile.jpg".format(dataset, user)
    if os.path.exists(img_path):
        user_dict["profile_img"] = "{}/{}/profile.jpg".format(dataset, user)
        os.system("cp {0}/{1}/profile.jpg ../static/user/profile_img/{0}/{1}/profile.jpg".format(dataset, user))
    else:
        user_dict["profile_img"] = "default.png"

    return user_dict


if __name__ == "__main__":
    # dataset = "dataset-small"
    # db_filename = "small_sqlite.db"
    if len(sys.argv) < 2:
        print("Usage: {} [dataset dir]".format(sys.argv[0]))
        exit(1)

    dataset = sys.argv[1]
    if "large" in dataset:
        db_filename = "large_SQLite.db"
    elif "medium" in dataset:
        db_filename = "medium_SQLite.db"
    elif "small" in dataset:
        db_filename = "small_SQLite.db"
    else:
        db_filename = "other_SQLite.db"

    print('''Transferring {} to {} '''.format(dataset, db_filename))
    print()

    ''' get user basic info '''
    users = [f for f in os.listdir(dataset)]
    user_dicts = []
    for user in users:
        user_dicts.append(get_user_dict(dataset, user))

    print(''' Checking all usr info attributes.. ''')
    keys_set = set()
    for user_dict in user_dicts:
        # print(user_dict.keys())
        keys_set |= set(user_dict.keys())
    print(" User has {} attributes: ".format(len(keys_set)), keys_set)
    print()

    print(''' Building all tables ''')
    os.system("sqlite3 {} < db_schema.sql".format(db_filename))
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()


    print(''' Inserting user basic user info.. ''')
    users_insert = []
    for user_dict in user_dicts:
        users_insert.append((user_dict['zid'], user_dict['email'], user_dict['password'],
                           user_dict['full_name'], user_dict['birthday'], user_dict['profile_img'],
                           user_dict['program'],
                           user_dict['home_suburb'], user_dict['home_longitude'], user_dict['home_latitude']))
    insert_sql = "INSERT INTO USER VALUES (?,?,?, ?,?,?, ?, ?,?,?, '',1)"
    result = c.executemany(insert_sql, users_insert)
    print("   Totally {} users inserted.".format(len(users_insert)))

    for user_dict in user_dicts:
        for mate in user_dict['mates']:
            insert_mate_sql = "INSERT INTO MATES(user_zid, mate_zid, confirmed) VALUES (?, ?, ?)"
            c.executemany(insert_mate_sql, [(user_dict['zid'], mate, 1)])
        for course in user_dict['courses']:
            insert_course_sql = "INSERT INTO ENROLLMENT(zid, course) VALUES (?, ?)"
            c.executemany(insert_course_sql, [(user_dict['zid'], course)])


    print(''' Transferring Posts Comments replies.. ''')
    post_id, comment_id, reply_id = 0, 0, 0
    for i, user in enumerate(users):
        if i%10 == 0:
            rate = (i+1)*1.0/len(users)*100
            print("   {0:.1f}%..".format(rate))

        ''' Posts '''
        post_dir = "{}/{}/posts".format(dataset, user)
        for post in os.listdir(post_dir):
            post_dict = dataset2dict("{}/{}/post.txt".format(post_dir, post))
            if post_dict:
                insert_post_sql = "INSERT INTO POST(id, zid, time, latitude, longitude, message, privacy) " \
                                  "VALUES (?, ?, ?, ?, ?, ?, 'public')"
                post_id += 1
                c.execute(insert_post_sql, [post_id, post_dict["from"], post_dict["time"], post_dict["latitude"], post_dict["longitude"], post_dict["message"]])
            else:
                print("continue");continue

            ''' Comments '''
            comment_dir = "{}/{}/posts/{}/comments".format(dataset, user, post)
            if os.path.exists(comment_dir):
                for comment in os.listdir(comment_dir):
                    comment_dict = dataset2dict("{}/{}/comment.txt".format(comment_dir, comment))
                    insert_comment_sql = "INSERT INTO COMMENT(id, post_id, zid, time, message) " \
                                         "VALUES (?, ?, ?, ?, ?)"
                    comment_id += 1
                    c.execute(insert_comment_sql,
                              [comment_id, post_id, comment_dict['from'], comment_dict['time'], comment_dict['message']])

                    reply_dir = "{}/{}/posts/{}/comments/{}/replies".format(dataset, user, post, comment)
                    if os.path.exists(reply_dir):
                        for reply in os.listdir(reply_dir):
                            reply_dict = dataset2dict("{}/{}/reply.txt".format(reply_dir, reply))
                            if reply_dict:
                                insert_reply_sql = "INSERT INTO REPLY(id, comment_id, zid, time, message) " \
                                                   "VALUES (?, ?, ?, ?, ?)"
                                reply_id += 1
                                c.execute(insert_reply_sql,
                                          [reply_id, comment_id, reply_dict['from'],
                                           reply_dict['time'], reply_dict['message']])
                            else:
                                print("continue")
                                continue

    conn.commit()
    conn.close()
    print(" Done!")




