import time
from Controller_ARUCO import ArucoController
from Controller_ROBOT import RobotController


robot1_control = 0
robot1_target = [0, 0]

# 创建Aruco线程识别标签
arucoThread = ArucoController(True)
arucoThread.start()


robot1_control = [arucoThread.RobotPOS, robot1_target]

print(robot1_control)


# 创建Robot线程控制机器人的移动
# robotThread1 = RobotController(1, robot1_control)
# robotThread1.start()

# robotThread1 = RobotController(2, arucoThread.RobotPOS)
# robotThread1.start()

count = 0

robot_id = 0

while(True):

    All_Robot_Pos = arucoThread.RobotPOS[0]
    print(All_Robot_Pos)
    pos_arrya = All_Robot_Pos[0]
    print(pos_arrya)
    pos_1 = pos_arrya[0, :]

    print(pos_1)

    count += 1
    # robot1_target = [count,count]
    # robot1_control = [arucoThread.RobotPOS, robot1_target]
    time.sleep(1000)
