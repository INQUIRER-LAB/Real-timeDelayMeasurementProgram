# スペクトルアナライザプログラム（鷹合研）
import pyaudio
import time
import numpy as np
import signal

#####################
## 仮想のステレオマイク
## x[0] R(受信音), x[1] L(原音)
CHANNELS = 2
FS = 44100
########################
## オーディオ設定
CHUNK=1024    # オーディオデバイスと1回でやりとりするサンプル点数(チャンネルあたり)
FORMAT = pyaudio.paInt16 # フォーマット
########################
# グローバルデータ
# 開始判定
start_L = 0
start_R = 0
# 開始時間
sound_L = 0
sound_R = 0
# 遅延時間
leatancy = 0
cr0 = 0
cr1 = 0
########################

# 録音した音声データの取り出し（コールバック）
def cb_audio_proc(in_data, frame_count, time_info, status):
    global sound_L, sound_R, start_L, start_R, leatancy, cr0, cr1
    x = np.frombuffer(in_data, dtype = np.int16).reshape(CHUNK, CHANNELS).T # frombufferで高速に16bitデータ取り出し(スキャン方向に注意)
    t = (time.perf_counter_ns()-T0)/(10**9)
    
    # 原音の開始取得
    r0 = x[1][0]
    if r0 > 0.5 and start_L == 0:
            sound_L = t
            start_L += 1

    # 受信音の開始取得
    r1 = x[0][0]
    if r1 > 0.5 and start_R == 0:
            sound_R = t
            start_R += 1

    # 遅延時間取得
    if sound_L != 0 and sound_R != 0:
        latancy = sound_R-sound_L
        print('\r%10.3f[sec]' % (latancy), end = '')
        exit()
    else:
        print('\r   処理中@_@  ',end='')
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