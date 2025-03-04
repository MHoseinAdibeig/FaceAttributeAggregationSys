import grpc
from concurrent import futures
import redis
import io
import time
import json
import numpy as np
from PIL import Image
from keras.models import load_model
from keras.layers import DepthwiseConv2D
from keras.applications.efficientnet import preprocess_input
import aggregator_pb2
import aggregator_pb2_grpc
import logging
import os

# Configure logging
logging.basicConfig(filename='age_gender_estimation.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s:%(message)s')

class CustomDepthwiseConv2D(DepthwiseConv2D):
    def __init__(self, **kwargs):
        if 'groups' in kwargs:
            del kwargs['groups']
        super().__init__(**kwargs)

class AgeGenderEstimationService(aggregator_pb2_grpc.AgeGenderEstimationServicer):
    def __init__(self, redis_url):
        self.redis_client = redis.StrictRedis.from_url(redis_url)
        self.model = load_model("EfficientNetB3_224_weights.11-3.44.hdf5", custom_objects={'DepthwiseConv2D': CustomDepthwiseConv2D})
        self.transform = preprocess_input

    def EstimateAgeGender(self, request, context):
        try:
            image_data = request.image
            image_hash = hash(image_data)

            image = Image.open(io.BytesIO(image_data)).resize((224, 224))
            image_array = np.array(image)
            image_array = self.transform(image_array)
            image_array = np.expand_dims(image_array, axis=0)

            age_gender = self.model.predict(image_array)
            age, gender = age_gender[0][0], age_gender[0][1]

            self.redis_client.set(f"{image_hash}_age_gender", json.dumps({"age": age, "gender": gender}))

            logging.info("Age/Gender estimated")

            landmarks = self.redis_client.get(image_hash)
            if landmarks:
                self.send_to_data_storage(image_data, image_hash)
            return aggregator_pb2.AgeGenderResponse(age=age, gender=gender)
        except Exception as e:
            logging.error(f"Error in EstimateAgeGender: {e}")
            context.set_details('Internal error')
            context.set_code(grpc.StatusCode.INTERNAL)
            return aggregator_pb2.AgeGenderResponse()

    def send_to_data_storage(self, image_data, image_hash):
        try:
            channel = grpc.insecure_channel("localhost:5003")
            stub = aggregator_pb2_grpc.DataStorageStub(channel)
            stub.StoreData(aggregator_pb2.DataRequest(image=image_data, redis_key=image_hash))
        except Exception as e:
            logging.error(f"Error in send_to_data_storage: {e}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    redis_url = os.getenv('REDIS_URL', "redis://localhost:6379/0")
    aggregator_pb2_grpc.add_AgeGenderEstimationServicer_to_server(AgeGenderEstimationService(redis_url), server)
    server.add_insecure_port("[::]:5002")
    server.start()
    logging.info('AgeGenderEstimation server started on port 5002')
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
