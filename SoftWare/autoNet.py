import network
import usocket
import utime
import gol


NETWORK_PROFILES = 'wifi.ini'
esp32_ap = None
client = None
addr = None
esp32_wlan = None

def read_profiles():
    with open(NETWORK_PROFILES) as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        key, value = line.strip("\n").split(':')
        profiles[key] = value
    return profiles

def write_profiles(profiles):
    lines = []
    for key, value in profiles.items():
        lines.append("%s:%s\n" % (key, value))
    with open(NETWORK_PROFILES, "w") as f:
        f.write(''.join(lines))
        
def start_ap():
  global esp32_ap
  esp32_ap= network.WLAN(network.AP_IF)
  esp32_ap.active(True)
  esp32_ap.config(essid="NixieFriday", authmode=network.AUTH_WPA_WPA2_PSK, password="12345678")

def connect_wifi(ssid,pwd):
  global esp32_wlan
  global addr
  global client
  retry_times = 10
  esp32_wlan.connect(ssid,pwd)
  while not esp32_wlan.isconnected() and retry_times > 0:
    utime.sleep(1)
    retry_times -= 1
  if esp32_wlan.isconnected():
    msg = str(esp32_wlan.ifconfig())
    client.send(msg)
    profile = {}
    profile['ssid'] = ssid
    profile['password'] = pwd
    write_profiles(profile)
    return True
  else:
    client.send('connect false')
    return False
  
# 配网
def distribution_network():
  global client,addr
  # 开启ap热点
  start_ap()
  # 监听tcp80端口，只允许一个连接
  tcp_server = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
  tcp_server.bind(('0.0.0.0',80))
  tcp_server.listen(1)  
  client,addr = tcp_server.accept()
  # 连上之后设置为阻塞式IO
  client.setblocking(True)
  # 开始轮询接收来自TCP客户端的消息
  while True:
    data = client.recv(1024)
    data = data.decode('utf-8')
    print(data)
    strs = data.split('$')
    if strs[0] == 'ssid' and strs[2] == 'password':
      if connect_wifi(strs[1],strs[3]):
        break
    # 客户端发送跳过配网的指令
    elif strs[0] == 'skip':
      break
  
def auto_connect_wlan():
  global esp32_wlan
  esp32_wlan = network.WLAN(network.STA_IF)
  esp32_wlan.active(True)   
  gol.set_value('esp32_wlan', esp32_wlan)
  config = read_profiles()
  esp32_wlan.connect(config['ssid'],config['password'])
  retry_times = 10
  while not esp32_wlan.isconnected() and retry_times > 0:
      print('connectting...',retry_times)
      utime.sleep(1)
      retry_times -= 1
  if esp32_wlan.isconnected():
    print('connect success')
  else:
    print('connect false')
    print('start config network')
    distribution_network()
 




