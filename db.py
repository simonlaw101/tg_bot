import logging
import sqlite3
from sqlite3 import Error

logger = logging.getLogger('FxStock')

class DB:
    def __init__(self):
        self.db_file = 'db.db'

    def get_connection(self, db_file):
        try:
            return sqlite3.connect(db_file)
        except Error as e:
            logger.exception('db get_connection Error: '+str(e))
            return None
        
    def execute(self, sql, param=None):
        con = None
        cursor = None
        
        try:
            con = self.get_connection(self.db_file)
            cursor = con.cursor()

            if param is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, param)

            if sql.upper().startswith('SELECT'):
                return cursor.fetchall()
            elif sql.upper().startswith('INSERT'):
                con.commit()
                return cursor.lastrowid
            elif sql.upper().startswith('UPDATE') or\
                 sql.upper().startswith('DELETE') or\
                 sql.upper().startswith('REPLACE'):
                con.commit()
        except Error as e:
            logger.exception('db execute Error: '+str(e))
            
        if cursor:
            cursor.close()
        if con:
            con.close()

            
