# coding: utf-8
# Copyright (c) 2018 Jun Hirabayashi (jun@hirax.net)
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

from manualCapture import *

@on_main_thread
def main():
    ext = '.DNG'
    for denominator in [5, 15, 30, 60]:      # time
        imagefileName = 'iso:050_timescale:{}'.format(scale)+ext
        manualCapture(
            AVCaptureVideoOrientationLandscapeRight, # 撮影向き
            AVCaptureExposureModeLocked, # 露出設定
            1, denominator, # 1/denominator (秒)
            50,  # ISO値 (23-736)
            AVCaptureFocusModeLocked, # レンズ焦点モード
            0.7, # 焦点距離（0.0-1.0）
            [6000.0, 0.0], # 色温度
            [AVCaptureTorchModeOff, 0.01], # ライト設定
            imagefileName, #画像ファイル名
            'Pythonista Album', # アルバム名
            ext, # 画像保存形式
            True )  # .npy で「も」保存するか
        time.sleep(2.5)

main()
