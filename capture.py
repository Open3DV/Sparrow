# -*- coding: utf-8 -*-
import glob
import msvcrt
import os
import time

import gxipy as gx
from PIL import Image
from gxipy import RawImage
from reconstruct import reconstruct

cam=0

def LINE0_IN():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE0)
    cam.LineMode.set(gx.GxLineModeEntry.INPUT)


def LINE1_OUT():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE1)
    cam.LineMode.set(gx.GxLineModeEntry.OUTPUT)

    # cam.LineInverter.set(True)


def SDA_OUTPUT():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE2)
    cam.LineMode.set(gx.GxLineModeEntry.OUTPUT)
    cam.LineInverter.set(False)


def SDA_ON():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE2)
    cam.LineMode.set(gx.GxLineModeEntry.OUTPUT)
    cam.LineInverter.set(False)


def SDA_OFF():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE2)
    cam.LineMode.set(gx.GxLineModeEntry.OUTPUT)
    cam.LineInverter.set(True)


def SDA_INPUT():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE2)
    cam.LineMode.set(gx.GxLineModeEntry.INPUT)
    cam.LineInverter.set(False)


def SDA_READ():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE2)
    cam.LineMode.set(gx.GxLineModeEntry.INPUT)
    return cam.LineStatus.get()


def SCL_OUTPUT():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE3)
    cam.LineMode.set(gx.GxLineModeEntry.OUTPUT)
    cam.LineInverter.set(False)


def SCL_ON():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE3)
    cam.LineMode.set(gx.GxLineModeEntry.OUTPUT)
    cam.LineInverter.set(False)


def SCL_OFF():
    cam.LineSelector.set(gx.GxLineSelectorEntry.LINE3)
    cam.LineMode.set(gx.GxLineModeEntry.OUTPUT)
    cam.LineInverter.set(True)


def TestGpioSda():
    icnt = 0
    while True:
        SDA_ON()
        time.sleep(1 / 1000)

        SDA_OFF()
        time.sleep(1 / 1000)
        icnt += 1
        if icnt >= 1000:
            break


def TestGpioScl():
    icnt = 0
    while True:
        SCL_ON()
        time.sleep(1 / 1000)

        SCL_OFF()
        time.sleep(1 / 1000)
        icnt += 1
        if icnt >= 1000:
            break


def iic_read(inner_reg, buffer, buffer_size):
    ack = 0
    inner_addr = 0x1b
    SDA_OUTPUT()
    SDA_ON()
    SCL_ON()
    SDA_OFF()
    SCL_OFF()

    ch = (inner_addr << 1)
    for j in range(0, 8):
        if (ch & 0x80):
            SDA_ON()
        else:
            SDA_OFF()
        SCL_ON()
        SCL_OFF()
        ch <<= 1
    SDA_ON()
    SDA_INPUT()
    SCL_ON()
    ack = SDA_READ()
    SCL_OFF()
    if (ack):
        print("no ack")
    SDA_OUTPUT()

    ch = inner_reg
    SDA_OUTPUT()

    for j in range(0, 8):
        if (ch & 0x80):
            SDA_ON()
        else:
            SDA_OFF()
        SCL_ON()
        SCL_OFF()
        ch <<= 1
    SDA_ON()
    SDA_INPUT()
    SCL_ON()
    ack = SDA_READ()
    SCL_OFF()
    if (ack):
        print("no ack")
    SDA_OUTPUT()
    SCL_OFF()
    SDA_OFF()

    SCL_ON()
    SDA_ON()

    SDA_OFF()
    SCL_OFF()

    ch = (inner_addr << 1) | 0x01

    for j in range(0, 8):
        if (ch & 0x80):
            SDA_ON()
        else:
            SDA_OFF()
        SCL_ON()
        SCL_OFF()
        ch <<= 1
    SDA_ON()
    SDA_INPUT()
    SCL_ON()
    ack = SDA_READ()
    SCL_OFF()
    if (ack):
        print("no ack")
    for i in range(buffer_size):
        ch = 0
        SDA_INPUT()
        for j in range(0, 8):
            ch <<= 1
            if (SDA_READ()):
                ch |= 0x01
            SCL_ON()
            SCL_OFF()
        SDA_OUTPUT()
        SCL_ON()
        SDA_OFF()
        SCL_OFF()
        buffer[i] = (ch & 0xff)
        print("ch:", ch)
    SCL_ON()
    SDA_ON()
    return 0


def iic_write(inner_reg, buffer, buffer_size):
    ack = 0
    inner_addr = 0x1b
    SDA_OUTPUT()
    SDA_ON()
    SCL_ON()
    SDA_OFF()
    SCL_OFF()
    ch = (inner_addr << 1)
    for j in range(0, 8):
        if (ch & 0x80):
            SDA_ON()
        else:
            SDA_OFF()
        SCL_ON()
        SCL_OFF()
        ch <<= 1
    SDA_ON()
    SDA_INPUT()
    SCL_ON()
    ack = SDA_READ()
    SCL_OFF()
    if (ack):
        print("no ack")
    SDA_OUTPUT()

    ch = inner_reg
    for j in range(0, 8):
        if (ch & 0x80):
            SDA_ON()
        else:
            SDA_OFF()
        SCL_ON()
        SCL_OFF()
        ch <<= 1
    SDA_ON()
    SDA_INPUT()
    SCL_ON()
    ack = SDA_READ()
    SCL_OFF()
    if (ack):
        print("no ack")
    SDA_OUTPUT()

    for i in range(buffer_size):
        ch = buffer[i]
        SDA_OUTPUT()
        for j in range(0, 8):
            if (ch & 0x80):
                SDA_ON()
            else:
                SDA_OFF()
            SCL_ON()
            SCL_OFF()
            ch <<= 1
        SDA_ON()
        SDA_INPUT()
        SCL_ON()
        ack = SDA_READ()
        SCL_OFF()
        if (ack):
            print("no ack")
    SDA_OUTPUT()
    SCL_OFF()
    SDA_OFF()
    SCL_ON()
    SDA_ON()
    return 0


