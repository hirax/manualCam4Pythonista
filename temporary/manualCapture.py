# coding: utf-8
# Copyright (c) 2018 Jun Hirabayashi (jun@hirax.net)
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

from objc_util import *
from ctypes import c_void_p, cast
import ui, time, photos, threading
import os
import numpy as np

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

CVPixelBufferLockBaseAddress = c.CVPixelBufferLockBaseAddress
CVPixelBufferLockBaseAddress.argtypes = [c_void_p, c_int]
CVPixelBufferLockBaseAddress.restype = None

CVPixelBufferUnlockBaseAddress = c.CVPixelBufferUnlockBaseAddress
CVPixelBufferUnlockBaseAddress.argtypes = [c_void_p, c_int]
CVPixelBufferUnlockBaseAddress.restype = None

CVPixelBufferGetWidthOfPlane = c.CVPixelBufferGetWidthOfPlane
CVPixelBufferGetWidthOfPlane.argtypes = [c_void_p, c_int]
CVPixelBufferGetWidthOfPlane.restype = c_int

CVPixelBufferGetHeightOfPlane = c.CVPixelBufferGetHeightOfPlane
CVPixelBufferGetHeightOfPlane.argtypes = [c_void_p, c_int]
CVPixelBufferGetHeightOfPlane.restype = c_int

CVPixelBufferGetBaseAddressOfPlane = c.CVPixelBufferGetBaseAddressOfPlane
CVPixelBufferGetBaseAddressOfPlane.argtypes = [c_void_p, c_int]
CVPixelBufferGetBaseAddressOfPlane.restype = c_void_p

CVPixelBufferGetBytesPerRowOfPlane = c.CVPixelBufferGetBytesPerRowOfPlane
CVPixelBufferGetBytesPerRowOfPlane.argtypes = [c_void_p, c_int]
CVPixelBufferGetBytesPerRowOfPlane.restype = c_int

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

