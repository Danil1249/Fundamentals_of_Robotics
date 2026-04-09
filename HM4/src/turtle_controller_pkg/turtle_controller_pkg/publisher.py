#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class TurtlePublisher(Node):
    def __init__(self):
        super().__init__('turtle_publisher')

        self.publisher_ = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.publish_cmd)

        # Своя логика движения: квадрат.
        # 20 шагов по 0.1 c при linear.x = 1.5 -> одна сторона квадрата.
        # 10 шагов по 0.1 c при angular.z = 1.57 -> примерно поворот на 90°.
        self.phases = [
            {'name': 'forward_1', 'steps': 20, 'linear_x': 1.5, 'angular_z': 0.0},
            {'name': 'turn_1',    'steps': 10, 'linear_x': 0.0, 'angular_z': 1.57},
            {'name': 'forward_2', 'steps': 20, 'linear_x': 1.5, 'angular_z': 0.0},
            {'name': 'turn_2',    'steps': 10, 'linear_x': 0.0, 'angular_z': 1.57},
            {'name': 'forward_3', 'steps': 20, 'linear_x': 1.5, 'angular_z': 0.0},
            {'name': 'turn_3',    'steps': 10, 'linear_x': 0.0, 'angular_z': 1.57},
            {'name': 'forward_4', 'steps': 20, 'linear_x': 1.5, 'angular_z': 0.0},
            {'name': 'turn_4',    'steps': 10, 'linear_x': 0.0, 'angular_z': 1.57},
        ]

        self.phase_index = 0
        self.step_in_phase = 0

        self.get_logger().info('Publisher started. Motion logic: square path.')

    def publish_cmd(self):
        current_phase = self.phases[self.phase_index]

        message = Twist()
        message.linear.x = current_phase['linear_x']
        message.angular.z = current_phase['angular_z']
        self.publisher_.publish(message)

        if self.step_in_phase == 0:
            self.get_logger().info(
                f"Start phase: {current_phase['name']} | "
                f"linear.x={message.linear.x:.2f}, angular.z={message.angular.z:.2f}"
            )

        self.step_in_phase += 1

        if self.step_in_phase >= current_phase['steps']:
            self.phase_index = (self.phase_index + 1) % len(self.phases)
            self.step_in_phase = 0


def main(args=None):
    rclpy.init(args=args)
    node = TurtlePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()