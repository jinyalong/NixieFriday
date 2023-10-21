from DS3231micro import DS3231
from ssd1306 import SSD1306_I2C
from ws2812 import WS2812
from HV57708 import HV57708
from irreciver import IR
from wifimgr import get_connection
from pindef import *
from machine import I2C,Pin,SPI,PWM,Timer,RTC
from umqtt.simple import MQTTClient
import ujson
import utime
import _thread
import machine
import urequests
import json


WEEKDAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

NOW_DAY = -1
NOW_HOUR = -1
NOW_MINUTE = -1
SECOND_COUNT = 0
ALL_FLASH_TIME = 600
TIME_SWITCH = 0

###### 模块定义 ######
dot1 = Pin(DOT1_PIN,Pin.OUT)
dot2 = Pin(DOT2_PIN,Pin.OUT)
i2c = I2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=100000)
spi = SPI(1)
spi.init(baudrate=3200000,mosi=Pin(WS2812_PIN))

ds3231 = DS3231(SCL_PIN, SDA_PIN)
oled = SSD1306_I2C(128,64,i2c,addr=60)
ir = IR(IRM_PIN)
ws2812 = WS2812(spi,led_count=6)
hv_en = Pin(HVEN_PIN,Pin.OUT)
hv57708 = HV57708(0)
dot1_pwm = PWM(dot1)
dot2_pwm = PWM(dot2)

ir_Timer = Timer(1)
clock_Timer = Timer(2)
rtc = RTC()
config = None
mqttClient = None
# 订阅的主题，接收推送的指令消息
topic_sub = None
# 发布的主题，发布自身状态
topic_rel = None

def upload_status(version):
  global mqttClient,hv_en,config,TIME_SWITCH
  dict = {}
  dict['VERSION'] = version;
  dict['HV_EN'] = hv_en.value()
  dict['WS2812'] = config['ws2812']
  dict['TIME_SWITCH'] = TIME_SWITCH
  dict['DOT'] = config['dots']['dot1']
  dict['FLASHTIME'] = config['flashTime']
  dict['STARTSTR'] = config['start_str']
  dict['HV57708']=config['hv57708']
  mqttClient.publish(topic_rel, ujson.dumps(dict))

def mqtt_thread():
  global mqttClient,ir
  while True:
    mqttClient.wait_msg()
    utime.sleep_ms(300)
    
def ir_handler(t):
  global ir
  changed,s,repeat,t_ok = ir.scan()
  if changed == True:
    if s == '*' and repeat > 50:
      upload_status()
    elif s == '#' and repeat > 100:
      machine.reset()
      
def sub_handler(topic, msg): 
  global ws2812,dot1_pwm,dot2_pwm,ALL_FLASH_TIME,hv_en,config,TIME_SWITCH
  args = msg.decode().split('$')
  if args[0] == 'ws2812':
    r = int(args[2])
    g = int(args[3])
    b = int(args[4])
    if args[1] == 'ALL':
      for i in range(0,6):
        config['ws2812'][i] = (r,g,b)
    else:
      index = 5-int(args[1])
      config['ws2812'][index] = (r,g,b)
    ws2812.show(config['ws2812'])
  elif args[0] == 'dot':
    if args[1] == 'ALL':
      if args[2] == 'ON':
        config['dots']['dot1'] = 1023
        config['dots']['dot2'] = 1023
        dot1_pwm.duty(1023)
        dot2_pwm.duty(1023)
      elif args[2] == 'OFF':
        config['dots']['dot1'] = 0

        config['dots']['dot2'] = 0
        dot1_pwm.duty(0)
        dot2_pwm.duty(0)
      elif args[2] == 'FLASH':
        config['dots']['dot1'] = 512
        config['dots']['dot2'] = 512
        dot1_pwm.duty(512)
        dot2_pwm.duty(512)
      else:
        print('非法参数')
    elif args[1] == 'LEFT':
      if args[2] == 'ON':
        config['dots']['dot2'] = 1023
        dot2_pwm.duty(1023)
      elif args[2] == 'OFF':
        config['dots']['dot2'] = 0
        dot2_pwm.duty(0)
      elif args[2] == 'FLASH':
        config['dots']['dot2'] = 512
        dot2_pwm.duty(512)
      else:
        print('非法参数')
    elif args[1] == 'RIGHT':
      if args[2] == 'ON':
        config['dots']['dot1'] = 1023
        dot1_pwm.duty(1023)
      elif args[2] == 'OFF':
        config['dots']['dot1'] = 0
        dot1_pwm.duty(0)
      elif args[2] == 'FLASH':
        config['dots']['dot1'] = 512
        dot1_pwm.duty(512)
      else:
        print('非法参数')
    else:
      print('非法参数')
  elif args[0] == 'hv57708':
    if args[1] == 'NORMAL':
      hv57708.set_change_mode(0)
      config['hv57708'] = 0
    elif args[1] == 'FLOP':
      hv57708.set_change_mode(1)
      config['hv57708'] = 1
    else:
      print('非法参数')
  elif args[0] == 'FLASHTIME':
    if args[1] == 'SHORT':
      config['flashTime'] = 5
      ALL_FLASH_TIME = 300
    elif args[1] == 'LONG':
      config['flashTime'] = 10
      ALL_FLASH_TIME = 600
    elif args[1] == 'VERYLONG':
      config['flashTime'] = 30
      ALL_FLASH_TIME = 1800
    else:
      print('非法参数')
  elif args[0] == 'STARTSTR':
    if len(args[1]) == 6 and args[1].isdigit() == True:
      config['start_str'] = args[1]
    else:
      print('非法参数')
  elif args[0] == 'HIGHVOLTAGEBOOST':
    if args[1] == 'ON':
      hv_en.value(1)
    elif args[1] == 'OFF':
      hv_en.value(0)
    else:
      print('非法参数')
  elif args[0] == 'RESET':
    machine.reset()
  elif args[0] == 'UPLOAD_STATUS':
    version = int(args[1])
    upload_status(version)
  elif args[0] == 'TIME_SWITCH':
    _index = int(args[1])
    TIME_SWITCH ^= (1 << _index)
    config['time_switch'] = TIME_SWITCH
  else:
    print('非法参数')
  
  with open("config.json",'w') as f:
    f.write(ujson.dumps(config))

