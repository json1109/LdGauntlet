# LdGauntlet
  基于模拟器(雷电)的自动化测试工具</br>
  无需root或者装app至模拟器内，与按键精灵等内置相比，识别效率略低但隐匿性更强
## 实际效率可直接通过命令调取雷电api进行测试

</br>
### 使用方法：</br>
  通过运行gui_record.py抓取色值点生成脚本</br>
  生成的json和脚本存储在main/script文件夹中</br>
  修改config.ini后运行main/main.py</br>
</br>
### 可配置的属性：(config.ini)</br>
```html
     <!--配置项-->
      [File-Path]
          ;apk包名
          package_name = 
      [Screen-Setting]
          ;模拟器分辨率
          screen_width = 960
          screen_height = 540
          ;坐标偏移范围量
          DEFAULT_OFFSET = 3
          ;百度OCR
          APP_ID = 
          API_KEY = 
          SECRET_KEY = 
      [Script-Setting]
          ACCOUNT_TYPE = 1
          RUN_SCRIPT = 
          RUN_START_MODULE = 0
          IS_COLUMN = 0
          IS_DEV = 0
          IP_NAME = 
          REPEAT_ERROR = 0
          EMPTY_ERROR = 0
```
### 注意事项：</br>
    本项目使用的是色值匹配、多色值匹配及偏移色值匹配。
    通过将整体流程拆分成各个模块进行识别，因此如果出现重复的色值点请通过拆分模块来避免识别错误。
    如果需要使用百度OCR需配置APP_ID、API_KEY、SECRET_KEY。
