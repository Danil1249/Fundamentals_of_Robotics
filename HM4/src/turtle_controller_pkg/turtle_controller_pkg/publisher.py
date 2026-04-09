#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class TurtlePublisher(Node):
    def __init__(self):
        super().__init__('turtle_publisher')

        self.cmd_publisher = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        # Внутри publisher подписываемся на pose,
        # чтобы движение было красивым и управляемым.
        self.pose_subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

        self.pose = None
        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.publish_cmd)

        # Центр поля turtlesim
        self.center_x = 5.54
        self.center_y = 5.54

        # Параметры спирали
        self.inner_radius = 0.35
        self.outer_radius = 4.20
        self.total_steps = 260
        self.angle_step = 0.22

        self.phase = 'spiral_out'
        self.step_index = 0
        self.phi = 0.0

        self.get_logger().info(
            'Publisher started. Motion logic: spiral out -> spiral in -> repeat'
        )

    def pose_callback(self, msg):
        self.pose = msg

    def move_to_target(self, target_x, target_y):
        if self.pose is None:
            return

        dx = target_x - self.pose.x
        dy = target_y - self.pose.y

        distance = math.sqrt(dx * dx + dy * dy)
        target_theta = math.atan2(dy, dx)
        angle_error = normalize_angle(target_theta - self.pose.theta)

        msg = Twist()
        msg.angular.z = clamp(5.0 * angle_error, -4.0, 4.0)
        msg.linear.x = min(2.0, 1.8 * distance)

        if abs(angle_error) > 0.8:
            msg.linear.x *= 0.2
        elif abs(angle_error) > 0.4:
            msg.linear.x *= 0.5

        self.cmd_publisher.publish(msg)

    def publish_cmd(self):
        if self.pose is None:
            return

        progress = self.step_index / self.total_steps

        if self.phase == 'spiral_out':
            radius = self.inner_radius + (
                self.outer_radius - self.inner_radius
            ) * progress
        else:
            radius = self.outer_radius - (
                self.outer_radius - self.inner_radius
            ) * progress

        target_x = self.center_x + radius * math.cos(self.phi)
        target_y = self.center_y + radius * math.sin(self.phi)

        self.move_to_target(target_x, target_y)

        self.phi += self.angle_step
        self.step_index += 1

        if self.step_index > self.total_steps:
            self.step_index = 0
            if self.phase == 'spiral_out':
                self.phase = 'spiral_in'
                self.get_logger().info('Switching phase: spiral_in')
            else:
                self.phase = 'spiral_out'
                self.get_logger().info('Switching phase: spiral_out')


def main(args=None):
    rclpy.init(args=args)
    node = TurtlePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()