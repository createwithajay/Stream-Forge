from rocksdict import Rdict

db = Rdict("role3_state")

db["truck_001"] = "Temperature: 25"

print("Saved:", db["truck_001"])

db.close()