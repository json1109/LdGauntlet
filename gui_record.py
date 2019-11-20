# encoding: utf-8
import tkinter
from tkinter import ttk
from inspect import signature
import re
from pynput import mouse, keyboard
from threading import Thread
from PIL import ImageGrab,Image
from pathlib import Path
import time
import sys
import os
import win32gui
import random
import shutil
import pyautogui
import json
import traceback

# rec实例
rec_instance = None

dn_ld = None
dn_console = None
dn_share_path = None

# state状态
dot_record_state = False
command_record_state = False

win_name = input("input script name:") or "demo"
emulator_index = input("input record emulator index:") or "0"
module_index = input("input now module:") or "0"

# 点阵外部容器
grid_list_wrapper = None
grid_state = 0
# 点阵实体
dot_list = [
]
# 命令实体
command_list = {
    "name":'',
    "param":'',
    "data":[]
}

# 命令外部容器
text_area = None
# 实际命令文本域
script_text = None
# 模块索引
sp_module_index = None

FILE_FOLDER_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\'

def _entry_val_c(index,v):
    global dot_list
    if grid_state == 0:
        time.sleep(0.1)
        ls_arr = v.get().split(",")
        if len(ls_arr) == 4 and ls_arr[0] and ls_arr[1] and ls_arr[2] and ls_arr[3]:
            rox_confidence = round(float(ls_arr[3]),2)
            if rox_confidence == 1:
                rox_confidence = int(rox_confidence)
            dot_list[index] = [int(ls_arr[0]),int(ls_arr[1]),str(ls_arr[2]),rox_confidence]
    else:
        lc_arr = v.get().split(",")
        if index == 0 or index == 1:
            if len(lc_arr) == 2 and lc_arr[0] and lc_arr[1]:
                dot_list[index][0] = int(lc_arr[0])
                dot_list[index][1] = int(lc_arr[1])
        elif index == 2:
            rox_confidence = round(float(lc_arr[1]),2)
            if rox_confidence == 1:
                rox_confidence = int(rox_confidence)
            if len(lc_arr) == 2 and lc_arr[0] and lc_arr[1]:
                dot_list[index][2] = lc_arr[0]
                dot_list[index][3] = rox_confidence
        else:
            rox_confidence = round(float(lc_arr[3]),2)
            if rox_confidence == 1:
                rox_confidence = int(rox_confidence)
            if len(lc_arr) == 4 and lc_arr[0] and lc_arr[1] and lc_arr[2] and lc_arr[3]:
                dot_list[index] = [int(lc_arr[0]),int(lc_arr[1]),str(lc_arr[2]),rox_confidence]

def entry_val_change(index,v):
    # 键入时获取数据同步到dot_list
    p = Thread(target=_entry_val_c, args=(index,v))
    p.start()

def clean_t(item):
    if "\t" in item:
        return item.replace("\t","        ")
    return item

def _text_val_c():
    global script_text,command_list,cmb,text_area
    select_index = int(cmb.get().split(":")[0])
    if text_area and script_text:
        if select_index == 3 or select_index == 4:
            time.sleep(0.1)
            val = script_text.get('0.0','end')
            sx_arr = val.strip().split('\n')
            start_inx = 0
            for inx,item in enumerate(sx_arr):
                if 'def' in item:
                    start_inx = inx
            if start_inx:
                new_arr = sx_arr[start_inx+1:]
                command_list["data"] = list(map(clean_t,new_arr))
        elif select_index == 2:
            time.sleep(0.1)
            val = script_text.get('0.0','end')
            sx_arr = val.strip().split('\n')
            command_list["data"] = list(map(clean_t,sx_arr))

def text_val_change(e):
    p = Thread(target=_text_val_c)
    p.start()

# 实体类
class DnPlayer(object):
    def __init__(self, info: list):
        super(DnPlayer, self).__init__()
        self.index = int(info[0])
        self.name = info[1]
        self.top_win_handler = int(info[2])
        self.bind_win_handler = int(info[3])
        self.is_in_android = True if int(info[4]) == 1 else False
        self.pid = int(info[5])
        self.vbox_pid = int(info[6])

    def is_running(self) -> bool:
        return self.is_in_android

    def __str__(self):
        index = self.index
        name = self.name
        r = str(self.is_in_android)
        twh = self.top_win_handler
        bwh = self.bind_win_handler
        pid = self.pid
        vpid = self.vbox_pid
        return "\nindex:%d name:%s top:%08X bind:%08X running:%s pid:%d vbox_pid:%d\n" % (
            index, name, twh, bwh, r, pid, vpid)

    def __repr__(self):
        index = self.index
        name = self.name
        r = str(self.is_in_android)
        twh = self.top_win_handler
        bwh = self.bind_win_handler
        pid = self.pid
        vpid = self.vbox_pid
        return "\nindex:%d name:%s top:%08X bind:%08X running:%s pid:%d vbox_pid:%d\n" % (
            index, name, twh, bwh, r, pid, vpid)

