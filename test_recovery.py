from rocksdict import Rdict

DB_PATH = "role3_state"

# Save rolling-average state
db = Rdict(DB_PATH)

db["truck_001_sum"] = 50
db["truck_001_count"] = 2
db["truck_001_avg"] = 25

db.close()

print("State saved.")

# Reopen database to test recovery
db = Rdict(DB_PATH)

total = db["truck_001_sum"]
count = db["truck_001_count"]

print("Recovered sum:", total)
print("Recovered count:", count)
print("Recovered average:", total / count)

# Add a new temperature
new_temperature = 30

total = total + new_temperature
count = count + 1
average = total / count

db["truck_001_sum"] = total
db["truck_001_count"] = count
db["truck_001_avg"] = average

print("After new temperature:", new_temperature)
print("New rolling average:", average)

db.close()