import RPi.GPIO as GPIO
import os
import glob
import time

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

MAX_TEMP = 23.5
MIN_TEMP = 23.0

def get_temp():
    f = open('/sys/bus/w1/devices/28-000007550451/w1_slave')
    lines = f.readlines()
    f.close()
    t_pos = lines[1].find("t=")
    return float(lines[1][t_pos+2:t_pos+6]) / 100

try:
    TEMP_LED = 16
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(TEMP_LED, GPIO.OUT, initial=GPIO.LOW)
        
    while True:
        temp_c = get_temp()
        print temp_c

        if temp_c > MAX_TEMP:
            GPIO.output(TEMP_LED, GPIO.HIGH)
        else:
            GPIO.output(TEMP_LED, GPIO.LOW)

except KeyboardInterrupt:
    GPIO.cleanup()
        
