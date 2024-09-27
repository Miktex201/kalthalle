import website_host
import time
import pigpio
import wiegand
from doorcontrol import *
from threading import Thread
from queue import Queue
from datenauswertung import *
pi = pigpio.pi()


  

def main():
    def callback(bits, value):
        print("bits={} value={}".format(bits, value))
        #wenn es sich um einen Code handelt



        #wenn es sich um einen Chip handelt
        if bits == 26:
            if chipcode_in_data(value):
                tür_steuerung.öffnen()
                benutzername = user_in_data(value)
                login_write(value)
                log_write("Die Person %s mit dem Chipcode:%s hat die Tuere geoeffnet." %(benutzername, value))


    pi.set_mode(18, pigpio.OUTPUT)

    w = wiegand.decoder(pi, 14, 15, callback)
    

    time.sleep(1000)



tür_steuerung = TürSteuerung()
tür_steuerung.start()
main_programm = Thread(target=main)
main_programm.start()
website = Thread(target=website_host.start_website(True))
website.start()



