# encoding: utf-8
import configparser
cf = configparser.ConfigParser()

import os
import sys
import time
import linecache
from urllib.request import urlretrieve
FILE_FOLDER_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\'
cf.read(FILE_FOLDER_PATH+"config.ini",encoding='utf-8')
from ld_control import Dnconsole as dn
import shutil
import uuid
from PIL import ImageGrab,Image
import hashlib
import hex_handle 
import traceback
import datetime

import cv2 as cv

from aip import AipOcr
import random
from ident_card import create_realname_and_id_number
from emailReceive import EmailReceive

APP_ID = cf.get("Screen-Setting", "APP_ID")
API_KEY = cf.get("Screen-Setting", "API_KEY")
SECRET_KEY = cf.get("Screen-Setting", "SECRET_KEY")
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)


FILE_PARENT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'\\'

# 获取当前模拟器列表
def get_running_emu():
    return dn.list_running()

class VScript(object):
    # 目标模拟器索引值
    _target = 0
    # 运行中的模块序号 起始为0
    _run_module = int(cf.get("Script-Setting", "RUN_START_MODULE"))
    # 默认偏移距离
    _default_offset = int(cf.get("Screen-Setting", "DEFAULT_OFFSET"))

    _second_snap_path = ''

    # 当前账号密码
    _account = ''
    _password = ''

    _user_name_cache = ''

    snap_img_cache_path = ''

    params_data = {}

    _dump_time_cache = ''

    _actor_list_cache = ""

    def __init__(self,target_index = 0):
        self._target = target_index
        self.v_create_dir(dn.share_path + '/'+str(target_index)+'/')
        self._second_snap_path = dn.share_path + '/'+str(target_index)+'/screen_snap.png'
        self._second_dump_path = dn.share_path + '/'+str(target_index)+'/screen_snap.dump'

    def v_ramdom(self,num, r):
        return num + random.uniform(-r, r)

    def setParamsData(self,data):
        self.params_data = data
    
    def getParamsData(self):
        return self.params_data

    def v_ramdom_xy(self,x,y):
        ra_x = self.v_ramdom(x, self._default_offset)
        ra_y = self.v_ramdom(y, self._default_offset)
        if(ra_x < 0):
            ra_x = 0
        elif(ra_x > 960):
            ra_x = 960 
        if(ra_y < 0):
            ra_y = 0
        elif(ra_y > 540):
            ra_y = 540
        return ra_x,ra_y

    def click(self,x,y,delay,ramdom_time=0):
        ramdom_add = delay + random.uniform(0, ramdom_time)
        ra_x,ra_y = self.v_ramdom_xy(x,y)
        dn.touch(self._target,ra_x,ra_y,ramdom_add)

    def swipe(self,x1,y1,x2,y2,delay,ramdom_time=0):
        ramdom_add = delay + random.uniform(0, ramdom_time)
        ra_x1,ra_y1 = self.v_ramdom_xy(x1,y1)
        ra_x2,ra_y2 = self.v_ramdom_xy(x2,y2)
        dn.swipe(self._target,(ra_x1,ra_y1),(ra_x2,ra_y2),ramdom_add)

    def point_judge(self,color_arr):
        return hex_handle.color_compare(self._second_dump_path,color_arr,self._target)

    def muti_color_judge(self,color_arr):
        color_find_area = [color_arr[0]["dot"][0],color_arr[0]["dot"][1],color_arr[1]["dot"][0],color_arr[1]["dot"][1]]
        target_color = color_arr[2]["color"]
        target_color_confidence = color_arr[2]["confidence"]
        offset_aim_dot = color_arr[2]["dot"]
        offset_dot = []
        for index in range(3, len(color_arr)):
            pox = {}
            pox["offset"] = [color_arr[index]["dot"][0]-offset_aim_dot[0],color_arr[index]["dot"][1]-offset_aim_dot[1]]
            pox["color"] = color_arr[index]["color"]
            offset_dot.append(pox)
        return hex_handle.offset_compare(self._second_dump_path,color_find_area,target_color,target_color_confidence,offset_dot)

    def v_sleep(self,times):
        arm_time = int(times + random.uniform(0, 200))
        time.sleep(arm_time/1000)

    def sleep(self,time):
        self.v_sleep(time)

    def set_log(self,fn_name):
        try:
            log_path_snap = FILE_PARENT_FOLDER+'log\\'+self.v_now_time()+'\\'
            self.v_create_dir(log_path_snap)
            with open(log_path_snap + 'error.txt', 'a',encoding='utf-8') as file_obj:
                file_obj.write(str(fn_name))
            img_path = dn.screen_snap(self._target,'error')
            shutil.copy(img_path,  log_path_snap+'error.png')
        except Exception as e:
            traceback.print_exc()
            print(e)

    def md_jtl(self,name):
        return hashlib.md5(name.encode(encoding='UTF-8')).hexdigest()
    
    def get_FileModifyTime(self,filePath):
        t = int(os.path.getmtime(filePath)*1000)
        return t

    def get_FileSize(self,path):
        size = int(os.path.getsize(path))
        return size

    def get_FileCreateTime(self,filePath):
        t = int(os.path.getctime(filePath)*1000)
        return t

    def loop_snap_dump(self):
        dn.dnld(self._target, 'screencap /sdcard/Pictures/%s/%s.dump'%(self._target,'screen_snap'))
        while True:
            file_mod_time = self.get_FileModifyTime(self._second_dump_path)
            file_size_m = self.get_FileSize(self._second_dump_path)
            if file_mod_time and file_mod_time != self._dump_time_cache and file_size_m != 0:
                self._dump_time_cache = file_mod_time
                break
    def touch_down(self):
        dn.dnld(self._target, "sendevent dev/input/event2 3 57 0\nsendevent dev/input/event2 1 330 1\nsendevent dev/input/event2 1 325 1\n")

    def touch_up(self):
        dn.dnld(self._target, "sendevent dev/input/event2 3 57 -1\nsendevent dev/input/event2 1 330 0\nsendevent dev/input/event2 1 325 0\nsendevent dev/input/event2 0 0 0\n")

    def move_to(self,x,y):
        dn.dnld(self._target,"sendevent dev/input/event2 3 53 %s\nsendevent dev/input/event2 3 54 %s\nsendevent dev/input/event2 0 0 0\n"%(x,y))

    def _v_text_ocr(self,filepath='',accur=False):
        try:
            if(not accur):
                options = {}
                options["language_type"] = "CHN_ENG"
                options["detect_direction"] = "true"
                options["probability"] = "true"
                with open(filepath, 'rb') as f:
                    result = client.basicGeneral(f.read(),options)
                    if(len(result['words_result']) > 0):
                        return result['words_result'][0]['words'].strip()
                    else:
                        return None
            else:
                options = {}
                options["detect_direction"] = "true"
                options["probability"] = "true"
                with open(filepath, 'rb') as f:
                    result = client.basicAccurate(f.read(),options)
                    if(len(result['words_result']) > 0):
                        return result['words_result'][0]['words'].strip()
                    else:
                        return None
        except Exception as e:
            print('_v_text_ocr error')
            return None

    def _text_ocr(self,all_path,accur = False):
        if(not all_path):return
        return self._v_text_ocr(all_path,accur)


    def text_into(self,text):
        dn.input_text(self._target,text)

    def ocr_area(self,x1,y1,x2,y2,accur = False):
        self.v_sleep(1000)
        file_floder = os.path.dirname(self._second_snap_path)+'\\'
        self.v_crop_img(x1,y1,x2,y2,self._second_snap_path,file_floder+'crop_img.png')
        self.v_sleep(1200)
        return self._text_ocr(file_floder+'crop_img.png',accur)

    def key_code_press(self,key_num):
        dn.key_code_event(self._target,key_num)
    
    def delect_file(self,file_path):
        dn.del_file_libs(self._target,file_path)

    def copy_file(self,old_path,new_path):
        dn.copy_file(self._target,old_path,new_path)

    def set_run_module(self,module_num):
        self._run_module = module_num

    def next_module(self):
        self._run_module = self._run_module + 1
    
    # 获取当前运行的模块序号
    def get_run_module(self):
        return self._run_module

    # 设置账号
    def set_account(self,acc):
        self._account = acc

    def set_password(self,pwd):
        self._password = pwd

    # 获取账号
    def get_account(self):
        return self._account
    
    # 随机身份证和姓名 名字，id
    def ramdom_idcard(self):
        return create_realname_and_id_number()

    # 获取密码
    def get_password(self):
        return self._password

    def un_install_app(self):
        dn.uninstall(self._target)
        self.v_sleep(2000)
        return True

    def create_ram_unid(self):
        return str(uuid.uuid4().fields[-1])

    def change_imei_and_restart(self):
        try:
            dn.quit(self._target)
            self.v_sleep(1000)
            dn.change_device_data(self._target)
            self.v_sleep(1000)
            dn.launch(self._target)
            dn_times = 0
            while True:
                self.v_sleep(1000)
                if dn.is_running(self._target):
                    break
                else:
                    dn_times += 1
                    if(dn_times >120):
                        dn_times = 0
                        dn.launch(self._target)
                    print('%s restarting'%(self._target))
            return True
        except Exception as e:
            traceback.print_exc()
            print(e)

    def install_app(self,path):
        if(not path):
            return False
        return dn.install(self._target,path)

    # 清空app数据
    def clean_app(self):
        return dn.clear_app(self._target)

    def get_ramdom_only_name(self):
        sub_name = self.get_ramdom_textline('./names.txt')
        all_name = sub_name + self.v_ran_str(4)
        return all_name

    #获取txt中随机一行  txtpath例如:./names.txt
    def get_ramdom_textline(self,txt_path):
        with open(txt_path, 'r+',encoding="utf-8") as data:
            n = len(data.readlines())
            i = random.randint(1, n-1)
            line=linecache.getline(txt_path,i)
            print(line)
            return line

    def get_mail_code_sms(self,account,pwd,keys=r'你的验证码为:(\d+)（15分钟内有效）'):
        self.v_sleep(20000)
        a = EmailReceive(account,pwd)
        ax_result = a.getEmail(keyword=('验证码',),onlyUnsee=False,findAll=False)
        return re.search(keys,ax_result[0][1][0]).group(1)

    def set_file_acc(self,url,android_save_path):
        try:
            file_name = os.path.basename(url)
            file_end_path = os.path.dirname(self._second_snap_path) + '/' + file_name
            urlretrieve(url, file_end_path)
            ld_file_path = '/sdcard/Pictures/' + str(self._target) + '/' + file_name
            self.copy_file(ld_file_path,android_save_path)
            # 移除临时存放的文件
            os.remove(file_end_path)
            return True
        except Exception as e:
            traceback.print_exc()
            print(e)
            return False

    def get_file_acc(self,emu_path):
        pc_file_path = dn.share_path + '/'+str(self._target)+'/files'
        self.v_create_dir(pc_file_path)
        file_name = os.path.basename(emu_path)
        ld_file_path = '/sdcard/Pictures/' + str(self._target) + '/files/' + file_name
        self.copy_file(emu_path,ld_file_path)
        return dn.share_path + '/'+ str(self._target) +'/files/'+ file_name

    def img_push(self,snp_path = ''):
        snp_path = snp_path or self.create_ram_unid()
        self.v_sleep(1000)
        path_imx = dn.screen_snap(self._target,snp_path)
        self.v_sleep(2400)
        self.snap_img_cache_path = path_imx
        return path_imx

    def split_str_exten(self,paths):
        filepath_img,tempfilename_img = os.path.split(paths)
        shotname,extension = os.path.splitext(tempfilename_img)
        return shotname,extension

    # 判断路径是否存在 不存在则创建 相对于PC而言
    def v_create_dir(self,dirs):
        if not os.path.exists(dirs):
            os.makedirs(dirs)

    # 获取当前时间
    def v_now_time(self)->str:
        return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')

    def v_crop_img(self,x1,y1,x2,y2,old_path,new_path):
        img = Image.open(old_path)
        cropped = img.crop((x1, y1, x2, y2))
        cropped.save(new_path)

    def v_ran_str(self,num):
        H = 'abcdefghijklmnopqrstuvwxyz0123456789'
        salt = ''
        for i in range(num):
            salt += random.choice(H)
        return salt
    
    def v_ran_str_x(self,num):
        H = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        salt = ''
        for i in range(num):
            salt += random.choice(H)
        return salt

    # 启动app
    def v_run_apk(self):
        dn.invokeapp(self._target)
        self.v_sleep(2000)
        return True

    # 获取目录下所有文件
    def v_get_dir_files(self,dirname):
        result = []#所有的文件

        for maindir, subdir, file_name_list in os.walk(dirname):
            for filename in file_name_list:
                apath = os.path.join(maindir, filename)#合并成一个完整路径
                result.append(apath)

        return result

    def v_compare_pic(self,screen: str, template: str, threshold: float):
        size = None
        rex_len = 0
        try:
            time.sleep(1)
            scr = cv.imread(screen)
            tp = cv.imread(template)
            result = cv.matchTemplate(scr, tp, cv.TM_CCOEFF_NORMED)
            rex_len = len(result)
            size = tp.shape
        except cv.error:
            print('文件错误：', screen, template)
            time.sleep(1)
            try:
                scr = cv.imread(screen)
                tp = cv.imread(template)
                result = cv.matchTemplate(scr, tp, cv.TM_CCOEFF_NORMED)
                rex_len = len(result)
                size = tp.shape
            except cv.error:
                return False, rex_len
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
        print('%s %s'%(template,min_val))
        if min_val > threshold:
            return False, rex_len
        return True, rex_len

    def v_ocr_actor(self):
        pc_img_path = self.img_push('snap_ocr_actor_screen')
        all_template_mod = self.v_get_dir_files(FILE_FOLDER_PATH+'compare')
        rs_obj = {}
        for mod_path in all_template_mod:
            result,act_num = self.v_compare_pic(pc_img_path,mod_path,0.9)
            if result:
                file_name,sub = os.path.basename(mod_path).split('.')
                rs_obj[file_name] = act_num
        cp_str = ''
        for name in rs_obj:
            cp_str+= name+'*'+rs_obj[name]+','
        cp_str = cp_str[:-1]
        return cp_str

    def noop_end_tag(self,delayTime,pointJudge,eventFunc):
        self.v_sleep(delayTime)
        self.loop_snap_dump()
        self.v_sleep(500)
        result_point = self.point_judge(pointJudge)
        if not result_point:
            eventFunc()

    def area_find_dot_point(self,pointJudge):
        self.loop_snap_dump()
        self.v_sleep(500)
        result_point = self.muti_color_judge(pointJudge)
        if result_point:
            return {
                x:int(result_point[0]),
                y:int(result_point[1])
            }
        else:
            return None