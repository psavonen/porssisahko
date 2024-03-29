import requests
from RPLCD import i2c
from time import sleep
import json
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import pytz
import threading

running = True
lcdmode = 'i2c'
cols = 16
rows = 2
charmap = 'A00'
i2c_expander = 'PCF8574'
address = 0x27
port = 1

lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap, cols=cols, rows=rows)

utc = pytz.UTC
api_url = "https://api.porssisahko.net/v1/latest-prices.json"

singleyear = datetime.utcnow().strftime("%Y")
date = datetime.now(timezone.utc)
nyt_str = date.strftime("%Y-%m-%dT%H:%M:%S")
date = datetime.strptime(nyt_str, "%Y-%m-%dT%H:%M:%S")
date = date.replace(tzinfo=ZoneInfo("Europe/Helsinki"))
# Asettakaa raspin kello oikeaan aikaan :D
#date + timedelta(hours=2)
sekohinta = [],[],[]
spothinta = 0
ylinhinta = 0
alinhinta = 0
ylinhintaaika = 0
alinhintaaika = 0
nyt_aika = 0
ISOVIIVE = 43200
SPOTVIIVE = 3600
LCDVIIVE = 6
j = 0

def getTime():
    nyt_utc = datetime.strptime(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "%Y-%m-%dT%H:%M:%S.%fZ")
    nyt_vali = nyt_utc.replace(tzinfo=ZoneInfo('UTC'))
    nyt_oikea = nyt_vali.astimezone(ZoneInfo('Europe/Helsinki'))
    return nyt_oikea

def timeFinder(target):
    return datetime.strptime(target, "%Y-%m-%dT%H:%M:%S.%fZ")

nyt_aika = getTime()

def main_price_thread():
    global ylinhinta
    global alinhinta
    global ylinhintaaika
    global alinhintaaika
    global spothinta
    global nyt_aika
    try:
        while(running):
            print("Main price start")
            response = requests.get(api_url)
            y = json.loads(response.text)
            nyt_oikea = getTime()
            for i in y['prices']:
                alinhinta_t = timeFinder(i['startDate'])
                ylinhinta_t = timeFinder(i['endDate'])
                alinhinta_t = utc.localize(alinhinta_t)
                ylinhinta_t = utc.localize(ylinhinta_t)

                hinta = float(i['price'])
                if(alinhinta_t > nyt_oikea and ylinhinta_t > nyt_oikea):
                    sekohinta[0].append(hinta)
                if(alinhinta_t > nyt_oikea):
                    sekohinta[1].append(timeFinder(i['startDate']))
                if(ylinhinta_t > nyt_oikea):
                    sekohinta[2].append(timeFinder(i['endDate']))

            alinhinta = min(sekohinta[0])
            ylinhinta = max(sekohinta[0])

            alinhintaaikaindex = sekohinta[0].index(alinhinta)
            alinhintaaika = sekohinta[1][alinhintaaikaindex]

            ylinhintaaikaindex = sekohinta[0].index(ylinhinta)
            ylinhintaaika = sekohinta[1][ylinhintaaikaindex]
            sleep(ISOVIIVE)
    except Exception as e: 
       print(e)

def spot_price_thread():
    global spothinta
    global nyt_aika
    try:
        while(running):
            print("Spot price start")
            nyt_aika = getTime()
            singledate = datetime.utcnow().strftime("%Y-%m-%d")
            singlehour = nyt_aika.strftime("%H")
            spot_url  = "https://api.porssisahko.net/v1/price.json?date="
            spot_url += singledate
            spot_url += "&hour="
            spot_url += singlehour
            spotresponse = requests.get(spot_url)
            o = json.loads(spotresponse.text)
            spothinta = o['price']
            print("Spothinta ", spothinta, " ", nyt_aika)
            sleep(SPOTVIIVE)
    except Exception as e: 
       print(e)

def price_print_thread():
    global spothinta
    global ylinhinta
    global alinhinta
    global ylinhintaaika
    global alinhintaaika
    global nyt_oikea
    global nyt_aika
    while(running):
        try:
            nytaika = nyt_aika.strftime("%d-%m %H:%M")
            ylinaikapress = datetime.strptime(str(ylinhintaaika), "%Y-%m-%d %H:%M:%S")
            alinaikapress = datetime.strptime(str(alinhintaaika), "%Y-%m-%d %H:%M:%S")
            ylinaikapress = ylinaikapress.astimezone(ZoneInfo('Europe/Helsinki'))
            alinaikapress = alinaikapress.astimezone(ZoneInfo('Europe/Helsinki'))
            ylinaikapress = ylinaikapress.strftime("%d-%m %H:%M")
            alinaikapress = alinaikapress.strftime("%d-%m %H:%M")
            nythinta = "Nyt: " + str(spothinta) + "       " + str(nytaika)
            ylinhintaprint = "Ylin: " + str(ylinhinta) + "     " + str(ylinaikapress).replace(str(singleyear) + "-", "")
            alinhintaprint = "Alin: " + str(alinhinta) + "      " + str(alinaikapress).replace(str(singleyear) + "-", "")
            lcd.clear()
            lcd.write_string(nythinta)
            sleep(LCDVIIVE)
            lcd.clear()
            lcd.write_string(ylinhintaprint)
            sleep(LCDVIIVE)
            lcd.clear()
            lcd.write_string(alinhintaprint)
            sleep(LCDVIIVE)
        except Exception as e: 
            print(e)
if __name__ == "__main__":
    s = threading.Thread(target=main_price_thread, args=())
    d = threading.Thread(target=spot_price_thread, args=())
    f = threading.Thread(target=price_print_thread, args=())
    s.start()
    d.start()
    f.start()