# ===================  マニュアル撮影関数 ===================
def manualCapture(
      orientation,
      exposureMode, # AVCaptureExposureModeLocked/AVCaptureExposureModeAutoExpose/AVCaptureExposureModeContinuousAutoExposure/AVCaptureExposureModeCustom
      # The maximum exposure time: iPhone 6 is 1/2 second, 1/3 on iPhone 6s
                  # 1/15, 1/25, 1/45, 1/90, 1/190, 1/380
      exposureValue, exposureScale,  # value/scale (seconds) (CMTimeValue:value = Int62, CMTimeScale:scale = Int32)
      iso,           # min 23 - max 736
      focusMode,     # AVCaptureFocusModeLocked/AVCaptureFocusModeAutoFocus/AVCaptureFocusModeContinuousAutoFocus
      focusDistance, # 0.0 - 1.0
      temperatureAndTint,  # [temprature(kelvin), tint=white balance(-150.0 to +150.0)] ex.[6000.0, 0.0]
      torch,         # [AVCaptureTorchModeOff/AVCaptureTorchModeOn/AVCaptureTorchModeAuto, level(0.0-1.0)]
      fileName,      # fileName used in saving
      albumName,     # album name. if None, image isn't stored to album
      imageFormat,   # '.JPG', '.DNG'
      isSaveNPY ):   # True, False
    
    def processPixelBuffer(pixelData, fileName):
        # https://qiita.com/pashango2/items/5075cb2d9248c7d3b5d4
        base_address  = CVPixelBufferGetBaseAddressOfPlane(pixelData, 0)
        bytes_per_row = CVPixelBufferGetBytesPerRowOfPlane(pixelData, 0)
        width = CVPixelBufferGetWidthOfPlane(pixelData, 0)
        height = CVPixelBufferGetHeightOfPlane(pixelData, 0)
        data = np.ctypeslib.as_array(cast(base_address, POINTER(c_ushort)), shape=((height, width)))
        r = data[::2, ::2]; g = (data[1::2, ::2] + data[::2, 1::2])/2; b = data[1::2, 1::2];
        np.savez(fileName+'.npz', r=r, g=g, b=b)

    # .......... delegate method(共通) ..........
    def captureOutput_didFinishProcessingPhoto_error_(_self, _cmd, _output, _photoBuffer, _error):
        # バッファ, 画像取得, ファイル保存
        photoBuffer = ObjCInstance(_photoBuffer)
        if not photoBuffer:
            return
        # file save
        fileData = photoBuffer.fileDataRepresentation()
        if not fileData:
            print('we have no fileDataRepresentation for '+ fileName)
            return
        fileData.writeToFile_atomically_(fileName, True)
        if albumName:
            addImagefileToAlbum(fileName, albumName)
            os.remove(fileName) # アルバム登録時はカレントディレクトリのファイルは削除する
        # raw 画像処理
        if '.DNG'==imageFormat and isSaveNPY:
            _pixelData = photoBuffer.pixelBuffer()
            if not _pixelData:
                return
            CVPixelBufferLockBaseAddress(_pixelData,0)
            processPixelBuffer(_pixelData, fileName)
            CVPixelBufferUnlockBaseAddress(_pixelData,0)
        event.set()

    # ....... delegate 登録 .......
    CameraManualPhotoCaptureDelegate = create_objc_class('CameraManualPhotoCaptureDelegate', methods = [captureOutput_didFinishProcessingPhoto_error_], protocols=['AVCapturePhotoCaptureDelegate'])
    # .......　デバイス設定 .......
    device = AVCaptureDevice.defaultDeviceWithMediaType_('vide')
    device.lockForConfiguration_(None)
    # exposureMode lock/unlock
    if exposureMode and device.isExposureModeSupported_(exposureMode):
        device.exposureMode = exposureMode
    # exposureDuration and iso
    if exposureValue and exposureScale and iso:
        device.setExposureModeCustomWithDuration_ISO_completionHandler_( (CMTime(exposureValue, exposureScale,1,0)), iso, None, restype=None, argtypes=[CMTime, c_float, c_void_p] )
    while(not device.isAdjustingExposure): # 設定を待つ
        time.sleep(0.1)
    print(device.ISO())
    durationTime = device.exposureDuration()
    #focus distance and mode  ( 0.0 - 1.0 )
    if focusDistance and focusMode == AVCaptureFocusModeLocked:
        device.setFocusModeLockedWithLensPosition_completionHandler_(focusDistance, None)
    # focus distance and mode
    if AVCaptureTorchModeOff != torch[0] and device.hasTorch():
        device.torchMode = torch[0]
        device.setTorchModeOnWithLevel_error_(torch[1], None)
    # whitealance
    if temperatureAndTint:
        device.whiteBalanceMode = AVCaptureWhiteBalanceModeLocked
        AVCaptureWhiteBalanceTemperatureAndTintValues
        device.deviceWhiteBalanceGainsForTemperatureAndTintValues_(
            (AVCaptureWhiteBalanceTemperatureAndTintValues(temperatureAndTint[0], temperatureAndTint[1])),
            restype=None,argtypes=[AVCaptureWhiteBalanceTemperatureAndTintValues])
    device.unlockForConfiguration()
    time.sleep(0.2)

    # ....... create input, output, and session .......
    _input = AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)
    photoOutput = AVCapturePhotoOutput.alloc().init()
    time.sleep(0.2)

    # セッション
    session = AVCaptureSession.alloc().init()
    session.beginConfiguration()
    session.sessionPreset = 'AVCaptureSessionPresetPhoto'
    if _input:
        session.addInput_(_input)
    else:
        print('Failed to get AVCaptureDeviceInput.')
        return
    if photoOutput:
        session.addOutput_(photoOutput)
    else:
        print('Failed to get AVCapturePhotoOutput.')
        return
    session.commitConfiguration()
    session.startRunning()
    time.sleep(0.2)
    # connection (portrat/landscape交換のため）
    video_connection = None
    for connection in photoOutput.connections():
        for port in connection.inputPorts():
            if str(port.mediaType()) == 'vide':
                video_connection = connection
                break
        if video_connection:
            break
    if video_connection:
        video_connection.videoOrientation = orientation
    else:
        print("No video_connection")
    availableRawPhotoPixelFormatTypes = photoOutput.availableRawPhotoPixelFormatTypes()
    availableRawPhotoPixelFormatType = int('{}'.format(availableRawPhotoPixelFormatTypes[0]))
    # ..... ここから Debug 用 ....
    availableRawPhotoPixelFormatTypes = photoOutput.availablePhotoFileTypes()  # JPG, TIF
    availableRawPhotoPixelFormatTypes = photoOutput.availableRawPhotoFileTypes()  # ("com.adobe.raw-image")
    # ..... ここまで Debug 用 ....

    # settings
    settings = None
    if imageFormat == '.DNG': # bayer_RGGB14 1919379252
        settings = AVCapturePhotoSettings.photoSettingsWithRawPixelFormatType(availableRawPhotoPixelFormatType)
    if imageFormat == '.JPG':
        settings = AVCapturePhotoSettings.photoSettings()
    # settings.isHighResolutionPhotoEnabled = 0
    settings.AVCaptureFocusMode = focusMode # フォーカスモード
    time.sleep(0.2)
    
    event = threading.Event()
    delegate = CameraManualPhotoCaptureDelegate.new()
    retain_global(delegate)
    # --- capture ---
    photoOutput.capturePhotoWithSettings_delegate_(settings, delegate)
    session.stopRunning()
    session.release()
    photoOutput.release()
