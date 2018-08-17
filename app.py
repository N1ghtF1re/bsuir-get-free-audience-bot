import requests
import sys
import updateDB
import sqlite3
import os
from getEmployedFromDB import getEmployedAud
from getAudiences import getAudiencesList

db_file = '/projects/parser/db/schedule.sqlite' # Файл базы данных SQLite


try:
	# Подключаемся к БД
	conn = sqlite3.connect(db_file)
	cursor = conn.cursor()

	updateDB.updateAllTables(cursor, conn)
except sqlite3.Error as e:
	print(e)
finally:
	conn.close()
