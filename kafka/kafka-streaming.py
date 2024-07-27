from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import time
import uuid
import random
from datetime import datetime as dt
import json
from kafka import KafkaProducer
import requests
import os, sys

bootstrap_servers = '172.16.11.62:30238'
topic_name = 'bami-topic'

def confirm_topic():
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
        existing_topics = admin_client.list_topics()

        if topic_name in existing_topics:
            print(f"Topic list: '{topic_name}' ")
        else:
            topic = NewTopic(name=topic_name)
            try:
                admin_client.create_topics([topic])
                print(f"Topic '{topic_name}' created successfully.")
                time.sleep(8)
            except TopicAlreadyExistsError:
                print(f"Topic '{topic_name}' already exists.")

    except Exception as e:
        print(f"Error connecting to Kafka: {str(e)}")

def devices(offset=0):

    device_id = [1, 2, 3, 4, 5]
    age_list = [23, 3, 7, 35, 37]
    name_list = ["jeong" , "ba", "mi" , "ji" , "won"]

    _event = {
        "eventId": str(uuid.uuid4()),
        "eventOffset": offset,
        "eventPublisher": "device",
        "data": {
            "devices": [
                {
                    "deviceId": random.choice(device_id),
                    "name": random.choice(name_list),
                    "age": random.choice(age_list)
                }
            ],
        },
        "eventTime": str(dt.now())
    }
    time.sleep(10)

    return json.dumps(_event).encode('utf-8')

def kafka_streaming():

    confirm_topic()
    _offset = 100
    producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
    try:
        while True:
            data = devices(offset=_offset)
            producer.send(topic_name, key=b'device', value=data)
            producer.flush()
            print("Posted to topic")
            time.sleep(random.randint(0, 5))
            _offset += 1
    except Exception as e:
        print(f"Error: {e}")
    finally:
        producer.close()

if __name__ == "__main__" :
    kafka_streaming()
