import time
import cv2
from threading import Thread
import numpy as np
from sympy import Point2D, Line, Ray
import math
import pygame
from pygame.locals import *
from sys import exit
import pandas as pd
import sys


class ArucoController(Thread):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    SHADOW = (160, 192, 160)
    LIGHTGREEN = (0, 255, 0)
    LIGHTBLUE = (0, 0, 255)
    LIGHTRED = (255, 100, 100)
    PURPLE = (102, 0, 102)
    LIGHTPURPLE = (153, 0, 153)
    BLACK = (0, 0, 0)

    gui_goal_x = [170, 405, 405, 170]
    gui_goal_y = [360, 360, 90, 90]
    gui_goal_x_1 = [288, 288]
    gui_goal_y_1 = [90, 360]

    def __init__(self, gui_enable):
        Thread.__init__(self)
        self.name = "aruco"
        self.delay = 0.01
        self.gui_enable = gui_enable
        self.maxRobotNum = 9
        self.RobotPOS = np.zeros((self.maxRobotNum, 3), dtype=float)

    def run(self):

        camera_id = 1
        aruco_dict_type = cv2.aruco.DICT_4X4_50
        calibration_matrix_path = "Camera/calibration_matrix.npy"
        distortion_coefficients_path = "Camera/distortion_coefficients.npy"

        k = np.load(calibration_matrix_path)
        d = np.load(distortion_coefficients_path)

        video = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        video.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
        video.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)

        if self.gui_enable == True:

            Width = 1024
            Height = 768

            # Width = 640
            # Height = 480

            pygame.init()
            pygame.display.set_caption('多机器人编队控制实验平台')
            screen = pygame.display.set_mode((Width, Height), 0, 32)
            screen.fill([0, 0, 0])

        while True:
            ret, frame = video.read()

            if ret == False:
                break

            output = self.pose_esitmation(frame, aruco_dict_type, k, d)  # 计算输出每个标签的位置

            if self.gui_enable == True:

                frame = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
                frame = cv2.transpose(frame)
                frame = pygame.surfarray.make_surface(frame)
                screen.blit(frame, (0, 0))

                pygame.draw.circle(screen, self.RED, (320, 240), 5)
                pygame.display.update()

                for event in pygame.event.get():
                    if event.type == QUIT:
                        sys.exit()

            time.sleep(self.delay)

        video.release()
        cv2.destroyAllWindows()

        pygame.quit()
        sys.exit()

    def pose_esitmation(self, frame, aruco_dict_type, matrix_coefficients, distortion_coefficients):
        '''
        frame - Frame from the self.video stream
        matrix_coefficients - Intrinsic matrix of the calibrated camera
        distortion_coefficients - Distortion coefficients associated with your camera
        return:-
        frame - The frame with the axis drawn on it
        '''
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.aruco_dict = cv2.aruco.Dictionary_get(aruco_dict_type)
        parameters = cv2.aruco.DetectorParameters_create()
        # 检测标签
        corners, ids, rejected_img_points = cv2.aruco.detectMarkers(gray, cv2.aruco_dict, parameters=parameters,
                                                                    cameraMatrix=matrix_coefficients,
                                                                    distCoeff=distortion_coefficients)
        font = cv2.FONT_HERSHEY_SIMPLEX
        # 如果检测到了标签
        if len(corners) > 0:

            for i in range(0, len(ids)):
                # 检测标签坐标
                cv2.aruco.estimatePoseSingleMarkers(corners[i], 0.02, matrix_coefficients, distortion_coefficients)

            for i in range(0, len(ids)):

                # 计算中心点坐标
                topLeft = (int(corners[i-1][0][0][0]), int(corners[i-1][0][0][1]))
                topRight = (int(corners[i-1][0][1][0]), int(corners[i-1][0][1][1]))
                bottomRight = (int(corners[i-1][0][2][0]), int(corners[i-1][0][2][1]))
                bottomLeft = (int(corners[i-1][0][3][0]), int(corners[i-1][0][3][1]))

                # 计算中心点坐标
                cx = int((topLeft[0] + bottomRight[0]) / 2.0)
                cy = int((topLeft[1] + bottomRight[1]) / 2.0)
                arrowX = int((topLeft[0] + topRight[0]) / 2.0)
                arrowY = int((topLeft[1] + topRight[1]) / 2.0)

                # 计算机器人航向角
                r1 = Ray((cx, cy), (cx+10, cy))
                r2 = Ray((cx, cy), (arrowX, arrowY))
                yaw = math.degrees(r1.closing_angle(r2).evalf())
                yaw = int(self.constrain_0_360(yaw))

                # 保存到矩阵中
                label_id = ids[i-1][0]
                self.output_data(label_id-1, cx, cy, yaw)

                # 绘制图案
                if self.gui_enable == True:
                    # 绘制方向箭头
                    cv2.line(frame, (cx, cy), (arrowX, arrowY), (0, 0, 255), 4)
                    # 绘制标签边框
                    cv2.line(frame, topLeft, topRight, (0, 255, 0), 1)
                    cv2.line(frame, topRight, bottomRight, (0, 255, 0), 1)
                    cv2.line(frame, bottomRight, bottomLeft, (0, 255, 0), 1)
                    cv2.line(frame, bottomLeft, topLeft, (0, 255, 0), 1)
                    # 绘制中心点
                    cv2.circle(frame, (cx, cy), 1, (0, 255, 0), -1)
                    # 绘制坐标信息
                    # cv2.putText(frame, "ID:" + str(ids[i-1][0]), (int(cx-15), int(cy-40)), font, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(frame, "ID:" + str(ids[i-1][0]), (int(cx-15), int(cy-10)), font, 0.6, (255, 255, 0), 1, cv2.LINE_AA)
                    # cv2.putText(frame, str(cx), (int(cx-65), int(cy-20)), font, 0.6, (255, 0, 255), 2, cv2.LINE_AA)
                    # cv2.putText(frame, "," + str(cy), (int(cx-25), int(cy-20)), font, 0.6, (255, 0, 255), 2, cv2.LINE_AA)
                    # cv2.putText(frame, "," + str(yaw), (int(cx+20), int(cy-20)), font, 0.6, (255, 0, 255), 2, cv2.LINE_AA)
        else:
            cv2.putText(frame, "No Ids", (0, 32), font, 1, (0, 255, 0), 2, cv2.LINE_AA)

        return frame

    def output_data(self, num, x, y, yaw):
        self.RobotPOS[num, :] = [x, y, yaw]

    def constrain_0_360(self, value):
        if value < -180:
            value = value + 360
        if value > 180:
            value = value - 360
        return value


arucoThread = ArucoController(True)
arucoThread.start()
