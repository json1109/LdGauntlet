# encoding: utf-8
import sys
import time
import os
import uuid
from threading import Thread

sys.path.append('../')

from v_script import VScript,get_running_emu
import importlib
import traceback
import json
import random
import configparser

cf = configparser.ConfigParser()
FILE_FOLDER_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\'
cf.read(FILE_FOLDER_PATH+"config.ini",encoding='utf-8')
RUN_SCRIPT = cf.get("Script-Setting", "RUN_SCRIPT")
ACCOUNT_TYPE = int(cf.get("Script-Setting", "ACCOUNT_TYPE"))
IS_DEV = int(cf.get("Script-Setting", "IS_DEV"))
REPEAT_ERROR = int(cf.get("Script-Setting", "REPEAT_ERROR"))
EMPTY_ERROR = int(cf.get("Script-Setting", "EMPTY_ERROR"))

path = 'script.'+ RUN_SCRIPT +'.ScriptFunction'

model_path, class_name = path.rsplit(".", 1)
model = importlib.import_module(model_path)
sf = getattr(model, class_name)()  # 反射并实例化

RES_PATH = FILE_FOLDER_PATH + 'script\\' +RUN_SCRIPT+'\\'

class MainThread(Thread):

    context = None

    account = ''
    password = ''

    MAX_RUN_ROUND = 8
    max_count_restart = 0

    mistack_none_count = 0
    mistack_repeat_count = 0

    _match_success = False
    _repeat_index = 0
    _is_closed_app = False

    def __init__(self,context):
        Thread.__init__(self) 
        self.context = context

    def _get_files_account(self,path):
        file_count=0
        for dirpath, dirnames, filenames in os.walk(path):
            for item in filenames:
                file_count = file_count+1
        return file_count

    def _json_load(self,path):
        with open(path,encoding='utf-8') as json_file:
            data = json.load(json_file)
            return data

    # 空匹配异常处理
    def mistack_handle_none(self,event=None):
        if EMPTY_ERROR == 0:
            return
        if(event == 'clean'):
            self.mistack_none_count = 0
        else:
            self.mistack_none_count += 1
        if(self.mistack_none_count > EMPTY_ERROR):
            self.mistack_none_count = 0
            self.reopen_app(self.context)

    # 循环匹配异常处理
    def mistack_handle_repeat(self,module_index):
        if REPEAT_ERROR == 0:
            return
        if(module_index != self._repeat_index):
            self.mistack_repeat_count = 0
        else:
            self.mistack_repeat_count += 1
        if(self.mistack_repeat_count > REPEAT_ERROR):
            self.mistack_repeat_count = 0
            self.reopen_app(self.context)
        self._repeat_index = module_index

    def _match_reset(self,i):
        self.mistack_handle_none('clean')
        self.mistack_handle_repeat(i)
        self._match_success = True

    def _restart_check(self):
        if(self.max_count_restart > self.MAX_RUN_ROUND):
            context = self.context
            self.max_count_restart = 0
            context.change_imei_and_restart()
            context.sleep(3000)
            return True
        return

    # overwrite
    def set_account(self):
        print('please rewrie this interface')

    # overwrite
    def round_over(self):
        print('please rewrie this interface')

    # overwrite
    def round_fail(self):
        print('please rewrie this interface')

    def run(self):
        context = self.context
        while True:
            try:
                if(self._restart_check()):
                    continue
                runFlag = False
                if IS_DEV == 1:
                    runFlag = True
                else:
                    self.init_app_state(self.context)
                    runFlag = self.set_account()
                if runFlag:
                    self._is_closed_app = False
                    self.max_count_restart += 1
                    context.sleep(1000)
                    while True:
                        context.loop_snap_dump()
                        running_path = RES_PATH + str(context.get_run_module())+'\\'
                        # 获取检测模块内的检测数量
                        if os.path.exists(running_path):
                            acc_num = self._get_files_account(running_path)
                            self._match_success = False
                            index_tag = 0
                            for i in range(int(acc_num/2)):
                                # 先获取配置文件 根据配置去匹配
                                check_json = running_path + str(index_tag) + '.json'
                                check_png = running_path + str(index_tag) + '.png'
                                
                                if not os.path.exists(check_json):
                                    exist_json_flag = True
                                    while exist_json_flag:
                                        index_tag += 1
                                        check_json = running_path + str(index_tag) + '.json'
                                        check_png = running_path + str(index_tag) + '.png'
                                        if os.path.exists(check_json):
                                            exist_json_flag = False
                                            break

                                index_tag += 1

                                obj = self._json_load(check_json)

                                if not obj['pointJudge'] or not len(obj['pointJudge']) > 0:
                                    print('this obj was no pointJudge!!!')
                                    continue

                                judge_fn_list = obj['pointJudge']
                                if int(obj['handle']['type']) == 3:
                                    result_point = context.muti_color_judge(judge_fn_list)
                                    if result_point:
                                        handle_event = obj["handle"]["event"]
                                        if len(handle_event) == 0:
                                            context.click(int(result_point[0]),int(result_point[1]),80,40)
                                        else:
                                            for ev_fn in handle_event:
                                                getattr(sf,ev_fn)(context,result_point)
                                                
                                        # 如果是匹配到的则break 重新循环当前模块
                                        self._match_reset(i)
                                        break
                                else:
                                    list_center_point = obj['pointJudge'][0]['dot']
                                    if context.point_judge(judge_fn_list):
                                        handle_type = obj["handle"]["type"]
                                        handle_event = obj["handle"]["event"]
                                        # 0 1 2
                                        if(int(handle_type) == 0):
                                            if list_center_point:
                                                context.click(list_center_point[0],list_center_point[1],80,40)
                                        elif(int(handle_type) == 1):
                                            for ev in handle_event:
                                                if type(ev) == list:
                                                    if len(ev) == 2:
                                                        context.click(int(ev[0]),int(ev[1]),80,40)
                                                    else:
                                                        context.swipe(int(ev[0]),int(ev[1]),int(ev[2]),int(ev[3]),180,40)
                                                else:
                                                    if ev == 'next':
                                                        context.next_module()
                                                    else:
                                                        context.sleep(int(ev))
                                        elif(int(handle_type) == 2):
                                            for ev_fn in handle_event:
                                                getattr(sf,ev_fn)(context)

                                        # 如果是匹配到的则break 重新循环当前模块
                                        self._match_reset(i)
                                        break

                            # 该运行的模块内全部无法匹配时执行的默认行为
                            if not self._match_success:
                                text_fn_file = running_path + 'default.txt'
                                if os.path.exists(text_fn_file):
                                    with open(text_fn_file, 'r',encoding='utf-8') as file_obj:
                                        script_line = file_obj.readlines()
                                        for text_fn in script_line:
                                            exec(text_fn,{'context':context})
                                self.mistack_handle_none()
                            if(self._is_closed_app):
                                break
                        else:
                            if IS_DEV != 1:
                                self.round_over()
                            print('next account being run')
                            context.key_code_press(187)
                            context.sleep(2000)
                            context.swipe(564,453,213,455,180,40)
                            context.sleep(2000)
                            # 返回主页
                            context.key_code_press(3)
                            context.sleep(2000)
                            break

                    # 没有模块时重置回首个模块
                    context.set_run_module(0)
                else:
                    print('sleep 10s to get account again')
                    time.sleep(10)
            except Exception as e:
                traceback.print_exc()
                print(e)

    def init_app_state(self,context):
        context.key_code_press(187)
        context.sleep(2000)
        context.swipe(564,453,213,455,180,40)
        context.sleep(2000)
        # 返回主页
        context.key_code_press(3)
        context.sleep(2000)

    def reopen_app(self,context):
        print("Reopen app and restart script !")
        if IS_DEV != 1:
            self.round_fail()
        # 打开应用清除当前
        context.key_code_press(187)
        context.sleep(2000)
        context.swipe(564,453,213,455,180,40)
        context.sleep(2000)
        context.key_code_press(3)
        context.sleep(2000)
        context.set_run_module(999)
        self._is_closed_app = True
