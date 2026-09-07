import time
from confluent_kafka.admin import AdminClient

BOOTSTRAP_SERVERS = "localhost:9092"
GROUP_ID = "streamforge-workers"

admin = AdminClient({"bootstrap.servers": BOOTSTRAP_SERVERS})

def check_group_status():
    print(f"\n[MONITOR] Inspecting consumer group '{GROUP_ID}'...")
    try:
        group_desc = admin.describe_consumer_groups([GROUP_ID])
        future = group_desc.get(GROUP_ID)
        
        if future is None:
            print(f"[INFO] Group '{GROUP_ID}' not registered yet.")
            return

        res = future.result()
        state = getattr(res, 'state', 'Unknown')
        protocol_type = getattr(res, 'protocol_type', 'Unknown')
        members = getattr(res, 'members', [])

        print(f"State: {state} | Protocol: {protocol_type}")
        print(f"Active Members: {len(members)}")
        
        for member in members:
            m_id = getattr(member, 'member_id', 'N/A')
            c_id = getattr(member, 'client_id', 'N/A')
            host = getattr(member, 'host', 'N/A')
            print(f"  -> Member ID: {m_id} | Client: {c_id} | Host: {host}")

    except Exception as e:
        print(f"[INFO] Waiting for active consumers or rebalance: {e}")

if __name__ == "__main__":
    while True:
        check_group_status()
        time.sleep(3)