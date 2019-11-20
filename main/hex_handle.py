# encoding: utf-8
import math
import re

def get_hex_data(path):
    with open(path, 'rb') as f:
        hexdata = hexdata = f.read().hex()
        return hexdata

def hex2rgb(tmp):
    tmp = tmp.replace('#','')
    opt = re.findall(r'(.{2})',tmp)
    arr = []
    for i in range (0, len(opt)):
        arr.append(int(opt[i], 16))
    return arr

def colour_distance(hex_1, hex_2):
     rgb_1 = hex2rgb(hex_1)
     rgb_2 = hex2rgb(hex_2)
     R_1,G_1,B_1 = rgb_1
     R_2,G_2,B_2 = rgb_2
     rmean = (R_1 +R_2 ) / 2
     R = R_1 - R_2
     G = G_1 -G_2
     B = B_1 - B_2
     rx = 1 - int(math.sqrt((2+rmean/256)*(R**2)+4*(G**2)+(2+(255-rmean)/256)*(B**2)))/764
     return rx

def get_start_t(hexbase,x,y):
    return hexbase + ((x+1+y*960)-1)*4*2

def get_end_t(hexbase,x,y):
    return hexbase + (x+1+y*960)*4*2

def get_hex_str(hex_data,hexbase,x,y):
    start_t = get_start_t(hexbase,x,y)
    end_t = get_end_t(hexbase,x,y)
    target_hex = hex_data[start_t:end_t-2]
    return '#%s'%(target_hex)

def hex_compare(hex_data, item,target):
    x = item['dot'][0]
    y = item['dot'][1]
    if(x < 0):
        x = 0
    if(x > 959):
        x = 959
    if(y < 0):
        y = 0
    if(y > 539):
        y = 539
    hexbase = 12*2
    hex_str = get_hex_str(hex_data,hexbase,x,y)
    cp = colour_distance(item['color'],hex_str)
    if(cp >= item['confidence']):
        return True
    else:
        return False

def compare_only(hex_data,x,y,color,sim):
    hexbase = 12*2
    hex_str = get_hex_str(hex_data,hexbase,x,y)
    cp = colour_distance(color,hex_str)
    if(cp >= sim):
        return True
    else:
        return False

def color_compare(path, arr,target):
    if(arr and len(arr) > 0):
        hex_data = get_hex_data(path)
        all_same = True
        for i in arr:
            same_cam = hex_compare(hex_data, i,target)
            if(not same_cam):
                all_same = False
        return all_same
    else:
        return False

def compare_offset(hex_data,area,aim_color,confidence,offset_dot):
    for x_p in range(area[0],area[2]):
        for y_p in range(area[1],area[3]):
            result = compare_only(hex_data,x_p,y_p,aim_color,confidence)
            if result:
                all_same_judge = True
                for item in offset_dot:
                    ofset_result = compare_only(hex_data,x_p+item["offset"][0],y_p+item["offset"][1],item["color"],confidence)
                    if not ofset_result:
                        all_same_judge = False
                        break
                if all_same_judge:
                    return [x_p,y_p]
    return None

def offset_compare(path,area,aim_color,confidence,offset_dot):
    if(offset_dot and len(offset_dot) > 0):
        hex_data = get_hex_data(path)
        if int(area[0]) > int(area[2]):
            trans_val = area[0]
            area[0] = area[2]
            area[2] = trans_val
        if int(area[1]) > int(area[3]):
            trans_val = area[1]
            area[1] = area[3]
            area[3] = trans_val
        return compare_offset(hex_data,area,aim_color,confidence,offset_dot)
    else:
        return None