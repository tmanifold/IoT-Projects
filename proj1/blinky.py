import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT, initial=GPIO.LOW)



#while true:
#   if btnPressed:
#       blink_speed = increase_blink_speed()
#        blink(11, t)

#def blink(pin, wait_time):
#            GPIO.output(pin, GPIO.HIGH)
#            sleep(wait_time)
#            GPIO.output(pin, GPIO.LOW)
#            sleep(wait_time)

while True:
    
    blink_duration = 3.0
    
    for i in range(5, 0, -1):
        
        #print("i = %d" % i)
        
        blink_duration = i/10.0
        
        #print ("blink_duration = %f" % blink_duration)
        
        for j in range(0, 3):
            
            #print("j = %d" % j)
            
            GPIO.output(11, GPIO.HIGH)
            
            sleep(blink_duration)
            
            GPIO.output(11, GPIO.LOW)
            
            sleep(blink_duration)
        
#
#while True:
#    GPIO.output(11, GPIO.HIGH)
#    sleep(1)
#    GPIO.output(11, GPIO.LOW)
#    sleep(1)
