# スペクトルアナライザプログラム（鷹合研）
#
# 準備(Linux Mint20.2にて動作確認済み）：
#  sudo apt-get install python3-pigpio python3-scipy python3-pyaudio
#  sudo apt-get install python3-matplotlib
#
# 入力するオーディオデバイスの設定などに使うと良い
#   sudo apt-get install pavucontrol
#

import sys
import pyaudio
import datetime
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
VIEW_SEC = 5  # 録音可能時間（秒）
audio_seq = np.zeros( (CHANNELS, VIEW_SEC * FS) )   # 音声信号の系列(モノラル)


#   録音した音声データの取り出し（コールバック）
def cb_audio_proc(in_data, frame_count, time_info, status):
    global audio_seq
    x=np.frombuffer(in_data, dtype=np.int16).reshape(CHUNK,CHANNELS).T # frombufferで高速に16bitデータ取り出し(スキャン方向に注意)
    # x[0] R(受信音)
    # x[1] L(原音)
    
    # 原音の開始地点の取得
    r0 = (x[1][0])**2
    # r0 = r0/r0
    if r0 > 0:
        print("OK")
        
    # 受信音の開始地点の取得
    r1 = ([0][0])**2
    r1 = r1/r1
    cr1 = np.convolve(r1, np.array([1.0/100 for i in range(100)]), mode='same')
    cr1[cr1==1] = 1
    cr1[cr1!=1] = 0

    # print('---------')
    print(r1)

    # print(x[0][0],x[1][0])
    # print('  :     :')
    # print(x[0][-1],x[1][-1])
    # print('---------')

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
    signal.signal(signal.SIGINT, signal.SIG_DFL) # C-c で強制終了
    main()