from PIL import Image, ImageDraw, ImageFont
import random
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import logging
import time 

#LCD DISPLAY

# from lib import LCD_2inch
# import spidev as SPI

# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 18
bus = 0 
device = 0 

logging.basicConfig(level=logging.DEBUG)
SCREEN_WIDTH=320
SCREEN_HEIGHT=240

user_agents = [
    # Windows - Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36",

    # Windows - Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",

    # Mac - Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.187 Safari/537.36",

    # Mac - Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15",

    # Linux - Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36",

    # Linux - Firefox
    "Mozilla/5.0 (X11; Linux x86_64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",

    # Android - Chrome Mobile
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.92 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.131 Mobile Safari/537.36",

    # iPhone - Safari Mobile
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",

    # iPad - Safari Mobile
    "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",

    # Android - Samsung Browser
    "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/20.0 Chrome/114.0.5735.196 Mobile Safari/537.36",
]

class DummyLCD:
    def Init(self):
        pass
    def clear(self):
        pass
    def bl_DutyCycle(self, val):
        print(f"Backlight set to {val}%")
    def ShowImage(self, image):
        image.show()
    def module_exit(self):
        pass

class tramInfo:
    def __init__(self, tram, destination, minutes, time, delayed):
        self.tram = tram
        self.destination = destination
        self.minutes = minutes
        self.time = time
        self.delayed = delayed
        
test_trams = [
 tramInfo(19, "Diemen Sniep", "4", "19:42", False ),
 tramInfo(24, "AzartPlein", "6", "19:45", True ),
]

def display_stamp(display):
    stamp = Image.open("Images/tramp_stamp.png")
    stamp = stamp.resize((SCREEN_WIDTH, SCREEN_HEIGHT))
    frame = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), "WHITE")
    frame.paste(stamp, (0, 0))
    display.ShowImage(frame)

def display_trams(display, trams):    
    frame = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), "WHITE")
    draw = ImageDraw.Draw(frame)        
    
    item_h = 60
    border = 1
    font_size = 20
    
    for i, tram in enumerate(trams):
        print(f"drawing tram {tram.tram}")
        ypos = item_h * i
        
        draw.rectangle((0, ypos ,SCREEN_WIDTH, ypos + item_h), fill = "BLACK")
        draw.rectangle((border, 
                        ypos + border,
                        SCREEN_WIDTH - (border * 2),
                        ypos + item_h - (2 * border)
                        ), fill="WHITE")
        
        font = ImageFont.truetype("./Font/Roboto-Regular.ttf", font_size)
        font_bold = ImageFont.truetype("./Font/Roboto-Bold.ttf", font_size)

        
        font_y = 20
        
        draw.text((5, ypos + font_y), str(tram.tram), fill="BLACK", font=font_bold)
        draw.text((35, ypos + font_y), tram.destination, fill="BLACK", font=font)    
        
        fill = "RED" if tram.delayed else "BLACK"
        draw.text((250, ypos + font_y), f"{tram.minutes} min", fill=fill, font=font)
    
    display.ShowImage(frame)
    
def fetch_trams(html):
    soup = BeautifulSoup(html, "html.parser")    
    ul_element = soup.find('ul', {'class': 'flex flex-col space-y-2'})
    
    trams = []
    if ul_element:
        for child in ul_element.find_all('li', recursive=False):
            tram_info = child.find_all('div')                
                    
            number = tram_info[0].text.strip()[4:]        
            destination = tram_info[1].text.strip()        
            busy = tram_info[2].text.strip()
            
            time_info = tram_info[3].find_all('div')        
            
            # how many minutes until tram
            minutes_unstripped = time_info[1].text.strip()        
            minutes = minutes_unstripped[0: minutes_unstripped.find('m')]                
            
            delayed = False
            if len(time_info) == 5:        
                arrival_time = time_info[4].text.strip() 
            elif len(time_info) == 6:
                delayed = True
                arrival_time = time_info[5].text.strip()                              
                
            trams.append(tramInfo(number, destination, minutes, arrival_time, delayed))
            
    return trams

def main():    
    try:
        display = DummyLCD()
                
        # display = LCD_2inch.LCD_2inch()        
        display.Init() # Initialize library.
        display.clear() #Clear display.
        display.bl_DutyCycle(50) # Set the backlight to 100

        # display loading tramp stamp
        display_stamp(display)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            context = browser.new_context(user_agent=random.choice(user_agents))
            page = context.new_page()
            
            page.goto('https://gvb.nl/en/travel-information/stop/9508073')
            page.wait_for_load_state('networkidle') 
        
            try:
                while(True):
                    trams = fetch_trams(page.content())        
                    display_trams(display, trams)    
                    time.sleep(2)
            except KeyboardInterrupt:
                print("KeyboardInterrupt received, closing browser...")
            finally:
                try:
                    context.close()
                except Exception as e:
                    print(f"Ignored error closing context: {e}")
                try:
                    browser.close()
                except Exception as e:
                    print(f"Ignored error closing browser: {e}")
                print("Cleanup done.")

    except IOError as e:
        logging.info(e)    
    
    except KeyboardInterrupt:
        display.module_exit()        
        logging.info("quit:")
        exit()

if __name__ == "__main__":
    main()