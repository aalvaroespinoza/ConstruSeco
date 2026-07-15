import sqlite3
c = sqlite3.connect('corralon_profesional.db').cursor()
print(c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
