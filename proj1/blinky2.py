import threading
from time import sleep
import RPi.GPIO as GPIO

LED_RED = 11
LED_BLUE = 15
BTN_FREQ = 31
BTN_SEL = 33

SLOW = 102
FAST = 101

btnSelector = FAST
btnFrequencyPressed = False
fast_hold = False
slow_hold = False

time_elapsed = 0

lock = threading.Lock()
hold_lock = threading.Lock()

def blink_timer():
    global time_elapsed
    global lock
    
    while True:
        #print time_elapsed
        sleep(1)
        lock.acquire()
        time_elapsed += 1
        lock.release()

def btnSelector_callback(pin):
    global btnSelector
    print ("Selector button pressed.")
    if btnSelector == FAST:
        btnSelector = SLOW
    elif btnSelector == SLOW:
        btnSelector = FAST

def btnFrequency_callback(pin):
    global btnSelector
    
    print ("Frequency button pressed.")
    global fast_hold
    global slow_hold
    global hold_lock

    hold_lock.acquire()
    # hold red LED
    if btnSelector == FAST:
        if fast_hold == False:
            fast_hold = True
        else:
            fast_hold = False
    # hold blue LED        
    elif btnSelector == SLOW:
        if slow_hold == False:
            slow_hold = True
        else:
            slow_hold = False
    hold_lock.release()
    
def blink_led (pin):

    global lock
    global time_elapsed
    global fast_hold
    global slow_hold
    global btnSelector
    
    if pin == LED_RED:
        blink_freq = 1.0
    elif pin == LED_BLUE:
        blink_freq = 0.5
        
    while True:

        if time_elapsed % 3 == 0:
            hold_lock.acquire()
            # reduce time between blinks for red LED
            if pin == LED_RED and fast_hold == False:
                blink_freq -= 0.2
                if blink_freq < 0.0:
                    blink_freq = 1.0
            # increase time between blinks for blue LED
            if pin == LED_BLUE and slow_hold == False:
                blink_freq += 0.2
                if blink_freq > 1.3:
                    blink_freq = 0.5
            hold_lock.release()
        
        GPIO.output(pin, GPIO.HIGH)
        sleep(blink_freq)
        GPIO.output(pin, GPIO.LOW)
        sleep(blink_freq)

try:    
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LED_RED, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_BLUE, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(BTN_SEL, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_FREQ, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(BTN_SEL, GPIO.RISING, callback=btnSelector_callback)
    GPIO.add_event_detect(BTN_FREQ, GPIO.RISING, callback=btnFrequency_callback)

    thread1 = threading.Thread(target=blink_led, args=(LED_RED,))
    thread2 = threading.Thread(target=blink_led, args=(LED_BLUE,))
    thread_timer = threading.Thread(target=blink_timer)

    thread1.start()
    thread2.start()
    thread_timer.start()

    thread1.join()
    thread2.join()
    thread_timer.join()
    
except KeyboardInterrupt:
        GPIO.cleanup()

GPIO.cleanup()
