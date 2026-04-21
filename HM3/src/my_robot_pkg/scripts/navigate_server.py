#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from my_robot_pkg.action import Navigate


class NavigateServer(Node):
    def __init__(self):
        super().__init__('navigate_server')

        self._action_server = ActionServer(
            self,
            Navigate,
            'navigate',
            self.execute_callback,
        )

        self.get_logger().info('Navigate Action Server started')

    def execute_callback(self, goal_handle):
        target_x = goal_handle.request.target_x
        target_y = goal_handle.request.target_y

        self.get_logger().info(
            f'Received goal: x={target_x:.2f}, y={target_y:.2f}'
        )

        feedback = Navigate.Feedback()
        result = Navigate.Result()

        start_time = time.time()
        steps = 20

        current_x = 0.0
        current_y = 0.0

        for step in range(1, steps + 1):
            current_x = target_x * step / steps
            current_y = target_y * step / steps

            feedback.current_x = current_x
            feedback.current_y = current_y
            feedback.remaining_dist = math.hypot(
                target_x - current_x,
                target_y - current_y,
            )

            goal_handle.publish_feedback(feedback)

            self.get_logger().info(
                f'Feedback: x={current_x:.2f}, y={current_y:.2f}, '
                f'remaining={feedback.remaining_dist:.2f}'
            )

            time.sleep(0.5)

        result.total_distance = math.hypot(target_x, target_y)
        result.elapsed_time = time.time() - start_time

        goal_handle.succeed()

        self.get_logger().info(
            f'Goal done: total_distance={result.total_distance:.2f}, '
            f'elapsed_time={result.elapsed_time:.2f}'
        )

        return result


def main(args=None):
    rclpy.init(args=args)
    node = NavigateServer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Server stopped')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()