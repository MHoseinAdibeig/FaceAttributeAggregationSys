import grpc
import aggregator_pb2
import aggregator_pb2_grpc
import logging

# Configure logging
logging.basicConfig(filename='input_service.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s:%(message)s')

def readImage(img_path):
    try:
        with open(img_path, "rb") as image:
            img = image.read()
            logging.info("Image read successfully")
            return img
    except Exception as e:
        logging.error(f"Error in readImage: {e}")
        return None

def send_to_services(image_data):
    try:
        # Send to Landmark Detection Service
        channel = grpc.insecure_channel('localhost:5001')
        stub = aggregator_pb2_grpc.LandmarkDetectionStub(channel)
        response = stub.DetectLandmarks(aggregator_pb2.ImageRequest(image=image_data))
        logging.info("Landmark Detection Response: %s", response)

        # Send to Age/Gender Estimation Service
        channel = grpc.insecure_channel('localhost:5002')
        stub = aggregator_pb2_grpc.AgeGenderEstimationStub(channel)
        response = stub.EstimateAgeGender(aggregator_pb2.ImageRequest(image=image_data))
        logging.info("Age/Gender Estimation Response: %s", response)
    except Exception as e:
        logging.error(f"Error in send_to_services: {e}")

if __name__ == "__main__":
    image_data = readImage("./data/SingleFace.jpg")
    if image_data:
        send_to_services(image_data)
