**Face Attribute Aggregation System
This repository contains a microservices-based system for detecting faces, extracting
landmarks, estimating age and gender, and storing the results. The system is implemented using Flask, gRPC, and Redis.

Table of Contents
Features

Architecture

Setup

Environment Variables

Usage

Logging

Contributing

License

Features
Detects faces in images and extracts landmarks.

Estimates age and gender of faces.

Stores face attributes in Redis and saves data as JSON files.

Uses environment variables for configuration.

Logs action times for face detection and age/gender estimation.

Architecture
The system is divided into the following microservices:

Image Input Service: Reads image files and sends them to the Face Landmark Detection and Age/Gender Estimation services.

Face Landmark Detection Service: Detects faces in images and extracts landmarks. Stores landmarks in Redis and sends data to the Data Storage Service if age and gender data are available.

Age/Gender Estimation Service: Estimates age and classifies gender of faces. Stores results in Redis and sends data to the Data Storage Service if landmarks are available.

Data Storage Service: Receives image data and Redis keys from other services and saves the collected data as JSON files.

Setup
Prerequisites
Python 3.x

Redis

gRPC

Flask
