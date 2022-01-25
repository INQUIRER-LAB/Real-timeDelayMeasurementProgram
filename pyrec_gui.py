# スペクトルアナライザプログラム（鷹合研）
#
# 準備(Linux Mint20.2にて動作確認済み）：
#  sudo apt-get install python3-pigpio python3-scipy python3-pyaudio
#  sudo apt-get install python3-matplotlib
#
# 入力するオーディオデバイスの設定などに使うと良い
#   sudo apt-get install pavucontrol
#
DESC="STEREO AUDIO VIEWER (TAKAGO_LAB. 2022-01-23)"

from pydoc import visiblename
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib import gridspec
import matplotlib.pyplot as plt
 
import pyaudio
import wave       # Waveファイルの操作
import datetime
 
import numpy as np
from scipy.signal import spectrogram
 
import signal

from playsound import playsound

#####################
#
#  適宜変更
#
CHANNELS = 2
FS = 44100
 
########################
#
#  変更は必要ないかも
 
CHUNK=1024    # オーディオデバイスと1回でやりとりするサンプル点数(チャンネルあたり)
FORMAT = pyaudio.paInt16 # フォーマット
 
VIEW_SEC = 5  # 画面にプロットする時間（秒）
VIEW_FREQ_MAX = 2000   # 画面に表示する周波数の上限（切り出したときの上限値）
 
FONT_SZ = 16  # フォントサイズ
 
#####################
#
#  さらに変更は必要ないかも
 
AUDIO_SIG_RANGE = (-32768,32767)  # 音声信号の範囲
UPDATE_TICK_MS = 10   # 画面表示の更新間隔(ミリ秒単位)

 
#####################################
# グローバルデータ
audio_seq = np.zeros( (CHANNELS, VIEW_SEC * FS) )   # 音声信号の系列(モノラル)
  