def get_list():
    cmd = os.popen(dn_console + 'list2')
    text = cmd.read()
    cmd.close()
    info = text.split('\n')
    result = list()
    for line in info:
        if len(line) > 1:
            dnplayer = line.split(',')
            result.append((DnPlayer(dnplayer)))
    return result

def list_running():
    result = list()
    all_init = get_list()
    for dn in all_init:
        if dn.is_running() is True:
            result.append((dn.index,dn.bind_win_handler))
    return result

class RecordScript(object):
    simulator_x = 960
    simulator_y = 540

    def __init__(self):
        # 偏移的xy(正确)
        self.offset_x = 0
        self.offset_y = 0
        # 录制文件路径 和 录制资源文件夹
        self.script_path = None
        self.res_path = None

        self.fn_record_flag = False
        self.json_flag = False
        self.json_dump_enable = False
        # 左键点击缓存时间变量    
        self._press_time_cache = 0
        self._press_cache = None
        self.res_order = None
        self.input_emulator = 0
        # 当前的录制模块
        self.script_module = 0
        # 截屏路径
        self.emu_png_path = dn_share_path + '\\record.png'

        self.get_start_offset()

    def v_create_dir(self,dirs):
        if not os.path.exists(dirs):
            os.makedirs(dirs)

    def dnld(self,index: int, command: str, silence: bool = True):
        cmd = dn_ld + '-s %d %s' % (index, command)
        if silence:
            os.system(cmd)
            return ''
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    # 点击起始x
    def click_x(self,num):
        return num - self.offset_x

    # 点击起始y
    def click_y(self,num):
        return num - self.offset_y

    def v_find_by_pic(self,image,grayscale=False):
        try:
            x,y,w,h = pyautogui.locateOnScreen(image,grayscale=grayscale,confidence=0.99)
            return True,(x,y)
        except Exception as e:
            print(e)
            return False,None

    def v_screen_get(self):
        x1 = self.offset_x
        y1 = self.offset_y
        x2 = x1 + self.simulator_x
        y2 = y1 + self.simulator_y
        bbox = (x1, y1, x2, y2)
        im = ImageGrab.grab(bbox)
        return im

    def get_start_offset(self):
        result = None
        for device in list_running():
            left, top, right, bottom = win32gui.GetWindowRect(device[1])
            if(left < 0 or top < 0):
                win.quit()
                raise ValueError('plz set emulator top !')
            result = (left,top)
        if(result):
            x,y = result
            print('emulator x and y: %s %s'%(result[0],result[1]))
            self.offset_x = result[0]
            self.offset_y = result[1]
        else:
            win.quit()
            raise ValueError('emulator not exist')

    def run(self):
        global win_name,module_index,emulator_index
        self.input_names = win_name
        self.input_emulator = int(emulator_index)
        self.script_module = int(module_index)

        if(self.offset_x == 0 and self.offset_y == 0):
            print('Warning : offset_x and offset_y is 0 !')
        else:
            print('offset_x:%s offset_y:%s'%(self.offset_x,self.offset_y))
            
        self._init_script()
        self._init_listener()

    def refresh_base_res_path(self):
        self.res_path = FILE_FOLDER_PATH + 'main\\' + 'script\\' + self.input_names +'\\'+ str(self.script_module)
        self.v_create_dir(self.res_path)

    def _init_script(self):
        self.refresh_base_res_path()
        self.script_path = FILE_FOLDER_PATH + 'main\\' + 'script\\' + self.input_names + '.py'
        if not os.path.exists(self.script_path):
            with open(self.script_path, 'a',encoding='utf-8') as file_obj:
                self._add_import()
    
    def _add_import(self):
        arr_str = [
            'class ScriptFunction(object):',
            '    def __init__(self, *args, **kwargs):',
            '        return super().__init__(*args, **kwargs)',
            ''
        ]
        self._append_script(arr_str)

    def append_command_to_py(self,command_obj):
        if command_obj["name"]:
            insert_lines = ""
            insert_lines += '\n'
            insert_lines += '    @staticmethod\n'
            insert_lines += '    def %s(%s):\n'%(command_obj["name"],command_obj["param"])
            for i in command_obj["data"]:
                insert_lines += i + '\n'
            with open(self.script_path, 'a',encoding='utf-8') as file_obj:
                file_obj.write(insert_lines)

    def _append_script(self,text,init_flag=False):
        if(not isinstance(text,str)):
            text = '\n'.join(text)
        else:
            text = text+'\n'
        with open(self.script_path, 'a',encoding='utf-8') as file_obj:
            file_obj.write(text)

    def get_file_order_name(self):
        for i in range(1000):
            if not os.path.exists(self.res_path +'\\'+ (str(i)+'.json')):
                return str(i)

    def write_into_json(self,json_str):
        json_path = self.res_path +'\\'+ (self.res_order + '.json')
        with open(json_path, 'w',encoding='utf-8') as json_file:
            try:
                json_file.write(json_str)
            except Exception as e:
                traceback.print_exc()
                print(e)

    def get_hex_data(self,path):
        with open(path, 'rb') as f:
            hexdata = hexdata = f.read().hex()
            return hexdata

    def get_start_t(self,hexbase,x,y):
        return hexbase + ((x+1+y*960)-1)*4*2

    def get_end_t(self,hexbase,x,y):
        return hexbase + (x+1+y*960)*4*2
    
    def get_hex_str(self,hex_data,hexbase,x,y):
        start_t = self.get_start_t(hexbase,x,y)
        end_t = self.get_end_t(hexbase,x,y)
        target_hex = hex_data[start_t:end_t-2]
        return '#%s'%(target_hex)

    def json_load(self,path):
        with open(path,encoding='utf-8') as json_file:
            data = json.load(json_file)
            return data

    def v_get_color(self,x,y,path=None,file_data=None):
        if self.json_dump_enable:
            self.dnld(self.input_emulator, 'screencap /sdcard/Pictures/record.dump')
            time.sleep(0.5)
            self.json_dump_enable = False
        dmp_path = dn_share_path + '\\record.dump'
        if not os.path.exists(dmp_path):
            raise Exception('emulator config of share path has error , now is%s'%(dmp_path))
        hex_data = self.get_hex_data(dn_share_path +'\\record.dump')
        return self.get_hex_str(hex_data,24,x,y)


    def v_rgb2hex(self,valid_values):
        r, g, b = valid_values[0], valid_values[1], valid_values[2]
        return '#{:02x}{:02x}{:02x}'.format(r, g, b).upper()

    def snap_screen_by_start(self):
        self.res_order = self.get_file_order_name()
        png_path = self.res_path +'\\'+ (self.res_order + '.png')
        if not os.path.exists(png_path):
            self.dnld(self.input_emulator, 'screencap /sdcard/Pictures/record.png')
            if(os.path.exists(self.emu_png_path)):
                self.moveFileto(self.emu_png_path,png_path)

    # 资源录制
    def _snap_record(self,x,y):
        global dot_list
        dot_list.append([x,y,self.v_get_color(x, y),1])
        render_grid()

    def get_now_time(self):
        t = time.time()
        return int(round(t * 1000))

    def _new_press_down(self,x,y):
        self.clean_press_cache()
        self._press_cache = [x,y]

    def clean_press_cache(self):
        global command_list
        now_time = self.get_now_time()
        command_list['data'].append('        context.sleep(%s)'%(now_time-self._press_time_cache))
        render_command()
        self._press_time_cache = now_time

    def fn_name_get(self):
        return 'rec'+self.v_ran_str(7)

    def v_ran_str(self,num):
        H = 'abcdefghijklmnopqrstuvwxyz0123456789'
        salt = ''
        for i in range(num):
            salt += random.choice(H)
        return salt
    
    def f2_handle_start(self):
        global dot_record_state,dot_list
        self.f3_handle_stop()
        self.json_flag = True
        if len(dot_list) == 0:
            self.json_dump_enable = True
            self.snap_screen_by_start()
        dot_record_state = True
        show_tips_label()
    
    def f2_handle_stop(self):
        global dot_record_state
        self.json_flag = False
        dot_record_state = False
        show_tips_label()

    def f4_handle(self):
        global sp_module_index
        if dot_record_state:
            show_result("please stop dot record")
            return
        self.script_module = self.script_module + 1
        self.refresh_base_res_path()
        sp_module_index.set(self.script_module)

    def f3_handle_start(self,params_num):
        global command_list,command_record_state
        self.f2_handle_stop()
        self.fn_record_flag = True
        if len(command_list["data"]) == 0:
            if params_num == 1:
                command_list = {
                    "name":self.fn_name_get(),
                    "param":'context',
                    "data":[]
                }
            else:
                command_list = {
                    "name":self.fn_name_get(),
                    "param":'context,point',
                    "data":[]
                }
        self._press_time_cache = self.get_now_time()
        render_command()
        command_record_state = True
        show_tips_label()

    def f3_handle_stop(self):
        global command_record_state
        self.fn_record_flag = False
        command_record_state = False
        show_tips_label()

    def _new_press_up(self,x,y):
        global command_list
        now_time = self.get_now_time()
        time_between = now_time - self._press_time_cache
        if(x == self._press_cache[0] and y == self._press_cache[1]):
            command_list['data'].append('        context.click(%s,%s,%s,40)'%(x,y,time_between))
        else:
            command_list['data'].append('        context.swipe(%s,%s,%s,%s,%s,40)'%(self._press_cache[0],self._press_cache[1],x,y,time_between))
        render_command()

    def _init_listener(self):
        #监听鼠标
        def on_click(x,y,button,pressed):
            try:
                x = int(self.click_x(x))
                y = int(self.click_y(y))
                if(button == mouse.Button.right):
                    if self.json_flag:
                        if(pressed):
                            self._snap_record(x,y)
                    if self.fn_record_flag:
                        if(pressed):
                            self._new_press_down(x,y)
                        else:
                            self._new_press_up(x,y)
            except Exception as e:
                traceback.print_exc()
                print(e)


        mouse_listener = mouse.Listener(on_click=on_click)
        mouse_listener.start()

        def on_release(key):
            try:
                if(key == keyboard.Key.esc):
                    mouse_listener.stop()
                    keyboard_listener.stop()
                    win.quit()
                    return False

            except Exception as e:
                traceback.print_exc()
                print(e)

        keyboard_listener = keyboard.Listener(on_release=on_release)
        keyboard_listener.start()

        mouse_listener.join()
        keyboard_listener.join()

    def coverFiles(self,sourceDir, targetDir): 
        for file_item in os.listdir(sourceDir): 
            sourceFile = os.path.join(sourceDir,  file_item) 
            targetFile = os.path.join(targetDir,  file_item) 
            #cover the files 
            if os.path.isfile(sourceFile): 
                self.moveFileto(sourceFile,targetFile)
    
    def moveFileto(self,sourceDir,  targetDir): 
        shutil.copy(sourceDir,  targetDir)

