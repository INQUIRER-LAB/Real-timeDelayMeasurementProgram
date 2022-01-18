# スペクトルアナライザプログラム（鷹合研）
#
# 準備(Linux Mint20.2にて動作確認済み）：
#  sudo apt-get install python3-pigpio python3-scipy python3-pyaudio
#  sudo apt-get install python3-matplotlib
#
# 入力するオーディオデバイスの設定などに使うと良い
#   sudo apt-get install pavucontrol
#

from asyncore import read
from itertools import count
import sys
from time import time
from typing import Counter
import pyaudio
import datetime
import time
import numpy as np
import signal

#####################
#
#  適宜変更
#

## 仮想のステレオマイク
CHANNELS = 2
FS = 44100

########################
#
#  変更は必要ないかも
 
CHUNK=1024    # オーディオデバイスと1回でやりとりするサンプル点数(チャンネルあたり)
FORMAT = pyaudio.paInt16 # フォーマット

# グローバルデータ
# VIEW_SEC = 5  # 録音可能時間（秒）
# audio_seq = np.zeros( (CHANNELS, VIEW_SEC * FS) )   # 音声信号の系列(モノラル)
cnt = 0
count = 0
count1 = 0
data = 0
leatancy = 0
#   録音した音声データの取り出し（コールバック）
def cb_audio_proc(in_data, frame_count, time_info, status):
    # global audio_seq
    global cnt,data,data1,count,count1,leatancy
    x=np.frombuffer(in_data, dtype=np.int16).reshape(CHUNK,CHANNELS).T # frombufferで高速に16bitデータ取り出し(スキャン方向に注意)
    # x[0] R(受信音)
    # # x[1] L(原音)
    v = np.max(np.abs(x))
    cnt += 1
    t = (time.perf_counter_ns()-T0)/(10**9)
    # 原音の開始取得
    r0 = (x[1][0])**2
    if r0 > 0 and count == 0:
            data = t
            count += 1
    # 受信音の開始取得
    r1 = (x[0][0])**2
    if r1 > 0 and count1 == 0:
            data1 = t
            count1 += 1
    latancy = data1-data
    print('\r%10.3f[sec]' % (latancy), end = '')
        
    return None, pyaudio.paContinue

# メインルーチン
def main():

    # AUDIO-RECORDING
    p = pyaudio.PyAudio()

    p.open(format=FORMAT,
                channels=CHANNELS,
                rate=FS,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=cb_audio_proc)
    input('Hit Any Key')



#####################################
if __name__ == '__main__':
    global T0
    signal.signal(signal.SIGINT, signal.SIG_DFL) # C-c で強制終了
    T0 = time.perf_counter_ns()
    main()