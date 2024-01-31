import cv2 as cv
import pyautogui
from time import sleep, time
from threading import Thread, Lock
from math import sqrt


class BotState:
    INITIALIZING = 0
    SEARCHING = 1
    MOVING = 2
    MINING = 3
    BACKTRACKING = 4


class Metin2Bot:
    # TODO: StartingPOS tanımlayabilirsin.
    
    # constants
    
    INITIALIZING_SECONDS = 6
    MINING_SECONDS = 40 # Taş kesme süresi - koşma dahil
    MOVEMENT_STOPPED_THRESHOLD = 0.6 # Bu değer ile hareketsizlik durumunu kontrol ediyoruz.
    IGNORE_RADIUS = 0 # Eğer bir target ana karakterimize çok yakınca ignore edecek. (Target ile aramızda 130 pixel ve altı varsa ignore kısaca)
    SMALL_IMG_MATCH_THRESHOLD = 0.1 # Eğer cv.minMaxLoc() taki max_val >= SMALL_IMG_MATCH_THRESHOLD ise eşleşme kabul edilir. Ne kadar yüksekse eşleşme o kadar zorlaşır ama bu değer ne kadar 1'e yakınsa o kadar kalitelidir aslında.


    # threading properties
    stopped = True
    lock = None

    # properties
    state = None
    targets = []
    screenshot = None
    timestamp = None
    movement_screenshot = None # Karşılaştırmak için bir önceki screenshot'u alır. 

    # Window Parametreleri
    window_offset = (0,0)
    window_width = 0 
    window_height = 0
    
    small_img_imread = None
    click_history = [] # Daha sonra dönmesi için bir history. 

    def __init__(self, window_offset, window_size, small_img_path):
        # ThreadLock objesi oluşturuyorum.
        self.lock = Lock()

        self.window_offset = window_offset # window sol üst koordinatı (x,y)
        self.window_width = window_size[0]
        self.window_height = window_size[1]


        self.small_img_imread = cv.imread(small_img_path, cv.IMREAD_UNCHANGED)

        # Botu initializing modunda başlatıyoruz. Daha sonra o kendisi duruma göre karar verecek.
        # mark the time at which this started so we know when to complete it
        self.state = BotState.INITIALIZING
        self.timestamp = time()
        
    """ Bulduğu targetlere göre sırayla click yapar.
    1- Targetleri mesafelerine göre sırala
    While:
        2- En yakın target'e mouse'u taşı ve sleep
        3- Bu target, istenilen target mi kontrol et (matchTemplate ile)
        4- Eğer değilse bir sonraki target'e geç
    5- Eğer bir target yoksa return False 
    6- Target'e tıkla ve True dönder.
    """
    def click_next_target(self):
        print("TARGET BULUNDU!")
        targets = self.targets_ordered_by_distance(self.targets) # Uzaklığa göre bulduğu target'leri sıralar.

        target_i = 0
        found_small_img = False
        while not found_small_img and target_i < len(targets):
            if self.stopped: # Durdurursak döngüden çık
                break

            target_pos = targets[target_i] # En yakın target'i seçer.
            screen_x, screen_y = self.get_screen_position(target_pos) # En takın target'in x,y değerlerini dönderir.
            print('Vurulacak Koordinat x:{} y:{}'.format(screen_x, screen_y))

            
            pyautogui.moveTo(x=screen_x, y=screen_y)    # Mouse'i ekranda götürtme kodu. Mouse'u target'in x,y noktasına taşıyacak.
            sleep(3) # Mouse taşındıktan sonra biraz bekletmek mantıklı. Burası olmasa anında diğerine kayar durduramayız.
            
            if self.matched_with_matchTemplate(target_pos): # small_img ile eşleşiyor mu
                print('Noktaya vuruluyor. x:{} y:{}'.format(screen_x, screen_y)) # eğer eşleşirse noktaya vuracak.
                found_small_img = True
                pyautogui.click()
                self.click_history.append(target_pos) # Önceki noktaya dönmek için
            target_i += 1

        return found_small_img

    def have_stopped_moving(self):
        if self.movement_screenshot is None:
            self.movement_screenshot = self.screenshot.copy()
            return False

        result = cv.matchTemplate(self.screenshot, self.movement_screenshot, cv.TM_CCOEFF_NORMED)

        similarity = result[0][0]
        print('Hareket Algılama Benzerliği: {}'.format(similarity))

        if similarity >= self.MOVEMENT_STOPPED_THRESHOLD:
            # Hareketsizlik durumu
            print('Hareketsizlik tespit edildi. Similarly: {}'.format(similarity) )
            pyautogui.keyDown("e")
            sleep(1)
            pyautogui.keyUp("e")
            return True

        # Hareket tespit edildiği için bir sonraki screenshot kopyalıyoruz.
        self.movement_screenshot = self.screenshot.copy()
        return False

    def targets_ordered_by_distance(self, targets):

        my_hero_pos = (self.window_width / 2, self.window_height / 2) # Karakterimiz her zaman ekranın ortasında olduğu için  

        def pythagorean_distance(pos):  # Noktaları, my_hero_pos noktasından uzaklığa göre sıralamak için pythagorean theorem kullandık. # https://stackoverflow.com/a/30636138/4655368
            return sqrt((pos[0] - my_hero_pos[0])**2 + (pos[1] - my_hero_pos[1])**2)
        targets.sort(key=pythagorean_distance) 

        targets = [t for t in targets if pythagorean_distance(t) > self.IGNORE_RADIUS]
        return targets

    # small_img ile screenshot'u eşleştirir. eşleşme değeri, self.SMALL_IMG_MATCH_THRESHOLD'den büyükse True, değilse False döner.
    def matched_with_matchTemplate(self, target_position):

        result = cv.matchTemplate(self.screenshot, self.small_img_imread, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result) # En iyi match pozisyonunu getirir.

        # if we can closely match the tooltip image, consider the object found
        if max_val >= self.SMALL_IMG_MATCH_THRESHOLD: # max_val en iyi eşleşmeyi belirtiyor. 
            # print('Tooltip found in image at {}'.format(max_loc))
            # screen_loc = self.get_screen_position(max_loc)
            # print('Found on screen at {}'.format(screen_loc))
            # mouse_position = pyautogui.position()
            # print('Mouse on screen at {}'.format(mouse_position))
            # offset = (mouse_position[0] - screen_loc[0], mouse_position[1] - screen_loc[1])
            # print('Offset calculated as x: {} y: {}'.format(offset[0], offset[1]))
            # the offset I always got was Offset calculated as x: -22 y: -29
            return True
        #print('Tooltip not found.')
        return False

    def click_backtrack(self):

        sleep(0.500)


    # translate a pixel position on a screenshot image to a pixel position on the screen.
    # pos = (x, y)
    # WARNING: if you move the window being captured after execution is started, this will
    # return incorrect coordinates, because the window position is only calculated in
    # the WindowCapture __init__ constructor.
    def get_screen_position(self, pos):
        return (pos[0] + self.window_offset[0], pos[1] + self.window_offset[1])

    # threading methods

    def update_targets(self, targets):
        self.lock.acquire()
        self.targets = targets
        self.lock.release()

    def update_screenshot(self, screenshot):
        self.lock.acquire()
        self.screenshot = screenshot
        self.lock.release()

    def start(self):
        self.stopped = False
        t = Thread(target=self.run)
        t.start()

    def stop(self):
        self.stopped = True

    # main logic controller
    def run(self):
        while not self.stopped:
            if self.state == BotState.INITIALIZING:
                # do no bot actions until the startup waiting period is complete
                if time() > self.timestamp + self.INITIALIZING_SECONDS:
                    # start searching when the waiting period is over
                    self.lock.acquire()
                    self.state = BotState.SEARCHING
                    self.lock.release()

            elif self.state == BotState.SEARCHING:
                # check the given click point targets, confirm a limestone deposit,
                # then click it.
                success = self.click_next_target()
                # if not successful, try one more time
                if not success:
                    success = self.click_next_target()

                # if successful, switch state to moving
                # if not, backtrack or hold the current position
                if success:
                    self.lock.acquire()
                    self.state = BotState.MOVING
                    self.lock.release()
                elif len(self.click_history) > 0:
                    self.click_backtrack()
                    self.lock.acquire()
                    self.state = BotState.BACKTRACKING
                    self.lock.release()
                else:
                    # stay in place and keep searching
                    pass

            elif self.state == BotState.MOVING or self.state == BotState.BACKTRACKING:
                # see if we've stopped moving yet by comparing the current pixel mesh
                # to the previously observed mesh
                if not self.have_stopped_moving():
                    # wait a short time to allow for the character position to change
                    sleep(0.500)
                else:
                    # reset the timestamp marker to the current time. switch state
                    # to mining if we clicked on a deposit, or search again if we
                    # backtracked
                    self.lock.acquire()
                    if self.state == BotState.MOVING:
                        self.timestamp = time()
                        self.state = BotState.MINING
                    elif self.state == BotState.BACKTRACKING:
                        self.state = BotState.SEARCHING
                    self.lock.release()
                
            elif self.state == BotState.MINING:
                # see if we're done mining. just wait some amount of time
                
                if time() > self.timestamp + self.MINING_SECONDS:
                    # TAŞI KIRDIKTAN SONRAKI ISLEMLER. TASTAN DUSEN ITEMLERI TOPLAR VE TEKRAR SEARCHING STATE DURUMUNA GEÇER.
                    # TAŞ KIRILDIKTAN SONRA DA 3 SANİYE BOYUNCA VURMAYA DEVAM EDER. COMPLARIN BLOKLAMASINI ENGELLEMEK İÇİN.
                    print("Taştan Düşenler Toplanıyor.")

                    pyautogui.keyDown("z")
                    pyautogui.keyUp("z")
                    
                    pyautogui.keyDown("space")
                    print("Olası komp kalma durumu için vuruluyor.")
                    # time.sleep(3) hata fırlatıyor. Buraya sonra bak
                    pyautogui.keyUp("space")
                    self.lock.acquire()
                    self.state = BotState.SEARCHING
                    self.lock.release()