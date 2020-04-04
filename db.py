import csv
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
            
    def export_table(self, table_name, file_name='data.csv'):
        con = None
        cursor = None
        
        try:
            con = self.get_connection(self.db_file)
            cursor = con.cursor()
            sql = 'SELECT * FROM {}'.format(table_name)
            cursor.execute(sql)
            
            with open(file_name, 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=",")
                csv_writer.writerow([i[0] for i in cursor.description])
                csv_writer.writerows(cursor)

            read_file = open(file_name, 'r')
            content = read_file.read()[:-1]

            with open(file_name, 'w') as write_file:
                write_file.write(content)
            
            print('Table {} exported into file {}'.format(table_name, file_name))
            logger.debug('Table {} exported into file {}'.format(table_name, file_name))
        except Error as e:
            print('db export_table Error: '+str(e))
            logger.exception('db export_table Error: '+str(e))
            
        if cursor:
            cursor.close()
        if con:
            con.close()

    def import_table(self, table_name, file_name='data.csv'):
        con = None
        cursor = None
        
        try:
            con = self.get_connection(self.db_file)
            cursor = con.cursor()
            
            headers = []
            with open(file_name, 'r') as csv_file:
                headers = csv_file.readline().split(',')
                            
            with open(file_name, 'r') as csv_file:
                dict_reader = csv.DictReader(csv_file)
                params = [tuple([row[h] for h in headers]) for row in dict_reader]

            sql = 'INSERT INTO {}({}) VALUES ({})'.format(table_name, ','.join(headers), ','.join(['?' for i in range(len(headers))]))
            cursor.executemany(sql, params)
            con.commit()
            
            print('File {} imported into table {}'.format(file_name, table_name))
            logger.debug('File {} imported into table {}'.format(file_name, table_name))
        except Error as e:
            print('db import_table Error: '+str(e))
            logger.exception('db import_table Error: '+str(e))
            
        if cursor:
            cursor.close()
        if con:
            con.close()

            
