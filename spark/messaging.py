import os
import requests
import threading
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import SparkSession
import time

bootstrap_servers = '172.16.11.62:30238'
topic_name = 'bami-topic'
spark_version = '3.5.1'
spark_master_url = '133.186.152.78::6443'
data_path = '/result-data'

def process_messages(parsed_df):
    try:
        for i in range(60):
            print("Waiting to install kafka", end=" ")
            if i % 2 == 0:
                print("\\")
            else:
                print("/")
            time.sleep(1)
            print("\033[F", end="")

        spark = SparkSession \
            .builder \
            .appName("PipelineApp") \
            .master("k8s://"+spark_master_url) \
            .config('spark.jars', '/opt/bitnami/spark/jars/kafka-clients-3.5.1.jar,/opt/bitnami/spark/jars/spark-streaming-kafka-0-10_2.12-3.5.1.jar,/opt/bitnami/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.1.jar,/opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.5.1.jar,/opt/bitnami/spark/jars/commons-pool2-2.12.0.jar') \
            .config("spark.streaming.stopGracefullyOnShutdown","true") \
            .config("spark.kubernetes.driver.volumes.emptyDir.spark-work.mount.path","/spark-result") \
            .config("spark.kubernetes.driver.volumes.emptyDir.spark-work.options.path","/spark-result") \
            .config("spark.kubernetes.executor.volumes.emptyDir.spark-work.mount.path","/spark-result") \
            .config("spark.kubernetes.executor.volumes.emptyDir.spark-work.options.path","/spark-result") \
            .getOrCreate()

        df = spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", bootstrap_servers) \
            .option("startingOffsets", "latest") \
            .option("subscribe", topic_name) \
            .load()

        df.printSchema()

        schema = StructType([
            StructField("eventId", StringType(), True),
            StructField("eventOffset", StringType(), True),
            StructField("eventPublisher", StringType(), True),
            StructField("data", StructType([
                StructField("devices", ArrayType(StructType([
                    StructField("deviceId", StringType(), True),
                    StructField("name", StringType(), True),
                    StructField("age", IntegerType(), True)
                ])), True)
            ]), True),
            StructField("eventTime", StringType(), True)
        ])

        jsonSchema = schema

        parsed_df = df.selectExpr("CAST(value AS STRING) as json").select(from_json("json", jsonSchema).alias("data")).select("data.*")

        return parsed_df

    except Exception as e:
        print("An error occurred:", e)

def streaming(parsed_df):

    query = parsed_df \
            .writeStream \
            .format("json") \
            .option("checkpointLocation", "checkpoint") \
            .option("path", data_path) \
            .trigger(processingTime="30 seconds") \
            .outputMode("append") \
            .start()

    query.awaitTermination()

def get_token(auth_url, tenant_id, username, password):
    token_url = auth_url + '/tokens'
    req_header = {'Content-Type': 'application/json'}
    req_body = {
        'auth': {
            'tenantId': tenant_id,
            'passwordCredentials': {
                'username': username,
                'password': password
            }
        }
    }

    response = requests.post(token_url, headers=req_header, json=req_body)
    return response.json()

class ObjectService:
    def __init__(self, storage_url, token_id):
        self.storage_url = storage_url
        self.token_id = token_id

    def _get_url(self, container, object):
        return '/'.join([self.storage_url, container, object])

    def _get_request_header(self):
        return {'X-Auth-Token': self.token_id}

    def upload(self, container, object, object_path):
        req_url = self._get_url(container, object)
        req_header = self._get_request_header()

        file_path = os.path.join(object_path, object)
        with open(file_path, 'rb') as f:
            return requests.put(req_url, headers=req_header, data=f.read())

def upload_files():
    # 토큰 발급 및 객체 저장 시작
    AUTH_URL = 'https://api-identity-infrastructure.nhncloudservice.com/v2.0'
    TENANT_ID = '9ea3a098cb8e49468ac2332533065184'
    USERNAME = 'minkyu.lee'
    PASSWORD = 'PaaS-TA@2024!'

    token = get_token(AUTH_URL, TENANT_ID, USERNAME, PASSWORD)
    token_value = token["access"]["token"]["id"]
    print("get token successful")

    STORAGE_URL = 'https://kr1-api-object-storage.nhncloudservice.com/v1/AUTH_9ea3a098cb8e49468ac2332533065184'
    TOKEN_ID = token_value
    CONTAINER_NAME = 'cp-object-storage'
#    OBJECT_NAME = 'part-0000dd0-2f0f45cd-9194-48eb-ac34-0aac8f045288-c000.json'
    OBJECT_PATH = data_path

    directory = data_path
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            OBJECT_NAME = filename
            obj_service = ObjectService(STORAGE_URL, TOKEN_ID)
            obj_service.upload(CONTAINER_NAME, OBJECT_NAME, OBJECT_PATH)

    print("upload complete")

if __name__ == "__main__":
    upload_thread = threading.Thread(target=upload_files)
    upload_thread.start()

    upload_thread.join()


    parsed_df=None
    parsed_df= process_messages(parsed_df)

    streaming_thread = threading.Thread(target=streaming, args=(parsed_df,))
    streaming_thread.start()
