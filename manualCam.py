# coding: utf-8
# coding: utf-8
# Copyright (c) 2018 Jun Hirabayashi (jun@hirax.net)
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

from objc_util import *
import ui, time, photos, threading

AVCaptureSession = ObjCClass('AVCaptureSession')
AVCaptureDevice = ObjCClass('AVCaptureDevice')
AVCaptureDeviceInput = ObjCClass('AVCaptureDeviceInput')
AVCapturePhotoOutput = ObjCClass('AVCapturePhotoOutput')
AVCaptureVideoPreviewLayer = ObjCClass('AVCaptureVideoPreviewLayer')
AVCapturePhotoSettings = ObjCClass('AVCapturePhotoSettings')

AVCaptureConnection = ObjCClass('AVCaptureConnection')
#AVCaptureVideoOrientation = ObjCClass('AVCaptureVideoOrientation')

AVCaptureVideoOrientationPortrait = 1
AVCaptureVideoOrientationPortraitUpsideDown = 2
AVCaptureVideoOrientationLandscapeRight = 3
AVCaptureVideoOrientationLandscapeLeft = 4

AVCaptureFocusModeLocked = 0
AVCaptureFocusModeAutoFocus = 1
AVCaptureFocusModeContinuousAutoFocus = 2

AVCaptureExposureModeLocked = 0
AVCaptureExposureModeAutoExpose = 1
AVCaptureExposureModeContinuousAutoExposure = 2
AVCaptureExposureModeCustom = 3

AVCaptureWhiteBalanceModeLocked = 0
AVCaptureWhiteBalanceModeAutoWhiteBalance = 1
AVCaptureWhiteBalanceModeContinuousAutoWhiteBalance = 2

AVCaptureTorchModeOff = 0
AVCaptureTorchModeOn = 1
AVCaptureTorchModeAuto = 2

import ctypes
import objc_util

CMTimeValue=ctypes.c_int64
CMTimeScale=ctypes.c_int32
CMTimeFlags=ctypes.c_uint32
CMTimeEpoch=ctypes.c_int64
class CMTime(Structure):
    _fields_=[('value',CMTimeValue),
              ('timescale',CMTimeScale),
              ('flags',CMTimeFlags),
              ('epoch',CMTimeEpoch)]
    def __init__(self,value=0,timescale=1,flags=0,epoch=0):
        self.value=value
        self.timescale=timescale
        self.flags=flags
        self.epoch=epoch
c.CMTimeMakeWithSeconds.argtypes=[ctypes.c_double,ctypes.c_int32]
c.CMTimeMakeWithSeconds.restype=CMTime
c.CMTimeGetSeconds.argtypes=[CMTime]
c.CMTimeGetSeconds.restype=c_double

class AVCaptureWhiteBalanceTemperatureAndTintValues(Structure):
    _fields_=[('temperature',  ctypes.c_float),  # values must be between 1.0 and maxWhiteBalanceGain
              ('tint', ctypes.c_float)]
    def __init__(self,temperature=6000.0,tint=0.0):
        self.temperature=temperature
        self.tint = tint

class CAVCaptureWhiteBalanceGain(Structure):
    _fields_=[('blueGain',  ctypes.c_float),  # values must be between 1.0 and maxWhiteBalanceGain
              ('greenGain', ctypes.c_float),
              ('redGains',  ctypes.c_float)]
    def __init__(self,blueGain=1.0,greenGain=1.0,redGain=1.0):
        self.blueGain=blueGain
        self.greenGain=greenGain
        self.redGain=redGain

# 画像ファイルをアルバムに追加する
def addImagefileToAlbum( imagefilePath, albumName ):
    try:
        album = [a for a in photos.get_albums() if a.title == albumName][0]
    except IndexError:
        album = photos.create_album( albumName )
    asset = photos.create_image_asset( imagefilePath )
    album.add_assets([asset])

# マニュアル撮影関数
def manualCapture(orientation,
                  exposureMode, exposureValue, exposureScale, iso, # 23-736?
                  focusMode, focusDistance,
                  temperatureAndTint, torch, fileName, albumName):

    def captureOutput_didFinishProcessingPhotoSampleBuffer_previewPhotoSampleBuffer_resolvedSettings_bracketSettings_error_(
             _self, _cmd, _output, _photoBuffer, _previewBuffer, _resolveSettings, bracketSettings, _error ):
        photoBuffer = ObjCInstance(_photoBuffer)
        # JPEG画像の取得
        jpegPhotoData = AVCapturePhotoOutput.JPEGPhotoDataRepresentationForJPEGSampleBuffer_previewPhotoSampleBuffer_(
                            photoBuffer, _previewBuffer )
        # ファイル保存
        jpegPhotoData.writeToFile_atomically_(fileName, True )
        addImagefileToAlbum( fileName, albumName )
        event.set()
    
    # delegate
    CameraManualPhotoCaptureDelegate = create_objc_class(
        'CameraManualPhotoCaptureDelegate',
        methods=[ captureOutput_didFinishProcessingPhotoSampleBuffer_previewPhotoSampleBuffer_resolvedSettings_bracketSettings_error_ ],
            protocols=[ 'AVCapturePhotoCaptureDelegate' ])
    # セッション開始
    session = AVCaptureSession.alloc().init()
    device = AVCaptureDevice.defaultDeviceWithMediaType_('vide')
    _input = AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)
    if _input:
        session.addInput_(_input)
    else:
        return
    session.startRunning()
    output = AVCapturePhotoOutput.alloc().init()
    session.addOutput_(output)

    # settings
    settings = AVCapturePhotoSettings.photoSettings()
    settings.AVCaptureFocusMode = focusMode
    
    # デバイス設定
    device.lockForConfiguration_(None)
    # exposureMode lock/unlock
    if exposureMode and device.isExposureModeSupported_(exposureMode):
        device.exposureMode = exposureMode
    # exposureDuration and iso
    if exposureValue and exposureScale and iso:
        device.setExposureModeCustomWithDuration_ISO_completionHandler_((CMTime(exposureValue, exposureScale,1,0)),(iso), None,restype=None,argtypes=[ CMTime, c_float, c_void_p])
    # focus distance and mode
    if focusDistance and focusMode == AVCaptureFocusModeLocked:
        device.setFocusModeLockedWithLensPosition_completionHandler_(focusDistance, None)
    # focus distance and mode
    if torch:
        device.setTorchModeOnWithLevel_error_(torch[1], None)
        device.torchMode = torch[0]
    # whitealance
    if temperatureAndTint:
        device.whiteBalanceMode = AVCaptureWhiteBalanceModeLocked
        AVCaptureWhiteBalanceTemperatureAndTintValues
        device.deviceWhiteBalanceGainsForTemperatureAndTintValues_(
            (AVCaptureWhiteBalanceTemperatureAndTintValues(temperatureAndTint[0], temperatureAndTint[1])),
            restype=None,argtypes=[AVCaptureWhiteBalanceTemperatureAndTintValues]
        )
    device.unlockForConfiguration()
    time.sleep(0.2)

    # connection
    connection = output.connectionWithMediaType_('vide')
    connection.videoOrientation = orientation
    # 撮影開始
    event = threading.Event()
    delegate = CameraManualPhotoCaptureDelegate.new()
    retain_global(delegate)
    output.capturePhotoWithSettings_delegate_(settings, delegate) # capture
    session.stopRunning()
    session.release()
    output.release()

