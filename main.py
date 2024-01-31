
import cv2 as cv
import numpy as np # bilimsel hesaplamalar için kullanılan güçlü bir Python kütüphanesidir
from matplotlib import pyplot as plt
from time import sleep, time
from window_capture.windowcapture import WindowCapture
from window_capture.vision import Vision
from threading import Thread
from window_capture.detection import Detection
from window_capture.bot import Metin2Bot, BotState
import pyautogui    



#WindowCapture().get_window_names()
# hsv_filter = HsvFilter(0,0,0,130,255,255,0,255,120,50)


DEBUG = True

# initialize the WindowCapture class
wincap = WindowCapture('METIN2')
# load the detector
detector = Detection('cascade/cascade.xml')
# load an empty Vision class
vision = Vision()
# initialize the bot

bot = Metin2Bot((wincap.offset_x, wincap.offset_y), (wincap.window_width, wincap.window_height), 'metin2_tooltip.jpg')

wincap.start()
detector.start()
bot.start()

while(True):
    if wincap.screenshot is None:
        continue

    # Burası, bizim screenshot'taki target'leri bulmaya çalışıyor cascade.xml'deki verilere göre.
    detector.update(wincap.screenshot)
    
    if bot.state == BotState.INITIALIZING:
        targets = vision.get_click_points(detector.rectangles)
        bot.update_targets(targets)
    elif bot.state == BotState.SEARCHING:
        # when searching for something to click on next, the bot needs to know what the click
        # points are for the current detection results. it also needs an updated screenshot
        # to verify the hover tooltip once it has moved the mouse to that position
        targets = vision.get_click_points(detector.rectangles)
        bot.update_targets(targets)
        bot.update_screenshot(wincap.screenshot)
    elif bot.state == BotState.MOVING:
        # when moving, we need fresh screenshots to determine when we've stopped moving
        bot.update_screenshot(wincap.screenshot)
    elif bot.state == BotState.MINING:
        # Burada bir şey yapmaya gerek yok. Taşı kesmesini beklemek için
        pass
    
    
    if DEBUG:
        detection_image = vision.draw_rectangles(wincap.screenshot, detector.rectangles)
        cv.imshow('DEBUG_WINDOW', detection_image)
    else:
        cv.imshow('NORMAL_WINDOW', wincap.screenshot)
    # press 'q' with the output window focused to exit.
    # waits 1 ms every loop to process key presses
    key = cv.waitKey(1)
    currentTime = time()
    if key == ord('q'):
        wincap.stop()
        detector.stop()
        bot.stop()
        cv.destroyAllWindows()
        break
    elif key == ord("p"):
        cv.imwrite("image/positive/{}.jpg".format(currentTime), wincap.screenshot)
    elif key == ord("n"):
        cv.imwrite("image/negative/{}.jpg".format(currentTime), wincap.screenshot)

print('Done.')










# DEBUG MOD BURASI GIBI DUSUN ISIN BITINCE COMMENT LINE YAP
# cv.imshow("Result", result) # ilk parametre windowname, ikinci de verinin resmi 
# cv.waitKey()    # eğer bunu koymazsak aniden kapanır hiçbir şey göremeyiz. Bu bekletmeye yari



"""








minVal,maxVal, minLoc, maxLoc = cv.minMaxLoc(result);
tas_img_height = tas_img.shape[0]
tas_img_width = tas_img.shape[1]

topLeft = maxLoc;
bottomRight = (topLeft[0] + tas_img_width, topLeft[1] + tas_img_width);

cv.rectangle(tasFull_img, topLeft, bottomRight, color=(0, 255, 0), thickness=2, lineType=cv.LINE_4)
cv.imwrite("result.jpg", tasFull_img)
cv.imshow("Result", result)
cv.waitKey()



















minVal,maxVal, minLoc, maxLoc = cv.minMaxLoc(result); # minVal dediği en siyah nokta iken max dediği en beyaz nokta. minLoc = minimum olan noktanın lokasyonu

print("en beyaz nokta: " + str(maxVal) + " ve koordinatı: " + str(maxLoc))
print("en siyah nokta: " + str(minVal) + " ve koordinatı: " + str(minLoc))

threshold = 0.8 # Eşik, Limit
if maxVal >= threshold:
    print("Bulduk Ğardaş!")
    tas_img_height = tas_img.shape[0]
    tas_img_width = tas_img.shape[1]

    topLeft = maxLoc;
    bottomRight = (topLeft[0] + tas_img_width, topLeft[1] + tas_img_width);

    
    cv.rectangle(tasFull_img, topLeft, bottomRight, color=(0, 255, 0), thickness=2, lineType=cv.LINE_4)
    cv.imwrite("result.jpg", tasFull_img)
    cv.imshow("Result", tasFull_img)
    cv.waitKey()

else: 
    print("Gaptan Gaybolduğ la Ğardaş!")

"""