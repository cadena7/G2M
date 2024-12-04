
import time
import RPi.GPIO as GPIO

RPI_Pin = 18                     # define the RPI GPIO Pin we will use with PWM (PWM)
RPI_DutyCycle = 50               # define the Duty Cycle in percentage  (50%)
RPI_Freq = 500                   # define the frequency in Hz (500Hz)
RPI_LEDTime = 60                 # the time you want the LED to stay lit for (secs)
GPIO.setmode(GPIO.BCM)              # set actual GPIO BCM Numbers
GPIO.setup(RPI_Pin, GPIO.OUT)         # set RPI_PIN as OUTPUT mode
GPIO.output(RPI_Pin, GPIO.LOW)        # set RPI_PIN LOW to at the start
pwmobj = GPIO.PWM(RPI_Pin, RPI_Freq)  # Initialise instance and set Frequency
pwmobj.start(0)

print("al 20%")
pwmobj.ChangeDutyCycle(20)
time.sleep(10)
print("al 60%")
pwmobj.ChangeDutyCycle(60)
time.sleep(10)
