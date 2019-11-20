# encoding: utf-8

import datetime
import json
import os
import random
from datetime import date
from datetime import timedelta
import string


ARR = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
LAST = ('1', '0', 'x', '9', '8', '7', '6', '5', '4', '3', '2')

PATH = lambda p: os.path.abspath(
    os.path.join(os.path.dirname(__file__), p)
)
districtcode_path = PATH('./districtcode.txt')
d = datetime.datetime.now()


def get_random_phonenumber():
    number = random.choice(['133', '151', '187', '170']) + "".join(random.choice("0123456789") for i in range(8))
    return number


def intersection_of_path(file_path):
    relative_file_path = os.path.normpath(file_path)
    relative_list = relative_file_path.split(os.sep)
    sys_path_now_list = os.path.dirname(__file__).split(os.sep)[1:]
    for i in range(len(sys_path_now_list)):
        if (relative_list[0] == sys_path_now_list[i]):
            intersection = i
    prepose_path = ''.join(['/%s' % y for y in sys_path_now_list[:intersection]])
    return os.path.join(prepose_path, file_path)


def _getDistrictCode():
    with open(districtcode_path, "r",encoding="utf-8") as file:
        data = file.read()

    district_list = data.split('\n')
    code_list = []
    for node in district_list:
        # print node
        if node[10:11] != ' ':
            state = node[10:].strip()
        if node[10:11] == ' ' and node[12:13] != ' ':
            city = node[12:].strip()
        if node[10:11] == ' ' and node[12:13] == ' ':
            district = node[14:].strip()
            code = node[0:6]
            code_list.append(
                {"state": state, "city": city, "district": district, "code": code})
    return code_list

def create_realname_and_id_number():
    real_name = random.choice(['赵','张','孙','刘','徐','王','李','陈','杨','黄','吴','周','徐','孙','邓','曹','彭','曾']) + "".join(
        random.choice(['成', '小', '家', '洋', '钱', '广', '利','依','紫','萱','涵','易','忆','之','幻','巧','水','风','安','寒','白','亦','惜','玉','碧','春','怜','雪','听','南','念','蕾','夏']) for i in range(2))
    '''生成身份证号'''
    code_list = _getDistrictCode()
    id = code_list[random.randint(0, len(code_list))]['code']  # 地区项
    id = id + str(random.randint(1960, 1999))  # 年份项
    da = date.today() + timedelta(days=random.randint(1, 366))  # 月份和日期项
    id = id + da.strftime('%m%d')
    id = id + str(random.randint(100, 999))  # ，顺序号简单处理

    i = 0
    count = 0
    weight = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]  # 权重项
    checkcode = {'0': '1', '1': '0', '2': 'X', '3': '9', '4': '8',
                 '5': '7', '6': '6', '7': '5', '8': '5', '9': '3', '10': '2'}  # 校验码映射
    for i in range(0, len(id)):
        count = count + int(id[i]) * weight[i]
    id = id + checkcode[str(count % 11)]  # 算出校验码
    return real_name, id


def generate_bank_card_number():
    bank_card = random.choice(['62122653']) + "".join(random.choice("0123456789") for i in range(11))
    return bank_card


def now_time():
    now = datetime.datetime.now()
    strdatetime = now.strftime("%Y%m%d%H%M%S")
    return strdatetime


def string_to_dict(s):
    import ast
    result = ast.literal_eval(s)
    return result


def dict_to_string(d):
    return json.dumps(d)


def gen_random_string(str_len):
    return ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(str_len))