import time
from Controller_ARUCO import ArucoController
from Controller_ROBOT import RobotController

import scipy.io
data = scipy.io.loadmat('real_run.mat')  # 读取mat文件
# print(data.keys())  # 查看mat文件中的所有变量
matrix_x = data['pose_x']
matrix_y = data['pose_y']

robot_arrya = [
    [1, 0, 0, 0, 0],
    [2, 0, 0, 0, 0],
    [3, 0, 0, 0, 0],
    [4, 0, 0, 0, 0],
    [5, 0, 0, 0, 0],
    [6, 0, 0, 0, 0],
    [7, 0, 0, 0, 0],
    [8, 0, 0, 0, 0],
    [9, 0, 0, 0, 0],
]

# 创建Aruco线程识别标签
arucoThread = ArucoController(True)
arucoThread.start()

time.sleep(5)

# 创建Robot线程控制机器人的移动
robotThread1 = RobotController(1, robot_arrya[0])
robotThread1.start()

robotThread2 = RobotController(2,  robot_arrya[1])
robotThread2.start()

robotThread3 = RobotController(3,  robot_arrya[2])
robotThread3.start()

robotThread4 = RobotController(4,  robot_arrya[3])
robotThread4.start()

point_cnt = 0
loop_cnt = 0
run_sta = 0

qiehuan_cnt = 1
point_All = 300
tar_x = [50, 150, 250, 350, 450, 550]
tar_y = [240, 240, 240, 240, 240, 240]


All_Robot_Num = 4

x_scale = 570/1.2
x_add = 0.0
y_scale = 270/0.6
y_add= 0.175

while(True):

    loop_cnt += 1

    if(run_sta == 0):
        if(loop_cnt >= qiehuan_cnt):
            loop_cnt = 0
            point_cnt += 1
        if(point_cnt == point_All):
            point_cnt = point_All-1
            run_sta = 1
    else:
        if(loop_cnt >= qiehuan_cnt):
            loop_cnt = 0
            point_cnt -= 1
        if(point_cnt == -1):
            point_cnt = 0
            run_sta = 0

    # if(loop_cnt >= 2):
    #     loop_cnt = 0
    #     point_cnt += 1


    for id in range(0, All_Robot_Num):
        pose_real = arucoThread.RobotPOS[id]
        robot_arrya[id][0] = pose_real[0]
        robot_arrya[id][1] = pose_real[1]
        robot_arrya[id][2] = pose_real[2]
        robot_arrya[id][3] = (matrix_x[id][point_cnt]/10+x_add)*x_scale +25
        robot_arrya[id][4] = (-matrix_y[id][point_cnt]/10+y_add)*y_scale +150 
        # robot_arrya[id][3] = tar_x[point_cnt]
        # robot_arrya[id][4] = tar_y[point_cnt]+(id)*30

    # id = 0
    # pose_real = arucoThread.RobotPOS[id]
    # robot_arrya[id][0] = pose_real[0]
    # robot_arrya[id][1] = pose_real[1]
    # robot_arrya[id][2] = pose_real[2]
    # # robot_arrya[id][3] = matrix_x[id][point_cnt]/10
    # # robot_arrya[id][4] = matrix_y[id][point_cnt]/10
    # # robot_arrya[id][3] = 320
    # # robot_arrya[id][4] = 240
    # robot_arrya[id][3] = tar_x[point_cnt]
    # robot_arrya[id][4] = tar_y[point_cnt]

    time.sleep(0.1)
