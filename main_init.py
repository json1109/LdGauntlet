# encoding: utf-8
import os
import re
import time

dn_console = ''
dn_ld = ''
dn_share_path = ''

def copy(name: str, index: int = 0):
    cmd = dn_console + 'copy --name %s --from %d' % (name, index)
    process = os.popen(cmd)
    result = process.read()
    process.close()
    return result

def change_config(file,new_str):
    file_data = ""
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if 'statusSettings.sharedPictures' in line:
                bold = re.compile('sharedPictures\": \"(\S+)\"')
                matches = re.search(bold,line)
                line = line.replace(matches.group(1),new_str)
                line = line.replace('\\','/')
            file_data += line
    with open(file,"w",encoding="utf-8") as f:
        f.write(file_data)

def set_share_path(new_path):
    # 重置所有的共享地址
    for i in range(100):
        path_config = os.path.dirname(new_path) + '\\vms\\config' + '\\leidian'+ str(i) +'.config'
        if os.path.exists(path_config):
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            change_config(path_config,new_path)

if __name__ == '__main__':
    if(dn_share_path):
        set_share_path(dn_share_path)
        for i in range(10):
            copy('copyEmulator-'+i)
            time.sleep(10)