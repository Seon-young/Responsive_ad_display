import RPi.GPIO as gpio
import time
import datetime
import picamera
from google.cloud import vision
from google.cloud.vision import types
import io
import paho.mqtt.client as mqtt

mclient = mqtt.Client()
mclient.username_pw_set("root","root")
mclient.connect("m14.cloudmqtt.com",14079,3600)

def on_disconnect(client, userdata, rc) :
    if rc!=0:
        print "unexpected disconnection"

mclient.on_disconnect = on_disconnect

client = vision.ImageAnnotatorClient()

gpio.setmode (gpio.BCM)

trig = 13
echo = 19

print "start"

gpio.setup (trig, gpio.OUT)
gpio.setup (echo, gpio.IN)

def detect_label(path):
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.label_detection(image=image)
    labels = response.label_annotations
    #print("Labels: ")

    for label in labels:
        #print(label.description)
	mclient.publish("Label",label.description)
	time.sleep(1)

def detect_logos(path):
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.logo_detection(image=image)
    logos = response.logo_annotations
    #print('Logos:')

    for logo in logos:
        #print(logo.description)
	mclient.publish("Logo",logo.description)
	time.sleep(1)

try:
  while True:
    gpio.output (trig, False)
    time.sleep (0.5)

    gpio.output (trig, True)
    time.sleep (0.00001)
    gpio.output (trig, False)

    while gpio.input (echo) == 0:
      pulse_start = time.time ()

    while gpio.input (echo) == 1:
      pulse_end = time.time ()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17000
    distance = round (distance, 2)

    print "Distance:", distance, "cm"

    if(distance <= 30):
      with picamera.PiCamera() as camera: # the close() method is automatically called
        camera.resolution = (1024, 768)
        #camera.start_preview()
        # Camera warm-up time
        time.sleep(1)
	t = time.asctime(time.localtime(time.time()))
	filename = t + '.jpg'
	camera.capture(filename, resize=(320,240)) # capturing resized images
	print("#####logo#####")
	detect_logos(filename)
	print("#####label#####")
	detect_label(filename)
	
	
    elif(distance >= 60):
	mclient.publish("Basic","index")
	
    time.sleep(3)
    
except KeyboardInterrupt:
  gpio.cleanup ()
  mclient.disconnect()
