# encoding: utf-8
import os
from main_run import MainThread
from pynput import mouse, keyboard
from v_script import VScript, get_running_emu
import requests
from urllib.parse import urlencode
import threading
import time
import re
import configparser
import shutil
from urllib.request import urlretrieve

cf = configparser.ConfigParser()
FILE_FOLDER_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\'
cf.read(FILE_FOLDER_PATH+"config.ini",encoding='utf-8')
IS_DEV = int(cf.get("Script-Setting", "IS_DEV"))
IP_NAME = cf.get("Script-Setting", "IP_NAME")

emu_module_list = {}

def on_press(key):
    if(key == keyboard.Key.esc):
        os._exit(0)
    if(IS_DEV == 1 and key == keyboard.Key.f2):
        try:
            target_emu_index = input('please input emulator index:')
            new_dir_path = FILE_FOLDER_PATH + "nxlog"
            if not os.path.exists(new_dir_path):
                os.makedirs(new_dir_path)
            target_context = emu_module_list[str(target_emu_index)]
            last_target = target_context._target
            last_module = target_context.get_run_module()
            now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
            with open(FILE_FOLDER_PATH + "nxlog/log.txt",'a+') as f:
                f.write(now_time+' --- module:'+str(last_module)+' --- emulator_index:'+str(last_target)+' \n')
            pc_snap_path = target_context.img_push()
            shutil.copy(pc_snap_path, FILE_FOLDER_PATH + "nxlog/snapLog.png")
            print('log记录成功')
        except Exception as e:
            print(e)

listener = keyboard.Listener(on_press=on_press)
listener.start()


class MixTread(MainThread):

    def __init__(self, context):
        return super().__init__(context)

    def mx_get_account(self):
        return 

    def mx_upload_account(self, filePath):
        return 

    def mx_push_account(self,postdata):
        return 

    def change_config(self,basePath):
        return

    # 初始化应用
    def set_account(self):
        return True

    def round_over(self):
        return

    def round_fail(self):
        return

if __name__ == "__main__":
    emu_list = get_running_emu()
    for emu_item in emu_list:
        context = VScript(emu_item.index)
        t_line = MixTread(context)
        emu_module_list[str(emu_item.index)] = context
        t_line.start()