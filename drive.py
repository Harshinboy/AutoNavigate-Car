import socketio
import eventlet
import numpy as np
from flask import Flask
from keras.models import load_model
from keras.losses import MeanSquaredError
import base64
from io import BytesIO
from PIL import Image
import cv2

# Initialize the socketio server
sio = socketio.Server()

# Initialize Flask app
app = Flask(__name__)

# Speed limit
speed_limit = 10

# Image preprocessing function
def img_preprocess(img):
    img = img[60:135, :, :]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img / 255
    return img

# Define telemetry event
@sio.on('telemetry')
def telemetry(sid, data):
    if data:
        speed = float(data['speed'])
        image = Image.open(BytesIO(base64.b64decode(data['image'])))
        image = np.asarray(image)
        image = img_preprocess(image)
        image = np.array([image])
        steering_angle = float(model.predict(image))
        throttle = 1.0 - speed / speed_limit
        print('{} {} {}'.format(steering_angle, throttle, speed))
        send_control(steering_angle, throttle)
    else:
        # If no data is received, just send control with 0 values
        send_control(0, 0)

# Define connect event
@sio.on('connect')
def connect(sid, environ):
    print('Connected')
    send_control(0, 0)

# Send control commands to the simulator
def send_control(steering_angle, throttle):
    sio.emit('steer', data={
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })

# Main function
if __name__ == '__main__':
    # Load the model with custom objects
    model = load_model('model.h5', custom_objects={'mse': MeanSquaredError()})

    # Wrap Flask application with socketio's middleware
    app = socketio.WSGIApp(sio, app)

    # Deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)
