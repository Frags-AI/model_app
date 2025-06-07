import cv2
from config import settings

DEFAULT_CLASS_LABELS = [
    "gunshot", "grenade_throw", "knife_attack", "multiple_kills", "reload",
    "headshot", "sniper_shot", "pistol_shot", "explosion", "death",
    "heal", "revive", "crouch", "jump", "sprint",
    "capture_flag", "use_medkit", "use_shield", "taunt", "pickup_item"
]

class YOLOModel():
    def __init__(self, weights_path, cfg_path, class_labels):
        self.class_labels = class_labels
        self.net = cv2.dnn.readNet(weights_path, cfg_path)
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers().flatten()]

    def get_model(self):
        return self.net
    
    def get_layers(self):
        return self.output_layers
    
    def get_class_labels(self):
        return self.class_labels
    
    def get_details(self):
        return self.net, self.output_layers, self.class_labels
    
    def destroy(self):
        del self.net
        del self.output_layers
        del self.class_labels
    
def load_yolo_model():
    return YOLOModel(settings.WEIGHT_PATH, settings.CFG_PATH, DEFAULT_CLASS_LABELS)