def reset_time():
  global ds3231,rtc,NOW_DAY,config
  url = 'http://quan.suning.com/getSysTime.do'
  res=urequests.get(url).text
  print(res)
  j=json.loads(res)
  t2_date = j['sysTime2'].split()[0] #日期
  t2_time = j['sysTime2'].split()[1] #时间
  ds3231.setDate([int(x) for x in t2_date[2:].split('-')])   #设置初始日期年、月、日
  ds3231.setTime([int(x) for x in t2_time.split(':')])   #设置初始时间时、分、秒
  rtc.init(ds3231.getDateTime())
  config['last_day'] = NOW_DAY
  with open("config.json",'w') as f:
    f.write(ujson.dumps(config))
    
def timerSecondFlash(t):
  global SECOND_COUNT,NOW_HOUR,NOW_DAY,ds3231,hv57708,oled,ALL_FLASH_TIME,TIME_SWITCH,dot1,dot2
  SECOND_COUNT += 1
  _tmp = rtc.datetime()
  _date = '-'.join((str(_tmp[0]),str(_tmp[1]),str(_tmp[2])))
  _weekday = _tmp[3]
  _time = ''
  for i in range(4,7):
    if _tmp[i] < 10:
      _time += '0' + str(_tmp[i])
    else:
      _time += str(_tmp[i])
  hv57708.display(_time)
  if SECOND_COUNT == ALL_FLASH_TIME:
    hv57708.prevent_poisoning()
    SECOND_COUNT = 0
  if NOW_DAY != _date:
    NOW_DAY = _date
    reset_time()
    oled.showDateWeekDay(_date,WEEKDAYS[_weekday])
  if NOW_HOUR != _tmp[4]:
    NOW_HOUR = _tmp[4]
    hv_en.value(TIME_SWITCH & (1 << NOW_HOUR))
      
    # 更新RTC
  if NOW_MINUTE != _tmp[5]:
    # 闹钟检测
    if ds3231.alarmTriggert(1):
      print('闹钟1')
    if ds3231.alarmTriggert(2):
      print('闹钟2')
def main():
  global mqttClient,NOW_DAY,config,oled,topic_rel,topic_sub,TIME_SWITCH
  # 1.读取配置文件 并加载一些初始化配置 
  with open("config.json",'r') as load_f:
    config = ujson.load(load_f)
  topic_sub = config['mqtt']['topic_sub']
  topic_rel = config['mqtt']['topic_rel']
  mqttClient = MQTTClient(
    config['mqtt']['clientID'],
    config['mqtt']['mqttServer'],
    config['mqtt']['port'],
    config['mqtt']['user'],
    config['mqtt']['password'],
    60
  )
  NOW_DAY = config['last_day']
  mqttClient.set_callback(sub_handler)
  ALL_FLASH_TIME = config['flashTime']*60
  hv57708.set_change_mode(config['hv57708'])
  TIME_SWITCH = config['time_switch']
  
  # 2.升压模块初始化，清空显示
  hv_en.value(0)
  hv57708.show_nothing()
  dot1_pwm.freq(1)
  dot2_pwm.freq(1)
  dot1_pwm.duty(0)
  dot2_pwm.duty(0)
  utime.sleep_ms(100)
  
  hv_en.value(1)
  hv57708.display_normal(config['start_str'])
  oled.show_powered_by()
  utime.sleep(1)
  oled.showBigWifiLogo()
  ws2812.show(config['ws2812'])
  hv57708.prevent_poisoning()
  
  hv57708.show_nothing()
  dot1_pwm.duty(config['dots']['dot1'])
  dot2_pwm.duty(config['dots']['dot2'])
  
  # 
  esp32_wlan = get_connection(oled)
  try:
    mqttClient.connect()
    oled.mqtt_connecting()
    utime.sleep(2)
    oled.mqtt_connect_res(True)
    mqttClient.subscribe(topic_sub)
  except:
    oled.mqtt_connect_res(False)
    print('mqtt connect false!')  
  _thread.start_new_thread(mqtt_thread,())
  
  if esp32_wlan.isconnected():
    oled.wifi_on()
  rtc.init(ds3231.getDateTime())
  _tmp = rtc.datetime()
  _date = '-'.join((str(_tmp[0]),str(_tmp[1]),str(_tmp[2])))
  _weekday = _tmp[3]
  oled.showDateWeekDay(_date,WEEKDAYS[_weekday])
  ir_Timer.init(period=500,mode=Timer.PERIODIC, callback=ir_handler)
  clock_Timer.init(period=1000, mode=Timer.PERIODIC, callback=timerSecondFlash)
if __name__ == '__main__':
    main()

  












