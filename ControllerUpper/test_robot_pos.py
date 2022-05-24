import time
from Controller_ARUCO import ArucoController

# 创建Aruco线程识别标签
arucoThread = ArucoController(True)
arucoThread.start()

while(True):
    print(arucoThread.RobotPOS)
    time.sleep(1)
