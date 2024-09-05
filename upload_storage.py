import os
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.functions import col, pandas_udf, split
import requests
import json
import time


bootstrap_servers = '125.6.40.10:19092'
topic_name = 'devices'
spark_version = '3.3.0'
#os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12-3.3.0,org.apache.spark:spark-streaming-kafka-0-10_2.12-3.3.0,org.apache.spark:commons-pool2-2.11.0,org.apache.spark:kafka-clients-3.3.0'.format(spark_version)
spark_master_url = '125.6.40.10:7077'

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

        path = '/'.join([object_path, object])
        with open(path, 'rb') as f:
            return requests.put(req_url, headers=req_header, data=f.read())

#if __name__ =="__main__":
def upload_storage():
    
    AUTH_URL = 'https://api-identity-infrastructure.***********.com/v2.0'
    TENANT_ID = '9ea3a098**********332533065184'
    USERNAME = '*******'
    PASSWORD = '********'

    token = get_token(AUTH_URL, TENANT_ID, USERNAME, PASSWORD)
    #Token값 
    token_value=(token["access"]["token"]["id"])
    print("get token successful")

    STORAGE_URL = 'https://kr1-api-object-storage.**********.com/v1/AUTH_9ea3a098cb8**************184'
    TOKEN_ID = token_value
    CONTAINER_NAME = '************'
#    OBJECT_NAME = 'part-0000dd0-2f0f45cd-9194-48eb-ac34-0aac8f045288-c000.json'
    OBJECT_PATH = r'/tmp/data'
    
    #파일에 있는 모든 로그 한번에 보내기 
    directory = '/tmp/data'
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            OBJECT_NAME=filename
            obj_service = ObjectService(STORAGE_URL, TOKEN_ID)
            obj_service.upload(CONTAINER_NAME, OBJECT_NAME, OBJECT_PATH)
            
    print("upload complete")
    
def messaging():
    spark = SparkSession \
        .builder \
        .appName("PipelineApp")\
        .master("spark://"+spark_master_url)\
        .config('spark.jars', './jars/spark-sql-kafka-0-10_2.12-3.3.0.jar, ./jars/spark-streaming-kafka-0-10_2.12-3.3.0.jar, ./jars/commons-pool2-2.11.0.jar, ./jars/kafka-clients-3.3.0.jar, ./jars/spark-token-provider-kafka-0-10_2.12-3.3.0.jar')\
        .config("spark.streaming.stopGracefullyOnShutdown","true")\
        .getOrCreate()

    df = spark.readStream\
        .format("kafka")\
        .option("kafka.bootstrap.servers", bootstrap_servers)\
        .option("startingOffsets", "latest")\
        .option("subscribe", topic_name)\
        .option("group.id", "console-consumer-43849")\
        .load()

    df.printSchema()
    print("read schema from kafka!")
    
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

    query = parsed_df \
        .writeStream \
        .format("json") \
        .option("checkpointLocation", "checkpoint") \
        .option("path", upload_storage()) \
        .trigger(processingTime="30 seconds")\
        .outputMode("append")\
        .start()

    print("Wait for Streaming...")
#    query = parsed_df.writeStream.format("console").start()
    query.awaitTermination()

