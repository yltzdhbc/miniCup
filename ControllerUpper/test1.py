import scipy.io
data = scipy.io.loadmat('mpc1.mat')  # 读取mat文件
print(data.keys())  # 查看mat文件中的所有变量
print(data['pose_x'])
print(data['pose_y'])
matrix_x = data['pose_x']
matrix_y = data['pose_y']

robot_id = 2
cnt = 0

print(matrix_x[robot_id-1][cnt])
print(matrix_y[robot_id-1][cnt])



# robot_arrya = [
#     [1, 0, 0, 0, 0],
#     [2, 0, 0, 0, 0],
#     [3, 0, 0, 0, 0],
#     [4, 0, 0, 0, 0],
#     [5, 0, 0, 0, 0],
#     [6, 0, 0, 0, 0],
#     [7, 0, 0, 0, 0],
#     [8, 0, 0, 0, 0],
#     [9, 0, 0, 0, 0],
# ]

# print(robot_arrya[0])

# print(robot_arrya[0][0])
# print(robot_arrya[0][1])