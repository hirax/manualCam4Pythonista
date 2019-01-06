# coding: utf-8
# Copyright (c) 2018 Jun Hirabayashi (jun@hirax.net)
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

from manualCapture import *

@on_main_thread
def main():
    ext = '.DNG'
    #for iso in [50, 100, 200, 400]:   # iso
    for scale in [5*1000, 5*1000, 10*1000, 20*1000, 40*1000, 80*1000, 160*1000,320*1000,640*1000,1280*1000]:   # time
        imagefileName = 'iso:050_timescale:{}'.format(scale) + ext
        manualCapture( AVCaptureVideoOrientationLandscapeRight,
                       AVCaptureExposureModeLocked,
                       1*1000, scale,
                       50,
                       AVCaptureFocusModeLocked,
                       0.7, #focusPosition,
                       [6000.0, 0.0],
                       [AVCaptureTorchModeOff, 0.01],
                       imagefileName,
                       'Pythonista Album',
                       ext,
                       True)
        time.sleep(2.5)

main()

