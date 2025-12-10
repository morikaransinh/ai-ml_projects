import tensorflow as tf
import numpy as np
import cv2
from tensorflow.keras.models import load_model


model = load_model('/kaggle/input/ml/scikitlearn/default/1/pollution_detector.h5')

n
class_names = ["Non-Pollution", "Pollution"]   

def predict_image(image_path):
    
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

   
    img = cv2.resize(img, (224, 224))

    
    img = img.astype("float32") / 255.0

    
    img = np.expand_dims(img, axis=0)

   
    pred = model.predict(img)[0][0]

    
    label = class_names[1] if pred >= 0.5 else class_names[0]

    print(f"Raw model output: {pred}")
    print(f"Predicted class: {label}")

    return label

predict_image("/kaggle/input/test-png/Screenshot 2025-12-10 151802.png")
