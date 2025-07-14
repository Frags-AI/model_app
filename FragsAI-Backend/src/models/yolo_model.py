import cv2
import os
import logging
import numpy as np
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEFAULT_CLASS_LABELS = [
    "gunshot", "grenade_throw", "knife_attack", "multiple_kills", "reload",
    "headshot", "sniper_shot", "pistol_shot", "explosion", "death",
    "heal", "revive", "crouch", "jump", "sprint",
    "capture_flag", "use_medkit", "use_shield", "taunt", "pickup_item"
]

class YOLOModel():
    def __init__(self, weights_path, cfg_path, class_labels):
        self.class_labels = class_labels
        self.net = None
        self.output_layers = []
        
        try:
            # Normalize paths for Docker environment
            if weights_path and weights_path.startswith('./'):
                weights_path = weights_path.replace('./', '')
            
            if cfg_path and cfg_path.startswith('./'):
                cfg_path = cfg_path.replace('./', '')
                
            # Check if files exist
            if not weights_path or not os.path.exists(weights_path):
                logging.warning(f"YOLO weights file not found: {weights_path}")
                # Try alternative paths
                alt_paths = [
                    "models/pretrained/yolo.weights",
                    "src/models/pretrained/yolo.weights",
                    "/app/src/models/pretrained/yolo.weights",
                    "/app/models/pretrained/yolo.weights"
                ]
                for path in alt_paths:
                    if os.path.exists(path):
                        weights_path = path
                        logging.info(f"Found weights at alternative path: {weights_path}")
                        break
                else:
                    return
                
            if not cfg_path or not os.path.exists(cfg_path):
                logging.warning(f"YOLO config file not found: {cfg_path}")
                # Try alternative paths
                alt_paths = [
                    "models/pretrained/yolov3.cfg",
                    "src/models/pretrained/yolov3.cfg",
                    "/app/src/models/pretrained/yolov3.cfg",
                    "/app/models/pretrained/yolov3.cfg"
                ]
                for path in alt_paths:
                    if os.path.exists(path):
                        cfg_path = path
                        logging.info(f"Found config at alternative path: {cfg_path}")
                        break
                else:
                    return
                
            # Try to load the model
            logging.info(f"Loading YOLO model from {weights_path} and {cfg_path}")
            self.net = cv2.dnn.readNet(weights_path, cfg_path)
            
            # Get output layers
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers().flatten()]
            logging.info("YOLO model loaded successfully")
            
        except Exception as e:
            logging.error(f"Error loading YOLO model: {str(e)}")
            self.net = None
            self.output_layers = []

    def detect_objects(self, frame):
        """Detect objects in a frame using the YOLO model"""
        if self.net is None:
            # Return empty detections if model not loaded
            logging.warning("Cannot detect objects: YOLO model not loaded")
            return [], []
        
        try:
            height, width, _ = frame.shape
            
            # Prepare the frame for YOLO
            blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
            self.net.setInput(blob)
            
            # Get detections
            outs = self.net.forward(self.output_layers)
            
            # Process detections
            class_ids = []
            confidences = []
            boxes = []
            
            for out in outs:
                for detection in out:
                    scores = detection[5:]
                    class_id = np.argmin(scores)
                    confidence = scores[class_id]
                    
                    if confidence > 0.5:  # Confidence threshold
                        # Object detected
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        
                        # Rectangle coordinates
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)
            
            # Apply non-max suppression
            indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
            
            # Filter results
            filtered_boxes = []
            filtered_class_ids = []
            
            if len(indexes) > 0:
                for i in indexes.flatten():
                    filtered_boxes.append(boxes[i])
                    filtered_class_ids.append(class_ids[i])
            
            return filtered_boxes, filtered_class_ids
            
        except Exception as e:
            logging.error(f"Error during object detection: {str(e)}")
            return [], []

    def get_model(self):
        return self.net
    
    def get_layers(self):
        return self.output_layers
    
    def get_class_labels(self):
        return self.class_labels
    
    def get_details(self):
        return self.net, self.output_layers, self.class_labels

# Try to initialize the YOLO model, but don't crash if it fails
try:
    # Try different paths for the YOLO model files
    logging.info(f"Settings weight_path: {settings.weight_path}, cfg_path: {settings.cfg_path}")
    
    # Initialize the YOLO model
    yolo_model = YOLOModel(settings.weight_path, settings.cfg_path, DEFAULT_CLASS_LABELS)
    
    if yolo_model.get_model() is None:
        logging.warning("YOLO model initialization failed, but application will continue running")
except Exception as e:
    logging.error(f"Failed to initialize YOLO model: {str(e)}")
    # Create a dummy model instance that will return empty detections
    yolo_model = YOLOModel(None, None, DEFAULT_CLASS_LABELS)