#####################################
# クラス
class GUI(QWidget):
    def __init__(self, parent=None):
        global tt

        super().__init__(parent)
        self.timer_stat = False
 
        fnt=self.font()
        fnt.setPointSize(FONT_SZ)
        self.setFont(fnt)
 
        self.VIEW_CH=0
 
 
        # 空の縦レイアウトを作る
        self.mylayout = QVBoxLayout()
        self.setLayout(self.mylayout)
 
 
        # Matplotlib（準備）
        self.fig = plt.figure()
        spec = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[0.5,0.5]) # 縦に3つの図
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.mylayout.addWidget(self.canvas)
        self.fig.set_size_inches(10, 30) # 描画の大きさ
 
        # プロットの登録1（音声波形の表示）
        self.axes1 = self.fig.add_subplot(spec[0])
        tt = np.linspace(0,VIEW_SEC-(1/FS), VIEW_SEC*FS)
        self.line1, = self.axes1.plot(tt, audio_seq[self.VIEW_CH,:])
        self.line1x, = self.axes1.plot([-1,-1], [-32767,32767])
        self.axes1.set_ylim(AUDIO_SIG_RANGE[0], AUDIO_SIG_RANGE[1])
        self.axes1.set_xlim(0,VIEW_SEC)
        self.axes1.grid()
        self.axes1.set_yticks( np.arange( AUDIO_SIG_RANGE[0], AUDIO_SIG_RANGE[1]+1, (AUDIO_SIG_RANGE[1]-AUDIO_SIG_RANGE[0])/8) )
        self.axes1.set_xticks( np.arange( 0, VIEW_SEC+1, 1) )
        self.axes1.set_ylabel('Received sound', fontsize=FONT_SZ)
 
 


        # プロットの登録2（音声波形の表示）
        self.axes2 = self.fig.add_subplot(spec[1])
        self.line2, = self.axes2.plot(tt, audio_seq[self.VIEW_CH,:])
        self.line2x, = self.axes2.plot([-1,-1], [-32767,32767])
        self.axes2.set_ylim(AUDIO_SIG_RANGE[0], AUDIO_SIG_RANGE[1])
        self.axes2.set_xlim(0,VIEW_SEC)
        self.axes2.grid()
        self.axes2.set_yticks( np.arange( AUDIO_SIG_RANGE[0], AUDIO_SIG_RANGE[1]+1, (AUDIO_SIG_RANGE[1]-AUDIO_SIG_RANGE[0])/8) )
        self.axes2.set_xticks( np.arange( 0, VIEW_SEC+1, 1) )
        self.axes2.set_ylabel('Original sound', fontsize=FONT_SZ)
 
        # キャンバスのナビゲーションバーを隠す
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()
 
        # スピンボックス(1)...画面表示されるスペクトログラムの上限
        self.spin1 = QSpinBox()
        self.spin1.setMinimum(0)
        self.spin1.setMaximum(32000)
        self.spin1.setValue(1000)
        self.spin1.setSingleStep(1000)
        self.spin1.setPrefix("検知する振幅のしきい値 : ")
        self.mylayout.addWidget(self.spin1)
 
        # スピンボックス(2)...画面表示されるスペクトログラムの下限
        self.spin2 = QSpinBox()
        self.spin2.setMinimum(0)
        self.spin2.setMaximum(32000)
        self.spin2.setValue(1000)
        self.spin2.setSingleStep(1000)
        self.spin2.setPrefix("検知する振幅のしきい値 : ")
        self.mylayout.addWidget(self.spin2)
 
        self.lbl1 = QLabel('Diff: %7.3f[msec]' % 0, self)
        self.mylayout.addWidget(self.lbl1)

        # ボタン1
        self.button1 = QPushButton('(*_*)',self)
        self.button1.clicked.connect(self.myact_button1)
        self.mylayout.addWidget(self.button1)
 
        # ボタン2
        self.button2 = QPushButton('RUN WAVEFILE-OUT',self)
        self.button2.clicked.connect(self.myact_button2)
        self.mylayout.addWidget(self.button2)
  
        # ボタン3
        self.button3 = QPushButton('Play',self)
        self.button3.clicked.connect(self.myact_button3)
        self.mylayout.addWidget(self.button3)

        # インターバルタイマー（Matplotlibの画面更新に使用）
        self.timer = QTimer()
        self.timer.setSingleShot(False)  # 連続 or 1ショットか
        self.timer.setInterval(UPDATE_TICK_MS)
        self.timer.timeout.connect(self.update_fig)
 
        # 1度，ボタンを押したことにする
        self.myact_button1()
 
 
 
    # ボタン1が押された時のコールバック
    def myact_button1(self):
        self.timer_stat = not self.timer_stat
        if self.timer_stat is True:
             self.timer.start()
             self.button1.setText("STOP MONITOR")
        else:
             self.timer.stop()
             self.button1.setText("RUN MONITOR")
 
    # ボタン2が押された時のコールバック
    def myact_button2(self):
        global wf_stat, wavf
        wf_stat = not wf_stat
        if wf_stat is True:
 
            # WAVEファイル
            wav_file_name=datetime.datetime.now().strftime('%Y-%m-%d--%H-%M-%S--')+str(datetime.datetime.now().microsecond)+'.wav'
            wavf = wave.open( wav_file_name, 'wb')
            wavf.setnchannels(CHANNELS)
            wavf.setsampwidth(SAMPLEWIDTH)
            wavf.setframerate(FS)
 
            self.button2.setText("...Saving to "+wav_file_name)
            self.button2.setStyleSheet(
                        "QPushButton { color: white; background-color: red; border-radius: 5px; font-size: 20pt}"
                        "QPushButton:pressed { background-color: darkred }" )    
        else:
            wavf.close()
            self.button2.setText("RUN WAVEFILE-OUT")    
            self.button2.setStyleSheet(
                        "QPushButton { color: white; background-color: blue; border-radius: 5px; font-size: 20pt}"
                        "QPushButton:pressed { background-color: darkblue }" )         
    
    def myact_button3(self):
        # playsound("/home/nakamura/play.wav")
        global wf
        global pa 
        global data
        global stream

        wf = wave.open('/home/nakamura/play.wav', 'rb')
        pa = pyaudio.PyAudio()
        stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()), channels=2, rate=wf.getframerate(), output=True)
        data = wf.readframes(-1)

        while data != '':
            stream.write(data)
            data = wf.readframes(-1)
        
        stream.stop_stream()
        stream.close()
        pa.terminate()
 
    # 定期的に実行する処理（Matplotlibの画面更新や，PWM信号の送出など）
    def update_fig(self):
        self.line1.set_ydata( audio_seq[0,:] )
        self.line2.set_ydata( audio_seq[1,:] )


        a=np.argmax(abs(audio_seq[0,:]))
        b=np.argmax(abs(audio_seq[1,:]))
        if abs(audio_seq[0,a])<self.spin1.value() and abs(audio_seq[1,b])<self.spin2.value():
            self.line1x.set_xdata([-1,-1])
            self.line2x.set_xdata([-1,-1])
        else:
            self.line1x.set_xdata([tt[a],tt[a]])
            self.line2x.set_xdata([tt[b],tt[b]])
            self.lbl1.setText('Diff: %7.3f[msec]' % abs(1000*(tt[b]-tt[a])))

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
 
#####################################
# 関数
 
 
#   録音した音声データの取り出し（コールバック）
def cb_audio_proc(in_data, frame_count, time_info, status):
    global audio_seq
    global pwm_seq
    x=np.frombuffer(in_data, dtype=np.int16).reshape(CHUNK,CHANNELS).T # frombufferで高速に16bitデータ取り出し(スキャン方向に注意)
    ## WAVファイルに追記
    if wf_stat:
        wavf.writeframes(in_data)
    ## フィルタリング
    if False:
        pass
    audio_seq = np.c_[ audio_seq[:,CHUNK:], x.astype(float)] # 古いデータを廃棄し，新しいデータを入れる
    return None, pyaudio.paContinue
 
def main():
    global pi
    global wf_stat
    global SAMPLEWIDTH
    global p

    # AUDIO-RECORDING
    p = pyaudio.PyAudio()
    p.open(format=FORMAT,
                channels=CHANNELS,
                rate=FS,
                input=True, 
                frames_per_buffer=CHUNK,
                stream_callback=cb_audio_proc)
 
    # waveに書き出すための準備
    SAMPLEWIDTH=p.get_sample_size(FORMAT)
    wf_stat = False

    # GUI
    app = QApplication(sys.argv)
    main = GUI()
    main.setWindowTitle(DESC)
    main.show()
 
    sys.exit(app.exec_())
 
#####################################
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL) # C-c で強制終了
    main()