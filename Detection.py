import grpc
from concurrent import futures
import redis
import io
import time
import json
import numpy as np
from PIL import Image
import dlib
import aggregator_pb2
import aggregator_pb2_grpc
import logging
import os

# Configure logging
logging.basicConfig(filename='landmark_detection.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s:%(message)s')

class LandmarkDetectionService(aggregator_pb2_grpc.LandmarkDetectionServicer):
    def __init__(self, redis_url):
        self.redis_client = redis.StrictRedis.from_url(redis_url)
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    def DetectLandmarks(self, request, context):
        try:
            image_data = request.image
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            img = np.array(image)
            faces = self.detector(img, 1)
            landmarks = {}
            for idx, face in enumerate(faces):
                shape = self.predictor(img, face)
                landmark_points = [(p.x, p.y) for p in shape.parts()]
                landmarks[idx] = landmark_points
            image_hash = hash(image_data)
            self.redis_client.set(image_hash, json.dumps(landmarks))

            logging.info("Landmarks detected")

            # Constructing the gRPC LandmarkResponse message
            landmark_response = aggregator_pb2.LandmarkResponse()
            for idx, points in landmarks.items():
                landmark = landmark_response.landmarks[idx]
                for (x, y) in points:
                    point = landmark.points.add()
                    point.x = x
                    point.y = y

            # If age/gender already provided, send to Data Storage Service
            age_gender = self.redis_client.get(f"{image_hash}_age_gender")
            if age_gender:
                self.send_to_data_storage(image_data, image_hash)
            return landmark_response
        except Exception as e:
            logging.error(f"Error in DetectLandmarks: {e}")
            context.set_details('Internal error')
            context.set_code(grpc.StatusCode.INTERNAL)
            return aggregator_pb2.LandmarkResponse()

    def send_to_data_storage(self, image_data, image_hash):
        try:
            channel = grpc.insecure_channel('localhost:5003')
            stub = aggregator_pb2_grpc.DataStorageStub(channel)
            stub.StoreData(aggregator_pb2.DataRequest(image=image_data, redis_key=image_hash))
        except Exception as e:
            logging.error(f"Error in send_to_data_storage: {e}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    redis_url = os.getenv('REDIS_URL', "redis://localhost:6379/0")
    aggregator_pb2_grpc.add_LandmarkDetectionServicer_to_server(LandmarkDetectionService(redis_url), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logging.info('LandmarkDetection server started on port 5001')
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