win = tkinter.Tk()
win.title(win_name)
win.geometry("380x700+1200+50")

# 选框模块
cmb_val = 0
cmb = ttk.Combobox(win,state='readonly')
cmb.grid(row=4,column=0,padx=10,pady=5,sticky=tkinter.W)
cmb['value'] = ('1: Click First Dot','2: Run By command','3: Run By function','4: Area find muti-color')
cmb.current(0)
tkinter.Label(win,text = "now module:").grid(row=1,column=0,padx=10,pady=5,sticky=tkinter.W)
sp_module_index = tkinter.Variable()
sp_module_index.set(module_index)
tkinter.Entry(win,textvariable = sp_module_index,state='readonly').grid(row=1,column=0,pady=5,padx=100,sticky=tkinter.W)
btn_group = tkinter.Frame(win)
tkinter.Button(btn_group,text="START",width=10,command=lambda:rec_instance.f2_handle_start())\
    .grid(row=0, column=0,sticky=tkinter.W)
tkinter.Button(btn_group,text="STOP",width=10,command=lambda:rec_instance.f2_handle_stop())\
    .grid(row=0, column=1,sticky=tkinter.W,padx=10)
tkinter.Button(btn_group,text="NEXT MODULE",width=15,command=lambda:rec_instance.f4_handle())\
    .grid(row=0, column=2,sticky=tkinter.W)