def Light_Ctrl():
    print("???FW????:")
    rbuf = bytearray(30)
    iic_read(0xd4, rbuf, 1)

    sbuf1 = [
        [0x04],
        [0x00, 0x00, 0x00, 0x00],
    ]

    iic_write(0x05, sbuf1[0], 1)
    iic_write(0x9e, sbuf1[1], 2)
    # iic_read(0x06, rbuf, 1)
    # iic_read(0x06, rbuf, 1)


def Gpio_Trigger_photo():
    LINE1_OUT(1)
    time.sleep(1)
    LINE1_OUT(0)
    time.sleep(1)



def capture():

    # --------------------初始化模块---------------------
    gx.gx_init_lib()

    file_list = glob.glob("*.bmp")
    for file_path in file_list:
        os.remove(file_path)

    time.sleep(1)

   # --------------------获取设备列表---------------------
    device_manager = gx.DeviceManager()
    dev_num, dev_info_list = device_manager.update_all_device_list(1000)
    print(dev_info_list)
    for dev in dev_info_list:
        print("dev : ", dev)
    if dev_info_list == 0:
        print("no device found")
        exit(0)
    print(dev_info_list)
    print("Camera :", dev_info_list[0].get("model_name"))
    print("sn  :", dev_info_list[0].get("sn"))
    print("device_class :", dev_info_list[0].get("device_class"))

    # --------------------打开设备---------------------
    global cam
    cam = device_manager.open_device_by_index(dev_info_list[0].get("index"))
    if cam == 0:
        print("open device error")
        exit(0)

    # --------------------设置帧模式---------------------

    cam.AcquisitionMode.set(2)
    cam.AcquisitionFrameRate.set(40)
    cam.AcquisitionFrameRateMode.set(gx.GxSwitchEntry.OFF)

    print("AcquisitionMode : ", cam.AcquisitionMode.get())
    print("AcquisitionFrameRate : ", cam.AcquisitionFrameRate.get())
    print("AcquisitionFrameRateMode : ", cam.AcquisitionFrameRateMode.get())
    print("CurrentAcquisitionFrameRate : ", cam.CurrentAcquisitionFrameRate.get())

    # --------------------设置触发模式---------------------
    LINE0_IN()
    cam.TriggerMode.set(True)
    cam.TriggerSource.set(gx.GxTriggerSourceEntry.LINE0)
    cam.TriggerSelector.set(gx.GxTriggerSelectorEntry.FRAME_START)
    cam.TriggerActivation.set(gx.GxTriggerActivationEntry.FALLINGEDGE)
    cam.TimerTriggerSource.set(gx.GxTimerTriggerSourceEntry.EXPOSURE_START)

    print("TriggerMode : ", cam.TriggerMode.get())
    print("TriggerSource : ", cam.TriggerSource.get())
    print("TriggerSelector : ", cam.TriggerSelector.get())
    print("TriggerActivation : ", cam.TriggerActivation.get())

    # --------------------设置曝光时间---------------------

    # cam.ExposureMode.set(gx.GxExposureModeEntry.TRIGGER_WIDTH)
    cam.ExposureTime.set(3000)
    cam.ExposureDelay.set(0)
    print("ExposureTime : ", cam.ExposureTime.get())
    print("ExposureDelay : ", cam.ExposureDelay.get())

    # --------------------设置触发输出接口---------------------
    LINE1_OUT()
    cam.LineSource.set(gx.GxUserOutputModeEntry.STROBE)

    # cam.UserOutputValue.set(True)

    # --------------------相机拍照---------------------
    folder_count = 0

    #for folder_count in range(0, 26):
    cam.stream_on()
    Light_Ctrl()
    for cnt in range(0, 37):
        raw_image = cam.data_stream[0].get_image(1000)
        # w = raw_image.get_width()
        # h = raw_image.get_height()
        # print("Image : (", w, "x", h, ")")
        while True:
            if raw_image.get_status() == gx.GxFrameStatusList.SUCCESS:
                break
        # --------------------保存图片---------------------
        numpy_image = RawImage.get_numpy_array(raw_image)
        cimg = Image.fromarray(numpy_image)
        print("photo : phase%02d.bmp" % cnt)
        # cimg.save("D:/3d_camera/test/dev/xema/x64/Release/capture0/raw25/phase%02d.bmp" % cnt)
        # 检查目标文件夹是否存在，如果不存在则创建
        # cimg.folder = "./raw28"
        cimg.folder = "capture"
        if not os.path.exists(cimg.folder):
            os.makedirs(cimg.folder)
        cimg.save(cimg.folder + "/phase%02d.bmp" % cnt)

    # 等待拍照完成后再递增计数器
    input("Press Enter to continue...")
    folder_count += 1

    # --------------------GPIO 测试--------------------
    # TestGpioSda()
    # TestGpioScl()
    # --------------------光机控制---------------------

    # --------------------GPIO TRIGGER---------------------

    # Gpio_Trigger_photo()
    # --------------------关闭设备---------------------
    cam.stream_off()
    cam.close_device()

    # --------------------显示图片---------------------
    # image.show()
    # --------------------结束---------------------

if __name__ == "__main__":
    capture()
    reconstruct('param.txt', 'capture', 'point_cloud.xyz')
