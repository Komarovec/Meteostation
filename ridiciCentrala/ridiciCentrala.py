from os import popen
from signal import signal, setitimer, SIGALRM, ITIMER_REAL
from time import sleep, localtime, strftime
from subprocess import call, check_output
from Adafruit_BMP085 import BMP085
from w1thermsensor import W1ThermSensor
from PIL import Image, ImageDraw, ImageFont
from RPi import GPIO

import Adafruit_SSD1306 as SSD
import paho.mqtt.client as mqtt

#Uklizeni portu
call("gpio unexportall", shell=True)

RST = None

#Display I2C init
disp = SSD.SSD1306_128_64(rst=RST)

#Rotacni Enkoder.. Pins, init
clk = 17
dt = 18
btn = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

lastClkState = GPIO.input(clk)

#BMP180 I2C Init
bmp = BMP085(0x77)

#DS18B20 1W Init
teplomer = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "051701cba1ff")

#Merene hodnoty RASPBERRY
teplotaBMP = 0
teplotaDLS = 0
tlak = 0
nadmorem = 0
teplotaCPU = 0

#Merene hodnoty ESP
svetloESP = 0
teplotaESP = 0
vlhkostESP = 0
nabitiESP = 0

#Merene hodnoty jineho tymu
teplotaOT = 0
teplotaOTTopic = "tym/22/teplota"

#Ostatni promenne
displayState = 0
sendInterval = 10
maxState = 13

#Konstanty pro upravu textu
width = disp.width
height = disp.height
padding = 0
top = padding
bottom = height-padding
x = 0
fontSize = 12

#Inicializuje knihovnu pro display
disp.begin()

#Vymaze display
disp.clear()
disp.display()

#Vytvori nove okno pro vykreslovani
image = Image.new('1', (width, height))

#Vytvori kreslici objekt
draw = ImageDraw.Draw(image)

#Vykresli cerny plny obdelnik
draw.rectangle((0,0,width,height), outline=0, fill=0)

#Fonty stazeny z https://www.dafont.com/bitmap.php
#font = ImageFont.load_default()
font = ImageFont.truetype('retron2000.ttf', fontSize)

#Kontrolni promena pro vykreslovani
#Kontroluje jestli bylo vykresleni dokonceno
isDrawing = False

#Zjisteni a ulozeni IP
IP = check_output("hostname -I | cut -d\' \' -f1", shell = True)

# Funkce pro pripojeni k lokalnimu MQTT serveru
def on_local_connect(client, userdata, flags, rc):
    print("Connected to local MQTT server: "+str(rc))
    client.subscribe("meteo1/#")

# Funkce pro zpracovani zprav z lokalniho MQTT serveru
def on_local_message(client, userdata, msg):
    global svetloESP, teplotaESP, vlhkostESP, nabitiESP
    if(msg.topic == "meteo1/light"):
        svetloESP = float(msg.payload)
    elif(msg.topic == "meteo1/temp"):
        teplotaESP = float(msg.payload)
    elif(msg.topic == "meteo1/humd"):
        vlhkostESP = float(msg.payload)
    elif(msg.topic == "meteo1/bat"):
        nabitiESP = int(msg.payload)

# Funkce pro pripojeni k souteznimu MQTT serveru
def on_remote_connect(client, userdata, flags, rc):
    global connection
    print("Connected to remote MQTT server: "+str(rc))
    client.subscribe(teplotaOTTopic)
    if(rc == 0):
        connection = "OK"
        IP = check_output("hostname -I | cut -d\' \' -f1", shell = True)
    else:
        connection = "No connection"

# Funkce pro zpracovani zprav z souteznimu MQTT serveru
def on_remote_message(client, userdata, msg):
    global teplotaOT
    if(msg.topic == teplotaOTTopic):
        teplotaOT = float(msg.payload)
    #Zpracovani topicu pri aktualizaci

# Funkce pro vypsani chyby pri odpojeni
def on_remote_disconnect(unused_client, unused_userdata, rc):
    global connection
    print("Disconnection reason: ", error_str(rc))
    connection = "No connection"

