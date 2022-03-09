import Adafruit_DHT
import RPi.GPIO as GPIO
import subprocess
import os
import json
import time
import subprocess
import paho.mqtt.client as mqtt
from datetime import datetime
import argparse
import statistics
import math

PATH_TO_MITEMP_FOLDER = "/home/pi/temperature/mitemp"
XIAOMI_THERMOSTAT_MAC = "4c:65:a8:da:89:e9"
MQTT_TOPIC = "ambient/andreaBedroom"

parser = argparse.ArgumentParser(description='')
parser.add_argument("-c", "--client", type=str, default = 'MQTT_XIAOMI_THERMOSTAT', help='name of the mqtt client')
parser.add_argument("-p", "--path", type=str, default = PATH_TO_MITEMP_FOLDER, help='path of the mitemp folder')
parser.add_argument("-m", "--mac", type=str, default = XIAOMI_THERMOSTAT_MAC, help='mac address of the client')
parser.add_argument("-t", "--topic", type=str, default = MQTT_TOPIC, help='mqtt topic to use')

args = parser.parse_args()

# ------------------- START  CONFIGURATION ------------------- #

MQTT_SERVER_ADDRESS = "mqtt.server.com" # or IP address
MQTT_SERVER_PORT = 1883

# --------- BOARD CONFIGURATION ---------- #

TEMP_LED = 11
INTERNET_CONN_LED = 12
HUM_LED = 13

# ------------ THRESH ------------- #

HUM_MAX_TRESH = 55
HUM_MIN_TRESH = 40

TEMP_MAX_THRES = 25
TEMP_MIN_THRES = 20

# ----------- TIMINGS ------------ #

# sleep time between temperature reports
LOOP_TIMEOUT = 150

# set these in order to turn off the led's at night 
LEDs_OFF_START_HOUR = -1
LEDs_OFF_END_HOUR = 25

# --------- RECONNECTIONS ---------- #

MAX_BLE_RETRIES = 3

# --------- LED BRIGHTNESS ---------- #

# i connected the leds directly to the 3v3 rail, if you want to power them from the pin invert these values
LED_BRIGHTNESS_HIGH = 100
LED_BRIGHTNESS_LOW = 0

# ------------------- END CONFIGURATION ------------------- #


MOSQUITO_CLIENT_NAME = args.client
COMMAND = "python3" + str(args.path) + "/demo.py --backend bluepy poll_json" + str(args.mac)

GPIO.setmode(GPIO.BOARD)

GPIO.setup(HUM_LED, GPIO.OUT)
GPIO.setup(TEMP_LED, GPIO.OUT)
GPIO.setup(INTERNET_CONN_LED, GPIO.OUT)

HUM_LED_PWM = GPIO.PWM(HUM_LED,10)
TEMP_LED_PWM = GPIO.PWM(TEMP_LED,10)
INTERNET_CONN_LED_PWM = GPIO.PWM(INTERNET_CONN_LED,10)

HUM_LED_PWM.start(0)
TEMP_LED_PWM.start(0)
INTERNET_CONN_LED_PWM.start(0)

HUM_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_HIGH)
TEMP_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_HIGH)
INTERNET_CONN_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_HIGH)


def calculate_dew_point(T,RH):
  b = 17.62
  c = 243.12

  def gamma_func(T,RH,b,c):
      return math.log(RH/100) + (b * T)/(c + T)
  
  try:
    return float((c*gamma_func(T,RH,b,c)) / (b - gamma_func(T,RH,b,c)))
  except:
    return -10
   
def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))
    pass

def on_publish(mqttc, obj, mid):
    #print("mid: "+str(mid))
    pass

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))
        
def on_message(client, userdata, msg):
  msg_payload_decoded = msg.payload.decode("utf-8")
  print("Message received-> " + msg.topic + " " + str(msg_payload_decoded))
  
  
def on_disconnect(client, userdata, rc):
    connect_to_broker()
    
def connect_to_broker():
    not_connected = True
    while not_connected:
      try:
        client.connect(MQTT_SERVER_ADDRESS, port=MQTT_SERVER_PORT)
        not_connected = False
        print(datetime.now())
        print('Im connected')
        #client.subscribe("esp32/dht/#")
        time.sleep(5)
      except:
        print(datetime.now())
        print('Failed connection')
        time.sleep(15)
  
      
client = mqtt.Client(MOSQUITO_CLIENT_NAME)
connect_to_broker()
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_subscribe = on_subscribe
client.loop_start()

cumulative_ble_retry = 0

while True:
  try:
            hum_min_flag = False
            temp_min_flag = False  
              
            mi_ble_has_connected = False
            
            for i in range(3):
              try:
                json_string = os.popen(COMMAND).read()
                obj = json.loads(json_string)
                mi_ble_has_connected = True
                cumulative_ble_retry = 0
                break
              except:
                cumulative_ble_retry += 1
                time.sleep(15) 
                pass
              
            
            if cumulative_ble_retry == MAX_BLE_RETRIES:
              json_string = os.popen("sudo reboot")
              time.sleep(15)
              
            
            res = subprocess.call(['ping', '-c', '1', MQTT_SERVER_ADDRESS], stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
            
            if res is not 0:
              INTERNET_CONN_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_HIGH)
              continue
            else:
              INTERNET_CONN_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_LOW)
            
            client.publish(str(args.topic) + "/temperature",str(obj['temp']))
            client.publish(str(args.topic) + "/humidity",str(obj['hum']))
            client.publish(str(args.topic) + "/battery",str(obj['battery']))
            client.publish(str(args.topic) + "/dew_point", "{:.1f}". format(calculate_dew_point(obj['temp'],obj['hum'])))
               
            
            if datetime.now().hour <= LEDs_OFF_START_HOUR and datetime.now().hour >= LEDs_OFF_END_HOUR:
              if obj['temp'] >= TEMP_MAX_THRES:
                TEMP_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_HIGH)
              elif obj['temp'] <= TEMP_MIN_THRES:
                temp_min_flag = True
              else:
                TEMP_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_LOW)
  
              if obj['hum'] >= HUM_MAX_TRESH:
                HUM_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_HIGH)
              elif obj['hum'] <= HUM_MIN_TRESH:
                hum_min_flag = True
              else:
                HUM_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_LOW)
                        
                
              if hum_min_flag or temp_min_flag:
                for i in range(50):
                
                  if temp_min_flag:
                    TEMP_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_HIGH)
                  if hum_min_flag:
                    HUM_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_HIGH) 
                  time.sleep(0.5)
                  
                  if temp_min_flag:
                    TEMP_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_LOW)
                  if hum_min_flag:
                    HUM_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_LOW) 
                  time.sleep(0.5)
                  
              else:
                time.sleep(LOOP_TIMEOUT)

            else:
              TEMP_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_LOW)
              HUM_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_LOW)
              INTERNET_CONN_LED_PWM.ChangeDutyCycle(LED_BRIGHTNESS_LOW)
              time.sleep(LOOP_TIMEOUT)
            
                 
  except:
    time.sleep(15)
    
    
              