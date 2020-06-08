#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 17:46:29 2020

@author: ATAEI
"""
from psycopg2 import (
        connect
)

cleanup = (
        'DROP TABLE IF EXISTS members CASCADE',
        'DROP TABLE IF EXISTS data'
        )

commands = (
        """
        CREATE TABLE members (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
        """,
        """
        CREATE TABLE data (
                post_id SERIAL PRIMARY KEY,
                author_id INTEGER NOT NULL,
                date TIMESTAMP DEFAULT NOW(),
                latitude FLOAT NOT NULL,
                longitude FLOAT NOT NULL,
                litter VARCHAR(225) NOT NULL,
                FOREIGN KEY (author_id)
                    REFERENCES members (user_id)
        )
        """
)

sqlCommands = (
        'INSERT INTO members (username, password) VALUES (%s, %s) RETURNING user_id',
        'INSERT INTO data (latitude, longitude, litter, author_id) VALUES (%s, %s, %s, %s)'
        )
conn = connect("dbname=webapp user=ATAEI")
cur = conn.cursor()

for command in cleanup :
    cur.execute(command)
for command in commands :
    cur.execute(command)
cur.execute(sqlCommands[0], ('Ahmad', 'ahmad'))
userId = cur.fetchone()[0]
cur.execute(sqlCommands[1], ('-34.9642', '138.5131', 'Packaging', userId))
#cur.copy_from(f,'data', sep= ',', columns=('date', 'latitude', 'longitude', 'litter', 'author'))
cur.execute('SELECT * FROM data')

print(cur.fetchall())

cur.close()
conn.commit()
conn.close()

