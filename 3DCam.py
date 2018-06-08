# coding: utf-8
# Copyright (c) 2018 Jun Hirabayashi (jun@hirax.net)
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

from manualCapture import *

@on_main_thread
def main():
    for i in range(100, 900, 25):
        focusPosition = float(i)/1000.0
        imagefilePath = '{:.3f}'.format(focusPosition)+'.jpg'
        manualCapture( AVCaptureVideoOrientationLandscapeRight,
                       AVCaptureExposureModeLocked,
                       1, 30,
                       400.0,
                       AVCaptureFocusModeLocked,
                       focusPosition,
                       [6000.0, 0.0],
                       [AVCaptureTorchModeOff, 0.01],
                       imagefilePath,
                       'Pythonista Album')

main()

