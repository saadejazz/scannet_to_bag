import os
import cv2
import numpy as np
import rosbag
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import TransformStamped
import tf
from cv_bridge import CvBridge
import rospy

def load_intrinsics(file_path):
    with open(file_path, 'r') as f:
        intrinsics = np.loadtxt(f)
        width = 640
        height = 480
    return intrinsics, width, height

def create_camera_info(intrinsics, width, height):
    K = np.array(intrinsics).reshape(4, 4)[:3, :3]
    camera_info = CameraInfo()
    camera_info.width = width
    camera_info.height = height
    camera_info.K = K.flatten().tolist()
    camera_info.P = np.hstack((K, np.zeros((3, 1)))).flatten().tolist()
    return camera_info

def create_image_msg(cv_image, encoding, timestamp):
    bridge = CvBridge()
    image_msg = bridge.cv2_to_imgmsg(cv_image, encoding)
    image_msg.header.stamp = timestamp
    return image_msg

def create_transform_msg(pose, timestamp):
    transform = TransformStamped()
    transform.header.stamp = timestamp
    transform.transform.translation.x = pose[0, 3]
    transform.transform.translation.y = pose[1, 3]
    transform.transform.translation.z = pose[2, 3]
    rotation = tf.transformations.quaternion_from_matrix(pose)
    transform.transform.rotation.x = rotation[0]
    transform.transform.rotation.y = rotation[1]
    transform.transform.rotation.z = rotation[2]
    transform.transform.rotation.w = rotation[3]
    return transform

def convert_to_rosbag(folder_path, output_bag_path):
    color_folder = os.path.join(folder_path, 'color')
    depth_folder = os.path.join(folder_path, 'depth')
    pose_folder = os.path.join(folder_path, 'pose')
    intrinsics_file = os.path.join(folder_path, 'intrinsic', 'intrinsic_depth.txt')

    intrinsics, width, height = load_intrinsics(intrinsics_file)
    camera_info_msg = create_camera_info(intrinsics, width, height)

    bag = rosbag.Bag(output_bag_path, 'w')

    tum_gt_file = open(os.path.join("gt", f'{folder_path}.txt'), 'w')

    for filename in sorted(os.listdir(color_folder)):
        if filename.endswith('.jpg'):
            timestamp_str = os.path.splitext(filename)[0]
            timestamp = rospy.Time.from_sec(float(timestamp_str) / 1e6)

            color_image = cv2.imread(os.path.join(color_folder, filename))
            depth_image = cv2.imread(os.path.join(depth_folder, timestamp_str + '.png'), cv2.IMREAD_UNCHANGED)
            pose = np.loadtxt(os.path.join(pose_folder, timestamp_str + '.txt'))

            color_msg = create_image_msg(color_image, 'bgr8', timestamp)
            depth_msg = create_image_msg(depth_image, '16UC1', timestamp)
            pose_msg = create_transform_msg(pose, timestamp)

            camera_info_msg.header.stamp = timestamp
            color_msg.header.stamp = timestamp
            depth_msg.header.stamp = timestamp

            # set frame id to camera
            camera_info_msg.header.frame_id = 'camera'
            color_msg.header.frame_id = 'camera'
            depth_msg.header.frame_id = 'camera'

            bag.write('/camera/color/image_raw', color_msg, timestamp)
            bag.write('/camera/depth/image_raw', depth_msg, timestamp)
            bag.write('/camera/color/camera_info', camera_info_msg, timestamp)
            bag.write('/camera/depth/camera_info', camera_info_msg, timestamp)

            tum_gt_file.write(f"{timestamp.to_sec()} {pose[0,3]} {pose[1,3]} {pose[2,3]} "
                              f"{pose_msg.transform.rotation.x} {pose_msg.transform.rotation.y} "
                              f"{pose_msg.transform.rotation.z} {pose_msg.transform.rotation.w}\n")

    tum_gt_file.close()
    bag.close()
