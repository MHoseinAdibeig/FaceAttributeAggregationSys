import grpc
from concurrent import futures
import redis
import json
import aggregator_pb2
import aggregator_pb2_grpc
import logging
import os

# Configure logging
logging.basicConfig(filename='data_storage.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s:%(message)s')

class DataStorageService(aggregator_pb2_grpc.DataStorageServicer):
    def __init__(self, redis_url):
        self.redis_client = redis.StrictRedis.from_url(redis_url)

    def StoreData(self, request, context):
        try:
            image_data = request.image
            redis_key = request.redis_key

            landmarks = self.redis_client.get(redis_key)
            age_gender = self.redis_client.get(f"{redis_key}_age_gender")

            data = {
                "image": image_data.decode('latin1'),
                "landmarks": json.loads(landmarks) if landmarks else None,
                "age_gender": json.loads(age_gender) if age_gender else None,
            }

            with open(f"{redis_key}.json", "w") as json_file:
                json.dump(data, json_file)

            logging.info("Data stored")

            return aggregator_pb2.DataResponse(status="success")
        except Exception as e:
            logging.error(f"Error in StoreData: {e}")
            context.set_details('Internal error')
            context.set_code(grpc.StatusCode.INTERNAL)
            return aggregator_pb2.DataResponse(status="failure")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    redis_url = os.getenv('REDIS_URL', "redis://localhost:6379/0")
    aggregator_pb2_grpc.add_DataStorageServicer_to_server(DataStorageService(redis_url), server)
    server.add_insecure_port("[::]:5003")
    server.start()
    logging.info('DataStorage server started on port 5003')
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
