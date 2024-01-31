import numpy as np
import win32gui, win32ui, win32con
from threading import Thread, Lock


class WindowCapture:

    # threading properties
    stopped = True
    lock = None
    screenshot = None
    # properties
    window_name = ""
    window_width = 0
    window_height = 0
    hwnd = None
    cropped_x = 0
    cropped_y = 0
    offset_x = 0
    offset_y = 0

    # constructor
    def __init__(self, window_name=None):
        # ThreadLock objesi üretiyoruz. (MultiThreading)
        self.lock = Lock()

        self.window_name = window_name
        self.get_window()
        self.get_window_size()
        self.set_window_size()
        self.set_crop_image()


    
    # Window'u OpenCV'nin anlayacağı bir formata dönüştürüyoruz. 
    def get_screenshot(self):

        # get the window image data
        wDC = win32gui.GetWindowDC(self.hwnd) # Window'un Device Context(DC)'ini alır.
        dcObj = win32ui.CreateDCFromHandle(wDC) # Bu Device Context(DC)'ten bir Device Context nesnesi oluşturur.
        cDC = dcObj.CreateCompatibleDC() # Uyumlu bir DC nesnesi oluşturur.
        dataBitMap = win32ui.CreateBitmap() # Bir bitmap nesnesi oluşturur.
        dataBitMap.CreateCompatibleBitmap(dcObj, self.window_width, self.window_height) # Uyumlu bir bitmap oluşturur ve boyutunu belirler.
        cDC.SelectObject(dataBitMap)
        # Window'un dimensionları ile oynayabilirsin. Bunlarla oynama mouse tıklamalarındaki hesaplar da buna bağlı.
        cDC.BitBlt((0, 0), (self.window_width, self.window_height), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY) #  Windowun belirli bir bölgesini kopyalar



        # Şimdi elimizdeki datayı OpenCV'nin anlayabileceği bir forma çeviriyoruz.
        #dataBitMap.SaveBitmapFile(cDC, 'debug.bmp') dataBitMap'i görmek istersen bu bize output verir debug.bmp şeklinde.
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        


        img.shape = (self.window_height, self.window_width, 4)

        # free resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # AlphaChannel'i droplama işlemi. Bunu yapmazsak matchTemplate ederken hata alırız. RGBA ---> RGB yaptık aslında. 4 channel yerine 3 channel
        img = img[...,:3]

        mapLogoLocation = slice(0, 100), slice(800, 1200) # Siyah olarak kestiğim bölge
        img[mapLogoLocation] = [0, 0, 0]

        # NumPy dizisini ram'e sıralı olarak yerleştirir. Bunu yapmasak bazen hatalar alabiliriz.
        img = np.ascontiguousarray(img)


        return img

    # açık olan window'ların isimlerini verir.
    @staticmethod
    def get_window_names():
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                print(hex(hwnd), win32gui.GetWindowText(hwnd))
        win32gui.EnumWindows(winEnumHandler, None)

        
    """Window'un anlık çekilen screenshot'undaki pixel noktasını, window'daki pixel noktasına çevirir. 
    Galiba sahte window'daki pixel noktasını, orijinal windowdaki noktaya çevirir.
    
    Not: Eğer ekran görüntüsü alındıktan sonra yakalanan pencere hareket ederse, 
    bu metodun sonuçları doğru olmayabilir. Çünkü pencerenin konumu sadece __init__ kurucu fonksiyonunda 
    hesaplanır ve eğer pencere hareket ederse, bu hesaplanan konum güncellenmez. Bu durumda, pencerenin 
    konumu güncellendikten sonra tekrar bu metot çağrılmalıdır.
    """
    def get_screen_position(self, pos):
        return (pos[0] + self.offset_x, pos[1] + self.offset_y)

    # Windowu yakalamak için. Eğer aradığı windowu bulamazsa direkt ekran görüntüsünü alacak.
    def get_window(self):
        if self.window_name is None:
            self.hwnd = win32gui.GetDesktopWindow()
        else:
            self.hwnd = win32gui.FindWindow(None, self.window_name)
            if not self.hwnd:
                raise Exception('Window bulunamadı: {}'.format(self.window_name))

    # Window'un dimension'larını hesaplamak için.
    def get_window_size(self):
        window_dimensions = self.get_window_dimensions()
        self.window_width = window_dimensions[2] - window_dimensions[0]
        self.window_height = window_dimensions[3] - window_dimensions[1]


    # Window'daki kırpılacak koordinatları hesaplar.
    def set_window_size(self):
        border_pixels = 8
        titlebar_pixels = 30
        self.window_width = self.window_width - (border_pixels * 2)
        self.window_height = self.window_height - titlebar_pixels - border_pixels
        self.cropped_x = border_pixels
        self.cropped_y = titlebar_pixels

    # Window'daki kırpılacak koordinat değerlerini window'dan çıkarır.
    def set_crop_image(self):
        window_dimensions = self.get_window_dimensions()
        # Kırpılmış offset koordinatlar.
        # Bu offset'ler bizim gerçek pencerenin sol üst noktasının koordinatlarını veriyor.
        self.offset_x = window_dimensions[0] + self.cropped_x # Sol üst x koordinatı
        self.offset_y = window_dimensions[1] + self.cropped_y # Sol üst y koordinatı


    # Window dimension'u verir. (offset.x, offset.y, width, height) şeklinde
    def get_window_dimensions(self):
        return win32gui.GetWindowRect(self.hwnd)
    

    # threading methods
    def start(self):
        self.stopped = False
        t = Thread(target=self.run)
        t.start()

    def stop(self):
        self.stopped = True

    def run(self):
        # TODO: you can write your own time/iterations calculation to determine how fast this is
        while not self.stopped:
            # get an updated image of the game
            screenshot = self.get_screenshot()
            # lock the thread while updating the results
            self.lock.acquire()
            self.screenshot = screenshot
            self.lock.release()