btn_group.grid(row=2,column=0,padx=10,pady=5,sticky=tkinter.W)

state_tips_label = None
def show_tips_label():
    global state_tips_label,dot_record_state,command_record_state
    if state_tips_label:
        result_label.destroy()
    result_out_str = ''
    on_state = False
    if dot_record_state:
        result_out_str += "Point Record: On      "
        on_state = True
    else:
        result_out_str += "Point Record: Off      "
    if command_record_state:
        result_out_str += "Script Record: On      "
        on_state = True
    else:
        result_out_str += "Script Record: Off      "
    if on_state:
        result_label = tkinter.Label(win,text = result_out_str,bg = "#90EE90")
    else:
        result_label = tkinter.Label(win,text = result_out_str)
    result_label.grid(row=0,column=0,padx=10,pady=5,sticky=tkinter.W)

def close_tips_label():
    global state_tips_label
    if state_tips_label:
        result_label.destroy()

result_label = None
def show_result(val):
    global result_label
    if result_label:
        result_label.destroy()
    result_label = tkinter.Label(win,text = val)
    result_label.grid(row=10,column=0,padx=10,pady=5,sticky=tkinter.W)

def close_result():
    global result_label
    if result_label:
        result_label.destroy()

# 点阵列
def render_grid():
    global dot_list,grid_list_wrapper
    close_result()
    if grid_list_wrapper:
        grid_list_wrapper.destroy()
    grid_list_wrapper = tkinter.Frame(win)
    if grid_state == 0:
        for index,item in enumerate(dot_list):
            e1 = tkinter.Variable()
            tke1 = tkinter.Entry(grid_list_wrapper,textvariable = e1)
            e1.set(",".join(map(lambda x:str(x), item)))
            tkb1 = tkinter.Button(grid_list_wrapper,text="DELETE",command=lambda n=index:(dot_list.pop(n),grid_list_wrapper.destroy(),render_grid()))
            tke1.grid(row=index,column=0,pady=5)
            tke1.bind('<Key>', lambda e,p=index,v=e1:entry_val_change(p,v))
            tkb1.grid(row=index,column=1,padx=5,pady=5)
    else:
        for index,item in enumerate(dot_list):
            e1 = tkinter.Variable()
            tke1 = tkinter.Entry(grid_list_wrapper,textvariable = e1)
            if index == 0 or index == 1:
                e1.set(",".join(map(lambda x:str(x), item[0:2])))
            elif index == 2:
                e1.set(",".join(map(lambda x:str(x), item[2:4])))
            else:
                e1.set(",".join(map(lambda x:str(x), item)))
            tkb1 = tkinter.Button(grid_list_wrapper,text="DELETE",command=lambda n=index:(dot_list.pop(n),grid_list_wrapper.destroy(),render_grid()))
            tke1.grid(row=index,column=0,pady=5)
            tke1.bind('<Key>', lambda e,p=index,v=e1:entry_val_change(p,v))
            tkb1.grid(row=index,column=1,padx=5,pady=5)
    grid_list_wrapper.grid(row=3,column=0,padx=10,pady=5,sticky=tkinter.W)
