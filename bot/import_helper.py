# importing the module
import sqlite3

# Load backups
with open("moneybackup.eco") as file:
    money = file.readlines()

for i in range(0, len(money)):
    money[i] = float(money[i])

with open("userbackup.eco") as file:
    users = file.readlines()

for i in range(0, len(users)):
    users[i] = int(users[i])

# connect with the myTable database
connection = sqlite3.connect("economy.db")

# cursor object
crsr = connection.cursor()

for i in range(len(users)):
    crsr.execute(f'INSERT INTO Users VALUES ({users[i]}, "", {money[i]});')

# To save the changes in the files. Never skip this.
# If we skip this, nothing will be saved in the database.
connection.commit()
 
# close the connection
connection.close()
