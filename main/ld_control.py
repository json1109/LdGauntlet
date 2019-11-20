# encoding: utf-8
import os
import shutil
import time
from xml.dom.minidom import parseString
import configparser
import traceback

FILE_FOLDER_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\'

cf = configparser.ConfigParser()
cf.read(FILE_FOLDER_PATH+"config.ini", encoding='utf-8')
secs = cf.sections()

dn_ld = None
dn_console = None
dn_share_path = None

disk_in = ('C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q')
try:
    for path_li in disk_in:
        if os.path.exists(path_li+':\\ChangZhi\\dnplayer2\\dnconsole.exe'):
            dn_console = path_li+':\\ChangZhi\\dnplayer2\\dnconsole.exe '
            dn_ld = path_li+':\\ChangZhi\\dnplayer2\\ld.exe '
            dn_share_path = path_li+':\\ChangZhi\\dnplayer2\\ldshare'
            break
    if(not dn_ld or not dn_console or not dn_share_path):
        raise ValueError('path not exist')
except Exception as e:
    print('Exception out of system')

dn_package_name = cf.get("File-Path", "package_name")
is_column = cf.get("Script-Setting", "IS_COLUMN")

class DnPlayer(object):
    def __init__(self, info: list):
        super(DnPlayer, self).__init__()
        # 索引，标题，顶层窗口句柄，绑定窗口句柄，是否进入android，进程PID，VBox进程PID
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

