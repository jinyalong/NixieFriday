from machine import Pin, PWM
from pindef import BEEP_PIN
import utime

# 定义音调频率
tones = {'1': 262, '2': 294, '3': 330, '4': 349, '5': 392, '6': 440, '7': 494, '-': 0}

melodys = {
  "little_star" : "1155665-4433221-5544332-5544332-1155665-4433221"
}

def buzzer_sounds(index):
  # 设置GPIO口为IO输出，然后通过PWM控制无缘蜂鸣器发声
  beeper = PWM(Pin(BEEP_PIN, Pin.OUT), freq=0, duty=1000)
  for tone in melody:
      freq = tones[tone]
      if freq:
          beeper.init(duty=1000, freq=freq)  # 调整PWM的频率，使其发出指定的音调
      else:
          beeper.duty(0)  # 空拍时一样不上电
      # 停顿一下 （四四拍每秒两个音，每个音节中间稍微停顿一下）
      utime.sleep_ms(400)
      beeper.duty(0)  # 设备占空比为0，即不上电
      utime.sleep_ms(100)

  beeper.deinit()  # 释放PWM


