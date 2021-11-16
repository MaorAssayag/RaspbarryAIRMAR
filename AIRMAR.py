import socket, pynmea2
from pynmea2 import XDR,MWV
from time import sleep  
import logging
from logging.handlers import RotatingFileHandler
from logging import handlers
import sys
from threading import Thread
from prometheus_client import start_http_server, Gauge
from logging.handlers import RotatingFileHandler

# Prometheus metrics
HTTP_PORT = 4090
AIRMAR_BAROMETER = Gauge('AIRMAR_BAROMETER', 'BAROMETER')
AIRMAR_TWS = Gauge('AIRMAR_TWS', 'BAROMETER')
AIRMAR_TWA = Gauge('AIRMAR_TWA', 'BAROMETER')
AIRMAR_TEMPERATURE = Gauge('AIRMAR_TEMPERATURE', 'BAROMETER')

# Global values
AIRMAR_BAROMETER_CURR = 0
AIRMAR_TWS_CURR = 0
AIRMAR_TWA_CURR = 0
AIRMAR_TEMPERATURE_CURR = 0

connected = False

def isRelevantSentence(line):
    return any(line.startswith(s) for s in ["$IIXDR", "$WIMWV"])

def parseNMEA(sentence):
    global AIRMAR_BAROMETER_CURR, AIRMAR_TWS_CURR, AIRMAR_TWA_CURR, AIRMAR_TEMPERATURE_CURR
    logging.debug(sentence)
    parsed = pynmea2.parse(sentence)
    if (type(parsed) is XDR):
        AIRMAR_BAROMETER_CURR = float(parsed.data[13]) * 1000
        AIRMAR_TEMPERATURE_CURR = float(parsed.value)
        
    elif (type(parsed) is MWV):
        AIRMAR_TWA_CURR = float(parsed.wind_angle)
        AIRMAR_TWS_CURR = float(parsed.wind_speed)
        

def initLogger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("/home/pi/Documents/dev/debug.log"),
                  logging.StreamHandler(),
                  RotatingFileHandler("/home/pi/Documents/dev/debug.log", maxBytes=10*1024*1024, backupCount=2)])

def initSocket():
    # configure socket and connect to server
    #socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(3)

def main():
    global connected
    
    initSocket()
    host = '192.168.76.1' 
    port = 10110

    while not connected:   
        # attempt to connect
        try:
            logging.info("Trying to connect %s:%s..." %(host,port) )
            clientSocket = socket.socket() 
            clientSocket.connect( ( host, port ) )
            connected = True
        except Exception:
            logging.error("Failed to connect, trying again in 5s..")
            sleep(5)
            
    logging.info( "Connected to server successfully %s:%s" %(host,port)  )  
      
    while True:  
        # attempt to send and receive wave, otherwise reconnect  
        try:  
            message = clientSocket.recv( 1024 ).decode( "UTF-8" )  
            for line in message.splitlines():
                if (isRelevantSentence(line)):
                    parseNMEA(line)

        except socket.error:  
            # set connection status and recreate socket  
            connected = False  
            logging.warning( "connection lost... reconnecting" )  
            while not connected:  
                # attempt to reconnect, otherwise sleep for 2 seconds  
                try:
                    clientSocket = socket.socket() 
                    clientSocket.connect( ( host, port ) )  
                    connected = True  
                    logging.info( "re-connection successful" )  
                except Exception:
                    logging.error("Failed to connect, trying again in 5s..")
                    sleep(5)  

    logging.info("Closing connection..")
    clientSocket.close();

def updateGauges():
    global AIRMAR_BAROMETER_CURR, AIRMAR_TWS_CURR, AIRMAR_TWA_CURR, AIRMAR_TEMPERATURE_CURR, connected
    if (connected):
        AIRMAR_BAROMETER.set(AIRMAR_BAROMETER_CURR)
        AIRMAR_TEMPERATURE.set(AIRMAR_TEMPERATURE_CURR)
        AIRMAR_TWA.set(AIRMAR_TWA_CURR)
        AIRMAR_TWS.set(AIRMAR_TWS_CURR)
        logging.info("\nPublishing metrics: AIRMAR_BAROMETER=%0.2f, AIRMAR_TEMPERATURE=%0.2f, AIRMAR_TWA=%0.2f, AIRMAR_TWS=%0.2f\n" %(AIRMAR_BAROMETER_CURR,
                                                                                                            AIRMAR_TEMPERATURE_CURR,
                                                                                                            AIRMAR_TWA_CURR,
                                                                                                            AIRMAR_TWS_CURR))
    else:
        logging.info("Skipping publishing metrics..not connected to AIRMAR!")
        
def threaded_function():
    # Start up the server to expose the metrics.
    start_http_server(HTTP_PORT)
    # Generate some requests.
    while True:
        try: 
            updateGauges()
        except Exception as e:
            logging.error("Error while updating Gauges : %s" % str(e))
        sleep(5)

if __name__ == "__main__":
    initLogger()
    thread = Thread(target = threaded_function)
    thread.start()
    main()