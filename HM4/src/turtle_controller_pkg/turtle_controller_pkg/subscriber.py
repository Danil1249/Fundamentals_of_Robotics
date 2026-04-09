#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose


class TurtleSubscriber(Node):
    def __init__(self):
        super().__init__('turtle_subscriber')

        self.subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

        self.message_counter = 0
        self.get_logger().info('Subscriber started. Listening to /turtle1/pose')

    def pose_callback(self, msg: Pose):
        self.message_counter += 1

        # Логируем не каждое сообщение, чтобы терминал не засыпало слишком быстро.
        if self.message_counter % 5 == 0:
            self.get_logger().info(
                f'x={msg.x:.2f}, y={msg.y:.2f}, theta={msg.theta:.2f}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = TurtleSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
    