#Funkce pro obnoveni displaye
def drawDisplay():
    global isDrawing, connection
    
    if(isDrawing): #Pokud zrovna vykresluje, nevykresluj
        return
    else:
        isDrawing = True
    
    #Vymazani displaye (prekresleni na cerny obdelnik)
    draw.rectangle((0,0,width,height), outline=0, fill=0)
        
    #Vykreslovani textu --> Senzory raspberry
    if(displayState == 0):
        vypisText(1, "Temp BMP:")
        vypisText(2, "%.2f C" % teplotaBMP)
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 1):
        vypisText(1, "Temp DLS:")
        vypisText(2, "%.2f C" % teplotaDLS)
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 2):
        vypisText(1, "Temp CPU:")
        vypisText(2, "%.2f C" % teplotaCPU)
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 3):
        vypisText(1, "Tlak:")
        vypisText(2, "%.2f hPa" % (tlak/100))
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 4):
        vypisText(1, "MNM:")
        vypisText(2, "%.2f m" % nadmorem)
        vypisText(4, str(displayState)+"/"+str(maxState))

    #Vykreslovani textu --> Dodatecne info
    elif(displayState == 5):
        vypisText(1, "Cas:")
        vypisText(2, strftime("%H:%M:%S", localtime()))
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 6):
        vypisText(1, "Datum:")
        vypisText(2, strftime("%d.%m.%Y",localtime()))
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 7):
        vypisText(1, "IP:")
        vypisText(2, IP)
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 8):
        vypisText(1, "Status pripojeni:")
        vypisText(2, connection)
        vypisText(4, str(displayState)+"/"+str(maxState))

    #Vykreslovani textu --> Senzory meteostanice
    elif(displayState == 9):
        vypisText(1, "Temp Meteost.:")
        vypisText(2, "%.2f C" % teplotaESP)
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 10):
        vypisText(1, "Humd Meteost.:")
        vypisText(2, "%.2f pr" % vlhkostESP)
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 11):
        vypisText(1, "Svetlo Meteost.:")
        vypisText(2, "%.2f lux" % svetloESP)
        vypisText(4, str(displayState)+"/"+str(maxState))
    elif(displayState == 12):
        vypisText(1, "Baterie Meteost.:")
        vypisText(2, "%d procent" % nabitiESP)
        vypisText(4, str(displayState)+"/"+str(maxState))

    #Vykreslovani textu --> Hodnoty jineho tymu
    elif(displayState == 13):
        vypisText(1, "Tep. jineho tymu:")
        vypisText(2, "%.2f C" % teplotaOT)
        vypisText(4, str(displayState)+"/"+str(maxState))

    #Vykresleni     
    disp.image(image)
    disp.display()
    isDrawing = False

#Funkce pro zjisteni teploty
def getCpuTemp():
        temp = popen("vcgencmd measure_temp").readline()
        temp = temp.replace("temp=","")
        temp = temp.replace("'C\n","")
        return temp

#Funkce pro zjednoduseni vypisu
def vypisText(radek, txt):
    draw.text((x,top+(radek*fontSize)), txt, font=font, fill=255)

#Funkce na zjisteni hodnot
def getValues():
    global teplotaBMP, teplotaDLS, tlak, nadmorem, teplotaCPU
    teplotaBMP = bmp.readTemperature()
    teplotaDLS = teplomer.get_temperature()
    teplotaCPU = float(getCpuTemp())
    tlak = bmp.readPressure()
    nadmorem = bmp.readAltitude(102930)
    
#Funkce pro rotacni enkoder
def encoderCallback(channel):
    global lastClkState, displayState, maxState
    clkState = GPIO.input(clk)
    if(lastClkState != clkState):
        if(clkState != GPIO.input(dt)):
            if(displayState == maxState):
                displayState = 0
            else:
                displayState += 1
        else:
            if(displayState == 0):
                displayState = maxState
            else:
                displayState -= 1
    lastClkState = clkState
    drawDisplay()

#Funkce volajici v pravidelnem intervalu, pro posilani dat
def catcher(signum, _):
    global connection, teplotaDLS, teplotaBMP, tlak
    #Poslani hodnot merenych na raspberry
    mqttRemote.publish("tym/2/tempds", str(teplotaDLS))
    mqttRemote.publish("tym/2/tempbmp", str(teplotaBMP))
    mqttRemote.publish("tym/2/presbmp", str(tlak/100))
    mqttRemote.publish("tym/2/tempcpu", str(teplotaCPU))
    mqttRemote.publish("tym/2/altitude", str(nadmorem))

    #Poslani hodnot merenych na meteostanici
    mqttRemote.publish("tym/2/tempmeteo", str(teplotaESP))
    mqttRemote.publish("tym/2/humdmeteo", str(vlhkostESP))
    rc = mqttRemote.publish("tym/2/svetlometeo", str(svetloESP))

    #Test pripojeni z navratove hodnoty publishe
    if(rc[0] != 0):
        connection = "No connection"
    else:
        conneciton = "OK"

#Detekce pohybu enkoderu
GPIO.add_event_detect(clk, GPIO.BOTH, callback=encoderCallback, bouncetime=30)

#Nastaveni casoveho budice
signal(SIGALRM, catcher)
setitimer(ITIMER_REAL, sendInterval, sendInterval)

#Nastaveni MQTT Local
mqttLocal = mqtt.Client("localClient")
mqttLocal.on_connect = on_local_connect
mqttLocal.on_message = on_local_message

#Asynchroni komunikace s lokalnim MQTT brokerem
mqttLocal.connect_async("localhost", 1883, 60)
mqttLocal.loop_start()

connection = "No connection"

#Nastaveni MQTT Soutezniho brokeru
mqttRemote = mqtt.Client("remoteClient")
mqttRemote.on_connect = on_remote_connect
mqttRemote.on_message = on_remote_message
mqttRemote.on_disconnect = on_remote_disconnect
mqttRemote.username_pw_set(username="",password="")
mqttRemote.tls_set("/etc/ssl/certs/ca-certificates.crt")

#Asynchroni komunikace se vzdalenym MQTT brokerem
mqttRemote.connect_async("mqtt.nag-iot.zcu.cz", 8883, 60)
mqttRemote.loop_start()


try:
    #Hlavni smycka
    while True:    
        #Volani Funkci
        getValues()
        drawDisplay()
        
        #Update kazdou pul sekundu
        sleep(.5)

        

#Vycisteni portu..
except KeyboardInterrupt:
    GPIO.cleanup()
GPIO.cleanup()
