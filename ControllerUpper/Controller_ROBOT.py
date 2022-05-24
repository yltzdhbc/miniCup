from threading import Thread
import time
import os

from sympy import Point2D, Line, Ray
import math
import time
import numpy as np
import pandas as pd
import socket
from simple_pid import PID

DEBUG_PRINT = 0


class RobotPIDController:

    pid_throttle_controller = PID(5, 0, 0, setpoint=0)
    pid_throttle_controller.output_limits = (0, 1023)
    pid_steering_controller = PID(12, 0, 0, setpoint=0)
    pid_steering_controller.output_limits = (-1023, 1023)

    def __init__(self, Thr, Steer):
        self.Thr = Thr
        self.Steer = Steer

    def Output_left_wheel(self):
        clipped_left = float(np.clip((self.Thr - self.Steer), -1023, 1023))
        return np.round(clipped_left, -2)

    def Output_right_wheel(self):
        clipped_right = float(np.clip((self.Thr + self.Steer), -1023, 1023))
        return np.round(clipped_right, -2)


class RobotController(Thread):

    def __init__(self, robotID, *ptr):
        Thread.__init__(self)      # 调用父类的初始化方法
        self.robotID = robotID
        self.recv_all = ptr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)     # For UDP
        # 从机器人地址
        self.udp_host = "192.168.0.13" + str(self.robotID)
        self.udp_port = 2801
        print('target robot id: '+str(self.udp_host))
        self.ROBOT = RobotPIDController(0, 0)

    def run(self):

        spin_mode = False
        left_speed = 0
        right_speed = 0

        while True:

            #结构其他线程传进来的机器人位置和目标点
            bot_x, bot_y, bot_yaw, goal_x, goal_y = self.parse_pos()

            if(DEBUG_PRINT):
                print("robot id: "+str(self.robotID)+"----------")
                print("bot_x: "+str(bot_x)+", "+"bot_y: "+str(bot_y)+", "+"bot_yaw: "+str(bot_yaw))
                print("goal_x: "+str(goal_x)+", "+"goal_y: "+str(goal_y))

            # 计算反馈位置与目标点之间的距离误差
            Bot_Loc = Point2D(bot_x, bot_y)
            Goal_Loc = Point2D(goal_x, goal_y)
            distance_error = (Bot_Loc.distance(Goal_Loc)).evalf()
            if(DEBUG_PRINT):
                print("dist_error: "+str(distance_error))

            # 计算反馈角度与目标之间的角度误差
            r1 = Ray((bot_x, bot_y), (bot_x+10, bot_y))
            r2 = Ray((bot_x, bot_y), (goal_x, goal_y))
            angle_to_goal = math.degrees(r1.closing_angle(r2).evalf())
            angle_to_goal = self.constrain_0_360(angle_to_goal)
            angle_error = (bot_yaw - angle_to_goal)
            angle_error = self.constrain_0_360(angle_error)
            if(DEBUG_PRINT):
                print("angle_to_goal: "+str(angle_to_goal))
                print("angle_error: "+str(angle_error))

            # 如果误差角度大于了60度，则原地旋转
            if abs(angle_error) > 60 or spin_mode == True:
                spin_mode = True
                if abs(angle_error) >= 35:
                    spin_speed = int(np.interp(abs(angle_error), [35, 180], [400, 500]))
                    if angle_error > 0:
                        left_speed = spin_speed
                        right_speed = -spin_speed
                    else:
                        left_speed = -spin_speed
                        right_speed = spin_speed
                    if(DEBUG_PRINT):
                        print("模式： 原地旋转")
                else:
                    spin_mode = False

            # 误差角度小于60度，则进入点跟踪模式
            if spin_mode == False:
                # 在接近目标点的时候切换为精确的控制模式
                if(distance_error > 20 and distance_error <= 100):
                    left_speed = 600 + 3*angle_error
                    right_speed = 600 - 3*angle_error
                    if(DEBUG_PRINT):
                        print("模式： 精确控制")
                # 接近目标点 停止
                elif (distance_error <= 20):
                    left_speed = 0
                    right_speed = 0
                    if(DEBUG_PRINT):
                        print("模式： 到达目标")
                # 在正常运行中
                else:
                    # 根据误差计算PID值
                    self.ROBOT.Steer = self.ROBOT.pid_steering_controller(angle_error)
                    self.ROBOT.Thr = self.ROBOT.pid_throttle_controller(-distance_error)
                    left_speed = self.ROBOT.Output_left_wheel()
                    right_speed = self.ROBOT.Output_right_wheel()
                    if(DEBUG_PRINT):
                        print("模式： 误差跟踪阶段")

            # 通过UDP发送报文
            msg = self.package_msg(left_speed, right_speed)
            self.sock.sendto(msg.encode(), (self.udp_host, self.udp_port))
            if(DEBUG_PRINT):
                print('message: '+str(msg))

            time.sleep(0.5)

    def package_msg(self, leftSpeed, rightSpeed):
        temp = [0, 0]
        # package = str(int(rightSpeed/10)) + "," + str(int(leftSpeed/10)) + "," + str(int(temp[0])) + "," + str(int(temp[1])) + ","
        package = str(int(leftSpeed/10)) + "," + str(int(rightSpeed/10)) + "," + str(int(temp[0])) + "," + str(int(temp[1]))
        # package = str(int(rightSpeed/10)) + "," + str(int(leftSpeed/10)) + "," + str(int(temp[0])) + "," + str(int(temp[1]))
        return package

    def parse_pos(self):
        recv = self.recv_all[0]
        bot_x = recv[0]
        bot_y = recv[1]
        bot_yaw = recv[2]
        goal_x = recv[3]
        goal_y = recv[4]
        return bot_x, bot_y, bot_yaw, goal_x, goal_y

    def constrain_0_360(self, value):
        if value < -180:
            value = value + 360
        if value > 180:
            value = value - 360
        return value


# robotThread1 = RobotController(1)
# robotThread1.start()
