import sqlite3

db = sqlite3.connect('db.db')
c = db.cursor()

db.create_collation("en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1)

db.commit()

c.executescript(
    '''
drop table users;
CREATE TABLE users (
    id INTEGER NOT NULL,
    username VARCHAR(255) COLLATE "en_AU" NOT NULL,
    PRIMARY KEY (id)
)
'''
)
db.commit()

c.execute(
    '''
insert into users (username) values ("hello");

        '''
)

db.close()
