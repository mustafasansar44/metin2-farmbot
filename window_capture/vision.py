import cv2 as cv
import numpy as np


class Vision:


    """parametre olarak gönderilen [x, y, w, h] değerlerle click için [x,y] koordinatı sağlar.

    :param rectangles: [x, y, w, h]
    :returns: [center_x, center_y]
    """
    def get_click_points(self, rectangles):
            
        points = []

        # Loop over all the rectangles
        for (x, y, w, h) in rectangles:
            # Determine the center position
            center_x = x + int(w/2)
            center_y = y + int(h/2)
            # Save the points
            points.append((center_x, center_y))

        return points

    """parametre olarak gönderilen [x, y, w, h] değerlerle bize full_img'da eşleşen objeleri kare ile işaretleyip full_img'i tekrar dönderir.

    :param full_img: 
    :param rectangles: [x, y, w, h]
    :returns: full_img
    """
    def draw_rectangles(self, full_img, rectangles):
        line_color = (0, 255, 0) # BGR Şeklinde!
        line_type = cv.LINE_4

        for (x, y, w, h) in rectangles:
            # Kutunun pozisyonunu belirleme.
            top_left = (x, y)
            bottom_right = (x + w, y + h)

            # Kutuyu çizme işlemi
            cv.rectangle(full_img, top_left, bottom_right, line_color, lineType=line_type)

        return full_img

    """Gönderdiğimiz points noktalarına göre (x,y koordinatı) göre full_img'de koordinatı full_img'de çizer ve tekrar return eder.

    :param full_img: 
    :param points: [x, y]
    :returns: full_img
    """
    def draw_crosshairs(self, full_img, points):
        # these colors are actually BGR
        marker_color = (255, 0, 255)
        marker_type = cv.MARKER_CROSS

        for (center_x, center_y) in points:
            # draw the center point
            cv.drawMarker(full_img, (center_x, center_y), marker_color, marker_type)

        return full_img

    
    def centeroid(self, point_list):
        point_list = np.asarray(point_list, dtype=np.int32)
        length = point_list.shape[0]
        sum_x = np.sum(point_list[:, 0])
        sum_y = np.sum(point_list[:, 1])
        return [np.floor_divide(sum_x, length), np.floor_divide(sum_y, length)]