import sys
import cv2
from PIL import Image

from ayat.find_ayat_v2 import find_ayat
from lines.lines import find_lines

hafs_ayat = [7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111,
             43, 52, 99, 128, 111, 110, 98, 135, 112, 78, 118, 64, 77,
             227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75,
             85, 54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55,
             78, 96, 29, 22, 24, 13, 14, 11, 11, 18, 12, 12, 30, 52, 52,
             44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29, 19, 36, 25,
             22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
             11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6]
warsh_ayat = [7, 285, 200, 175, 122, 167, 206, 76, 130, 109, 121, 111,
              44, 54, 99, 128, 110, 105, 99, 134, 111, 76, 119, 62, 77,
              226, 95, 88, 69, 59, 33, 30, 73, 54, 46, 82, 182, 86, 72,
              84, 53, 50, 89, 56, 36, 34, 39, 29, 18, 45, 60, 47, 61, 55,
              77, 99, 28, 21, 24, 13, 14, 11, 11, 18, 12, 12, 31, 52, 52,
              44, 30, 28, 18, 55, 39, 31, 50, 40, 45, 42, 29, 19, 36, 25,
              22, 17, 19, 26, 32, 20, 15, 21, 11, 8, 8, 20, 5, 8, 9, 11,
              10, 8, 3, 9, 5, 5, 6, 3, 6, 3, 5, 4, 5, 6]

sura = 1
ayah = 1
# number of lines to skip when the end of the sura is reached
# for example, one for the basmallah and one for the header.
# 1 is automatically deducted from this number for sura Tawbah.
default_lines_to_skip = 2
sura_ayat = hafs_ayat

# by default, we don't increase the ayah on the top of this loop
# to handle ayat that span multiple pages - this flag allows us to
# override this.
end_of_ayah = False


def process_ayat(ayat):
    result = []
    cur_y = ayat[0][1]
    same_line = []
    for ayah in ayat:
        if abs(ayah[1] - cur_y) < 20:
            same_line.append(ayah)
        else:
            same_line.sort(key=lambda tup: tup[0])
            for s in same_line[::-1]:
                result.append(s)
            cur_y = ayah[1]
            same_line = [ayah]

    same_line.sort(key=lambda tup: tup[0])
    for s in same_line[::-1]:
        result.append(s)
    return result


def main():
    global end_of_ayah, sura, ayah, sura_ayat, default_lines_to_skip

    lines_to_skip = 0
    for i in range(1, 605):
        image_dir = sys.argv[1] + '/'
        filename = 'page' + str(i).zfill(3) + '.jpg'
        print(filename)

        # find lines
        image = Image.open(image_dir + filename).convert('RGBA')

        lines = find_lines(image, 114, 25, 1)
        print('found: %d lines on page %d' % (len(lines), i))

        img_rgb = cv2.imread(image_dir + filename)
        (ayat, _) = find_ayat(img_rgb)
        ayat = sorted(ayat, key=lambda x: (x[1], x[0]))
        ayat = process_ayat(ayat)
        print('found: %d ayat on page %d' % (len(ayat), i))

        line = 0
        current_line = 0
        x_pos_in_line = -1
        num_lines = len(lines)

        first = True
        end_of_sura = False
        for ayah_item in ayat:
            if (end_of_ayah or not first) and sura_ayat[sura - 1] == ayah:
                sura = sura + 1
                ayah = 1
                lines_to_skip = default_lines_to_skip
                if sura == 9:
                    lines_to_skip = lines_to_skip - 1
                end_of_ayah = False
            elif end_of_ayah or not first:
                ayah = ayah + 1
                end_of_ayah = False
            first = False
            y_pos = ayah_item[1]

            pos = 0
            for line in range(current_line, num_lines):
                if lines_to_skip > 0:
                    lines_to_skip = lines_to_skip - 1
                    current_line = current_line + 1
                    continue
                pos = pos + 1
                cur_line = lines[line]
                miny = cur_line[0][1]
                maxy = cur_line[1][1]
                if y_pos <= maxy:
                    # we found the line with the ayah
                    maxx = cur_line[1][0]
                    if x_pos_in_line > 0:
                        maxx = x_pos_in_line
                    minx = ayah_item[0]
                    vals = (i, line + 1, sura, ayah, pos, minx, maxx, miny, maxy)
                    s = 'insert into glyphs values(NULL, '
                    print(s + '%d, %d, %d, %d, %d, %d, %d, %d, %d);' % vals)

                    end_of_sura = False
                    if sura_ayat[sura - 1] == ayah:
                        end_of_sura = True

                    if end_of_sura or abs(minx - cur_line[0][0]) < ayah_item[2]:
                        x_pos_in_line = -1
                        current_line = current_line + 1
                        if current_line == num_lines:
                            # last line, and no more ayahs - set it to increase
                            end_of_ayah = True
                    else:
                        x_pos_in_line = minx
                    break
                else:
                    # we add this line
                    maxx = cur_line[1][0]
                    if x_pos_in_line > 0:
                        maxx = x_pos_in_line
                    x_pos_in_line = -1
                    current_line = current_line + 1
                    vals = (i, line + 1, sura, ayah, pos, cur_line[0][0], maxx,
                            cur_line[0][1], cur_line[1][1])
                    s = 'insert into glyphs values(NULL, '
                    print(s + '%d, %d, %d, %d, %d, %d, %d, %d, %d);' % vals)

        # handle cases when the sura ends on a page, and there are no more
        # ayat. this could mean that we need to adjust lines_to_skip (as is
        # the case when the next sura header is at the bottom) or also add
        # some ayat that aren't being displayed at the moment.
        if end_of_sura:
            # end of sura always means x_pos_in_line is -1
            sura = sura + 1
            ayah = 1
            lines_to_skip = default_lines_to_skip
            if sura == 9:
                lines_to_skip = lines_to_skip - 1
            end_of_ayah = False
            while line + 1 < num_lines and lines_to_skip > 0:
                line = line + 1
                lines_to_skip = lines_to_skip - 1
            if lines_to_skip == 0 and line + 1 != num_lines:
                ayah = 0

        # we have some lines unaccounted for or stopped mid-line
        if x_pos_in_line != -1 or line + 1 != num_lines:
            if x_pos_in_line == -1:
                line = line + 1
            pos = 0
            ayah = ayah + 1
            for l in range(line, num_lines):
                cur_line = lines[l]
                pos = pos + 1
                maxx = cur_line[1][0]
                if x_pos_in_line > 0:
                    maxx = x_pos_in_line
                    x_pos_in_line = -1
                vals = (i, l + 1, sura, ayah, pos, cur_line[0][0], maxx,
                        cur_line[0][1], cur_line[1][1])
                s = 'insert into glyphs values(NULL, '
                print(s + '%d, %d, %d, %d, %d, %d, %d, %d, %d);' % vals)


if __name__ == "__main__":
    main()
