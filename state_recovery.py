from rocksdict import Rdict

db = Rdict("role3_state")

if "sum" in db and "count" in db:
    # Recover existing state
    total = db["sum"]
    count = db["count"]

    print("Recovered sum:", total)
    print("Recovered count:", count)
    print("Recovered average:", total / count)

else:
    # Create initial state
    temperatures = [25, 27, 26]

    total = sum(temperatures)
    count = len(temperatures)

    db["sum"] = total
    db["count"] = count

    print("Initial state saved.")
    print("Sum:", total)
    print("Count:", count)
    print("Average:", total / count)

db.close()