class Dnconsole:
    console = dn_console
    ld = dn_ld
    share_path = dn_share_path

    @staticmethod
    def get_list():
        cmd = os.popen(Dnconsole.console + 'list2')
        text = cmd.read()
        cmd.close()
        info = text.split('\n')
        result = list()
        for line in info:
            if len(line) > 1:
                dnplayer = line.split(',')
                result.append(DnPlayer(dnplayer))
        return result

    @staticmethod
    def list_running() -> list:
        result = list()
        all = Dnconsole.get_list()
        for dn in all:
            if dn.is_running() is True:
                result.append(dn)
        return result

    @staticmethod
    def is_running(index: int) -> bool:
        all = Dnconsole.get_list()
        if index >= len(all):
            raise IndexError('%d is not exist' % index)
        return all[index].is_running()

    @staticmethod
    def dnld(index: int, command: str, silence: bool = True):
        cmd = Dnconsole.ld + '-s %d %s' % (index, command)
        if silence:
            os.system(cmd)
            return ''
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def adb(index: int, command: str, silence: bool = False) -> str:
        cmd = Dnconsole.console + \
            'adb --index %d --command "%s"' % (index, command)
        if silence:
            os.system(cmd)
            return ''
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def install(index: int,dn_apk_path):
        if not os.path.exists(dn_apk_path):
            return
        try:
            dir_path, apk_name = dn_apk_path.rsplit("/", 1)
            path = Dnconsole.share_path + '/' + apk_name
            if not os.path.exists(path):
                shutil.copy(path, dn_apk_path)
            time.sleep(1)
            Dnconsole.dnld(
                index, 'pm install /sdcard/Pictures/%s' % (apk_name))
            while True:
                time.sleep(1)
                if Dnconsole.has_install(index):
                    break
            return True
        except Exception as e:
            traceback.print_exc()
            print(e)
            return False

    @staticmethod
    def uninstall(index: int):
        if not Dnconsole.has_install(index):
            return
        cmd = Dnconsole.console + \
            'uninstallapp --index %d --packagename %s' % (
                index, dn_package_name)
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def invokeapp(index: int):
        if not Dnconsole.has_install(index):
            return
        cmd = Dnconsole.console + \
            'runapp --index %d --packagename %s' % (index, dn_package_name)
        process = os.popen(cmd)
        result = process.read()
        process.close()
        # print(result)
        return result

    @staticmethod
    def stopapp(index: int):
        if not Dnconsole.has_install(index):
            return
        cmd = Dnconsole.console + \
            'killapp --index %d --packagename %s' % (index, dn_package_name)
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def input_text(index: int, text: str):
        cmd = Dnconsole.console + \
            'action --index %d --key call.input --value %s' % (index, text)
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def get_package_list(index: int) -> list:
        result = list()
        text = Dnconsole.dnld(index, 'pm list packages', silence=False)
        info = text.split('\n')
        for i in info:
            if len(i) > 1:
                result.append(i[8:])
        return result

    @staticmethod
    def has_install(index: int):
        if Dnconsole.is_running(index) is False:
            return False
        return dn_package_name in Dnconsole.get_package_list(index)

    @staticmethod
    def launch(index: int):
        cmd = Dnconsole.console + 'launch --index ' + str(index)
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def quit(index: int):
        cmd = Dnconsole.console + 'quit --index ' + str(index)
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def set_screen_size(index: int):
        cmd = Dnconsole.console + 'modify --index %d --resolution 1080,1920,480' % index
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def touch(index: int, x: int, y: int, delay: int = 0):
        if is_column == '1':
            cx = x
            x = y
            y = cx
            x = 540 - x
        if delay == 0:
            print(x, y)
            Dnconsole.dnld(index, 'input tap %d %d' % (x, y))
        else:
            Dnconsole.dnld(index, 'input swipe %d %d %d %d %d' %
                           (x, y, x, y, delay))

    @staticmethod
    def swipe(index, coordinate_leftup: tuple, coordinate_rightdown: tuple, delay: int = 0):
        x0 = coordinate_leftup[0]
        y0 = coordinate_leftup[1]
        x1 = coordinate_rightdown[0]
        y1 = coordinate_rightdown[1]
        if is_column == '1':
            c1 = x0
            x0 = y0
            x0 = 540 - x0
            y0 = c1
            c2 = x1
            x1 = y1
            x1 = 540 - x1
            y1 = c2
        if delay == 0:
            Dnconsole.dnld(index, 'input swipe %d %d %d %d' % (x0, y0, x1, y1))
        else:
            Dnconsole.dnld(index, 'input swipe %d %d %d %d %d' %
                           (x0, y0, x1, y1, delay))

    @staticmethod
    def copy(name: str, index: int = 0):
        cmd = Dnconsole.console + 'copy --name %s --from %d' % (name, index)
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def add(name: str):
        cmd = Dnconsole.console + 'add --name %s' % name
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def auto_rate(index: int, auto_rate: bool = False):
        rate = 1 if auto_rate else 0
        cmd = Dnconsole.console + \
            'modify --index %d --autorotate %d' % (index, rate)
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def change_device_data(index: int):
        # 改变设备信息
        cmd = Dnconsole.console + \
            'modify --index %d --imei auto --imsi auto --simserial auto --androidid auto --mac auto' % index
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def reboot_device(index: int):
        cmd = Dnconsole.console + \
            'reboot --index %d' % index
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def change_cpu_count(index: int, number: int):
        cmd = Dnconsole.console + \
            'modify --index %d --cpu %d' % (index, number)
        process = os.popen(cmd)
        result = process.read()
        process.close()
        return result

    @staticmethod
    def get_activity_name(index: int):
        text = Dnconsole.dnld(
            index, '"dumpsys activity top | grep ACTIVITY"', False)
        text = text.split(' ')
        for i, s in enumerate(text):
            if len(s) == 0:
                continue
            if s == 'ACTIVITY':
                return text[i + 1]
        return ''

    @staticmethod
    def wait_activity(index: int, activity: str, timeout: int) -> bool:
        for i in range(timeout):
            if Dnconsole.get_activity_name(index) == activity:
                return True
            time.sleep(1)
        return False

    @staticmethod
    def screen_snap(index: int, img_name: str = 'screen_snap')->str:
        try:
            Dnconsole.dnld(index, 'mkdir /sdcard/Pictures/%s' % (index))
        except Exception as e:
            pass
        Dnconsole.dnld(
            index, 'screencap -p /sdcard/Pictures/%s/%s.png' % (index, img_name))
        time.sleep(1)
        return Dnconsole.share_path + '/'+str(index)+'/'+img_name+'.png'

    @staticmethod
    def key_code_event(index: int, key_num):
        Dnconsole.dnld(index, 'input keyevent %s' % (key_num))

    @staticmethod
    def copy_file(index: int, old_path, new_path):
        Dnconsole.dnld(index, 'cp %s %s' % (old_path, new_path))

    @staticmethod
    def del_file_libs(index: int, file_folder):
        Dnconsole.dnld(index, 'rm -r %s' % (file_folder))

    @staticmethod
    def clear_app(index: int):
        if not Dnconsole.has_install(index):
            return
        try:
            Dnconsole.dnld(index, 'pm clear %s' % (dn_package_name))
            time.sleep(2)
            return True
        except Exception as e:
            traceback.print_exc()
            print(e)
            return False
