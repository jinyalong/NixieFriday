from machine import Pin
from pindef import *
import utime

dic = [
    [63, 54, 55, 56, 57, 58, 59, 60, 61, 62],
    [53, 44, 45, 46, 47, 48, 49, 50, 51, 52],
    [43, 34, 35, 36, 37, 38, 39, 40, 41, 42],
    [33, 24, 25, 26, 27, 28, 29, 30, 31, 32],
    [23, 14, 15, 16, 17, 18, 19, 20, 21, 22],
    [13, 4, 5, 6, 7, 8, 9, 10, 11, 12]
]

power_on_num = [
  '000000',
  '111111',
  '222222',
  '333333',
  '444444',
  '555555',
  '666666',
  '777777',
  '888888',
  '999999'
]

power_off_str = 'XXXXXX'

class HV57708:
    def __init__(self,hv57708_mode,change_mode=0):
        self.change_mode = change_mode
        self.HV57708_LE = Pin(HV57708_LE_PIN, Pin.OUT)
        self.HV57708_POL = Pin(HV57708_POL_PIN, Pin.OUT)
        self.HV57708_CLK = Pin(HV57708_CLK_PIN, Pin.OUT)
        self.HV57708_DIN4 = Pin(HV57708_DIN4_PIN, Pin.OUT)
        self.HV57708_DIN3 = Pin(HV57708_DIN3_PIN, Pin.OUT)
        self.HV57708_DIN2 = Pin(HV57708_DIN2_PIN, Pin.OUT)
        self.HV57708_DIN1 = Pin(HV57708_DIN1_PIN, Pin.OUT)
        self.hv57708_init(hv57708_mode)

    def hv57708_init(self, hv57708_mode):
        self.HV57708_POL.value(hv57708_mode)
        self.HV57708_DIN4.value(0)
        self.HV57708_DIN3.value(0)
        self.HV57708_DIN2.value(0)
        self.HV57708_DIN1.value(0)
        self.HV57708_CLK.value(0)
        self.HV57708_LE.value(0)
        
    def hv57708_senddata(self, data1, data2):
        tmp = data1
        for i in range(0, 8):
            self.HV57708_CLK.value(0)
            self.HV57708_DIN4.value(tmp & 1)
            tmp >>= 1
            self.HV57708_DIN3.value(tmp & 1)
            tmp >>= 1
            self.HV57708_DIN2.value(tmp & 1)
            tmp >>= 1
            self.HV57708_DIN1.value(tmp & 1)
            tmp >>= 1
            self.HV57708_CLK.value(1)
            self.HV57708_CLK.value(0)
        tmp = data2
        for i in range(0, 8):
            self.HV57708_CLK.value(0)
            self.HV57708_DIN4.value(tmp & 1)
            tmp >>= 1
            self.HV57708_DIN3.value(tmp & 1)
            tmp >>= 1
            self.HV57708_DIN2.value(tmp & 1)
            tmp >>= 1
            self.HV57708_DIN1.value(tmp & 1)
            tmp >>= 1
            self.HV57708_CLK.value(1)
            self.HV57708_CLK.value(0)
            
    def hv57708_output(self):
        self.HV57708_LE.value(1)
        self.HV57708_LE.value(0)
        
    def set_change_mode(self, value):
      if value == '':
        return self.change_mode
      else:
        self.change_mode = value
        
    def display(self, content):
      if self.change_mode == 0:
        self.display_normal(content)
      else:
        self.display_flop(content)
      
    # 正常模式显示6个数字
    def display_normal(self, content):
        x = 0x0000000000000000
        for index, every_char in enumerate(content):
            if every_char != 'X':
                x |= (1 << dic[5 - index][int(every_char)])
        self.hv57708_senddata(int(x & 0xffffffff),int((x >> 32) & 0xffffffff))
        self.hv57708_output()
    
    # 翻牌模式显示6个数字
    def display_flop(self,content):
        tmp = content
        for i in range(10):
            self.display_normal(tmp[0:5]+str(i))
            utime.sleep_ms(20)
        self.display_normal(content)
        
    # 防止阴极中毒程序
    def prevent_poisoning(self):
      for i in range(10):
        for str in power_on_num:
          self.display_normal(str)
          utime.sleep_ms(20)
          
    # 辉光管不显示任何数字
    def show_nothing(self):
        self.display_normal(power_off_str)