render_grid()

def render_command():
    global text_area,script_text,command_list
    if text_area:
        script_text.delete('0.0','end')
        script_text.insert(tkinter.END,'\n')
        script_text.insert(tkinter.END,'    @staticmethod\n')
        script_text.insert(tkinter.END,'    def %s(%s):\n'%(command_list["name"],command_list["param"]))
        script_text.update()
        script_text.see(tkinter.END)
        for i in command_list["data"]:
            script_text.insert(tkinter.END,i+'\n')
            script_text.update()
            script_text.see(tkinter.END)

record_btn = None
stop_record_btn = None
def remove_record():
    global record_btn,stop_record_btn
    if record_btn:
        record_btn.destroy()
    if stop_record_btn:
        stop_record_btn.destroy()

def show_record(params_num):
    global record_btn,stop_record_btn
    if record_btn:
        record_btn.destroy()
    if stop_record_btn:
        stop_record_btn.destroy()
    if params_num == 1:
        record_btn = tkinter.Button(win,text="RECORD",width=15,command=lambda:rec_instance.f3_handle_start(1))
    else:
        record_btn = tkinter.Button(win,text="RECORD",width=15,command=lambda:rec_instance.f3_handle_start(2))
    record_btn.grid(row=5, column=0,sticky=tkinter.W,padx=10,pady=5)
    stop_record_btn = tkinter.Button(win,text="STOP",width=15,command=lambda:rec_instance.f3_handle_stop())
    stop_record_btn.grid(row=5, column=0,sticky=tkinter.W,padx=140,pady=5)

def remove_text_area():
    global text_area
    if text_area:
        script_text.delete('0.0','end')
        text_area.destroy()
        text_area = None

