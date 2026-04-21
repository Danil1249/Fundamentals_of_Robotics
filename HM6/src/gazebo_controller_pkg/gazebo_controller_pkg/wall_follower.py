#!/usr/bin/env python3

import csv
import math
import os

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from geometry_msgs.msg import TwistStamped, PoseStamped
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import LaserScan


def safe_min(values, default=3.5):
    valid = [v for v in values if math.isfinite(v) and 0.12 < v < 3.5]
    if not valid:
        return default
    return min(valid)


def quaternion_to_yaw(x, y, z, w):
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


class WallFollower(Node):
    FIND_WALL = 0
    TURN_LEFT = 1
    FOLLOW_WALL = 2

    def __init__(self):
        super().__init__('wall_follower')

        self.state = self.FIND_WALL

        self.front_dist = float('inf')
        self.right_dist = float('inf')
        self.front_right_dist = float('inf')
        self.has_scan = False

        # Параметры движения
        self.safe_front_dist = 0.50
        self.front_clear_dist = 0.65
        self.desired_right_dist = 0.55
        self.lost_wall_dist = 0.90

        self.linear_speed = 0.20
        self.search_speed = 0.15
        self.turn_speed = 0.80
        self.follow_gain = 1.8
        self.max_angular = 1.0

        self.cmd_pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.path_pub = self.create_publisher(Path, '/wall_follower_path', 10)

        scan_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            scan_qos,
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10,
        )

        self.timer = self.create_timer(0.1, self.control_loop)

        # Для Path и csv
        self.path_msg = Path()
        self.path_msg.header.frame_id = 'odom'

        self.last_saved_x = None
        self.last_saved_y = None

        self.csv_path = os.path.expanduser(
            '~/Fundamentals_of_Robotics/HM6/wall_follower_path.csv'
        )
        self.csv_file = open(self.csv_path, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['time_sec', 'x', 'y', 'yaw'])

        self.get_logger().info('Wall Follower Node Started')
        self.get_logger().info(f'Path will be saved to {self.csv_path}')

    def state_name(self, state):
        if state == self.FIND_WALL:
            return 'find_wall'
        if state == self.TURN_LEFT:
            return 'turn_left'
        return 'follow_wall'

    def set_state(self, new_state):
        if new_state != self.state:
            self.get_logger().info(
                f'State: {self.state_name(self.state)} -> {self.state_name(new_state)}'
            )
            self.state = new_state

    def scan_callback(self, msg):
        ranges = list(msg.ranges)

        self.front_dist = safe_min(ranges[0:20] + ranges[340:360], default=3.5)
        self.front_right_dist = safe_min(ranges[300:340], default=3.5)
        self.right_dist = safe_min(ranges[250:290], default=3.5)

        self.has_scan = True

    def odom_callback(self, msg):
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation

        yaw = quaternion_to_yaw(
            orientation.x,
            orientation.y,
            orientation.z,
            orientation.w,
        )

        pose = PoseStamped()
        pose.header = msg.header
        pose.header.frame_id = 'odom'
        pose.pose = msg.pose.pose

        need_save = False
        if self.last_saved_x is None or self.last_saved_y is None:
            need_save = True
        else:
            distance = math.hypot(
                position.x - self.last_saved_x,
                position.y - self.last_saved_y,
            )
            if distance >= 0.05:
                need_save = True

        if need_save:
            self.path_msg.header.stamp = self.get_clock().now().to_msg()
            self.path_msg.poses.append(pose)
            self.path_pub.publish(self.path_msg)

            time_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            self.csv_writer.writerow([
                f'{time_sec:.3f}',
                f'{position.x:.4f}',
                f'{position.y:.4f}',
                f'{yaw:.4f}',
            ])
            self.csv_file.flush()

            self.last_saved_x = position.x
            self.last_saved_y = position.y

    def make_cmd(self, linear_x=0.0, angular_z=0.0):
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = 'base_link'
        cmd.twist.linear.x = linear_x
        cmd.twist.angular.z = angular_z
        return cmd

    def control_loop(self):
        if not self.has_scan:
            return

        cmd = self.make_cmd()

        if self.state == self.FIND_WALL:
            if self.front_dist < self.safe_front_dist:
                self.set_state(self.TURN_LEFT)
                cmd.twist.linear.x = 0.0
                cmd.twist.angular.z = self.turn_speed
            elif self.right_dist < self.lost_wall_dist:
                self.set_state(self.FOLLOW_WALL)
                error = self.desired_right_dist - self.right_dist
                angular = self.follow_gain * error
                angular = max(-self.max_angular, min(self.max_angular, angular))
                cmd.twist.linear.x = self.linear_speed
                cmd.twist.angular.z = angular
            else:
                cmd.twist.linear.x = self.search_speed
                cmd.twist.angular.z = -0.35

        elif self.state == self.TURN_LEFT:
            if self.front_dist > self.front_clear_dist:
                if self.right_dist < self.lost_wall_dist:
                    self.set_state(self.FOLLOW_WALL)
                else:
                    self.set_state(self.FIND_WALL)

            if self.state == self.TURN_LEFT:
                cmd.twist.linear.x = 0.0
                cmd.twist.angular.z = self.turn_speed
            elif self.state == self.FOLLOW_WALL:
                error = self.desired_right_dist - self.right_dist
                angular = self.follow_gain * error
                angular = max(-self.max_angular, min(self.max_angular, angular))
                cmd.twist.linear.x = self.linear_speed
                cmd.twist.angular.z = angular
            else:
                cmd.twist.linear.x = self.search_speed
                cmd.twist.angular.z = -0.35

        elif self.state == self.FOLLOW_WALL:
            if self.front_dist < self.safe_front_dist:
                self.set_state(self.TURN_LEFT)
                cmd.twist.linear.x = 0.0
                cmd.twist.angular.z = self.turn_speed
            elif self.right_dist > self.lost_wall_dist and self.front_right_dist > self.lost_wall_dist:
                self.set_state(self.FIND_WALL)
                cmd.twist.linear.x = self.search_speed
                cmd.twist.angular.z = -0.35
            else:
                error = self.desired_right_dist - self.right_dist
                angular = self.follow_gain * error

                if self.front_right_dist < 0.40:
                    angular += 0.25

                angular = max(-self.max_angular, min(self.max_angular, angular))

                cmd.twist.linear.x = self.linear_speed
                cmd.twist.angular.z = angular

        self.cmd_pub.publish(cmd)

    def stop_robot(self):
        self.cmd_pub.publish(self.make_cmd(0.0, 0.0))

    def close_file(self):
        if not self.csv_file.closed:
            self.csv_file.close()


def main(args=None):
    rclpy.init(args=args)
    node = WallFollower()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down...')
    finally:
        node.stop_robot()
        node.close_file()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()