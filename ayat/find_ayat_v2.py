import cv2
import sys

# new madani
WIDTH_MIN = 50
WIDTH_MAX = 62
HEIGHT_MIN = 70
HEIGHT_MAX = 80


def find_ayat(img_rgb):
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(img_gray, 230, 255,  cv2.THRESH_BINARY_INV)[1]
    contours = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]

    results = []
    selected_contours = []
    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(contour)
        if WIDTH_MIN < w < WIDTH_MAX and HEIGHT_MIN < h < HEIGHT_MAX:
            is_marker = False
            for row in range(y + int(h/4), y + int(3*h/4)):
                if is_marker:
                    break
                for col in range(x + int(w/4), x + int(3*w/4)):
                    if row >= img_rgb.shape[0] or col >= img_rgb.shape[1]:
                        continue
                    (b, g, r) = img_rgb[row, col]
                    if b > 185 and b < 195 and g > 225 and g < 240 and r > 185 and r < 195:
                        is_marker = True
                        break
            if is_marker:
                results.append((x, y, w, h))
                selected_contours.append(contour)
    # cv2.imshow("image", img_rgb)
    # cv2.waitKey(0)
    return [results, selected_contours]


def draw(img_rgb, contours, output):
    for contour in contours:
        cv2.drawContours(img_rgb, [contour], -1, (0, 0, 255), 9)
    cv2.imwrite(output, img_rgb)


def main():
    if len(sys.argv) < 2:
        print("usage: " + sys.argv[0] + " image")
        sys.exit(1)

    filename = sys.argv[1]
    # filename = "new_madani/page003.png"
    img_rgb = cv2.imread(filename)
    (ayat, contours) = find_ayat(img_rgb)
    draw(img_rgb, contours, 'res.png')
    for ayah in ayat:
        (x, y, w, h) = ayah
        print("marker found at: (%d, %d) - %dx%d" % (x, y, w, h))


if __name__ == "__main__":
    main()