def show_text_area():
    global text_area,script_text
    if text_area:
        script_text.delete('0.0','end')
        text_area.destroy()
        text_area = None
    text_area = tkinter.Frame(win)
    scroll = tkinter.Scrollbar()
    script_text = tkinter.Text(text_area,width = 50,height = 15)
    script_text.grid()
    script_text.bind('<Key>', text_val_change)
    scroll.config(command = script_text.yview)
    script_text.config(yscrollcommand = scroll.set)
    text_area.grid(row=6,column=0,padx=10,pady=5,sticky=tkinter.W)

def cmb_func(event):
    global grid_state,grid_list_wrapper,cmb_val,script_text,text_area,command_list
    if grid_list_wrapper:
        grid_list_wrapper.destroy()

    close_result()
    rec_instance.f3_handle_stop()
    remove_record()
    remove_text_area()
    command_list["data"] = []

    select_index = int(cmb.get().split(":")[0])

    if select_index == 1:
        cmb_val = 0
        grid_state = 0
        render_grid()
    elif select_index == 2:
        cmb_val = 1
        grid_state = 0
        render_grid()
        show_text_area()
    elif select_index == 3:
        cmb_val = 2
        grid_state = 0
        render_grid()
        show_record(1)
        show_text_area()
    elif select_index == 4:
        cmb_val = 3
        grid_state = 1
        render_grid()
        show_record(2)
        show_text_area()
    close_result()
cmb.bind("<<ComboboxSelected>>",cmb_func)

def clean_all():
    global dot_list,grid_state,cmb_val,cmb,grid_list_wrapper,command_list,script_text,text_area
    grid_state = 0
    dot_list = []
    cmb_val = 0
    cmb.current(0)
    if grid_list_wrapper:
        grid_list_wrapper.destroy()
    command_list = {
        "name":'',
        "param":'',
        "data":[]
    }
    remove_record()
    if text_area:
        script_text.delete('0.0','end')
        text_area.destroy()
        text_area = None

def generate_all():
    global rec_instance,command_list
    outpush_str = ""
    outpush_func = ""
    rec_instance.f2_handle_stop()
    rec_instance.f3_handle_stop()
    json_mod = {
        "pointJudge": [],
        "handle": {
            "type": 0,
            "event": []
        }
    }

    if len(dot_list) == 0:
        show_result("there is no pointJudge")
        return
    
    for item in dot_list:
        json_mod['pointJudge'].append({
            "dot": [item[0], item[1]],
            "color": item[2],
            "confidence":item[3]
        })
    json_mod["handle"]["type"] = cmb_val

    if cmb_val == 1:
        """
            click:          [0,0]
            swipe:          [0,0,0,0]
            next_module:    'next'
            sleep:           1000
        """
        sc_text = script_text.get("0.0","end").strip()
        if sc_text:
            json_mod["handle"]["event"] = sc_text.split("\n")
        else:
            show_result("please input event text")
            return
    elif cmb_val == 2:
        sc_text = script_text.get("0.0","end").strip()
        if sc_text:
            bold = re.compile('def (\S+)\(context\):')
            matches = re.search(bold,sc_text)
            if matches:
                json_mod["handle"]["event"] = [matches.group(1)]
            else:
                show_result("def format is not true")
                return
        else:
            show_result("please input event text")
            return
    elif cmb_val == 3:
        sc_text = script_text.get("0.0","end").strip()
        if sc_text:
            bold = re.compile('def (\S+)\(context,point\):')
            matches = re.search(bold,sc_text)
            if matches:
                json_mod["handle"]["event"] = [matches.group(1)]
            else:
                show_result("def format is not true")
                return
    
    show_result("create success")
    outpush_str = json.dumps(json_mod)
    rec_instance.write_into_json(outpush_str)
    if cmb_val == 2 or cmb_val == 3:
        rec_instance.append_command_to_py(command_list)
    clean_all()


btn_end_group = tkinter.Frame(win)
tkinter.Button(btn_end_group,text="CREATE",width=10,command=generate_all)\
    .grid(row=0, column=0,sticky=tkinter.W)
btn_end_group.grid(row=9,column=0,padx=10,pady=15,sticky=tkinter.W)

def task(name):
    global rec_instance
    rec_instance = RecordScript()
    try:
        rec_instance.run()
    except Exception as e:
        traceback.print_exc()
        print(e)
    
def init_script():
    p = Thread(target=task, args=('thread-1',))
    p.start()
win.after(0,init_script)
win.mainloop()