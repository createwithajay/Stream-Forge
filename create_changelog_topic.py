from confluent_kafka.admin import AdminClient, NewTopic


def create_recovery_topic():
    admin_client = AdminClient({
        'bootstrap.servers': 'localhost:9092'
    })

    topic_name = "kafka_changelog"

    new_topic = NewTopic(
        topic_name,
        num_partitions=3,
        replication_factor=1
    )

    fs = admin_client.create_topics([new_topic])

    for topic, future in fs.items():
        try:
            future.result()
            print(f"Success: Topic '{topic}' created for State Recovery.")
        except Exception as e:
            print(f"Failed to create topic '{topic}': {e}")


if __name__ == '__main__':
    create_recovery_topic()