#!/usr/bin/env python3

import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from my_robot_pkg.action import Navigate


class NavigateClient(Node):
    def __init__(self, target_x, target_y):
        super().__init__('navigate_client')

        self.target_x = target_x
        self.target_y = target_y

        self._client = ActionClient(self, Navigate, 'navigate')

    def send_goal(self):
        self.get_logger().info('Waiting for action server...')
        self._client.wait_for_server()

        goal_msg = Navigate.Goal()
        goal_msg.target_x = self.target_x
        goal_msg.target_y = self.target_y

        self.get_logger().info(
            f'Sending goal: x={self.target_x:.2f}, y={self.target_y:.2f}'
        )

        future = self._client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback,
        )
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            rclpy.shutdown()
            return

        self.get_logger().info('Goal accepted')

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback

        self.get_logger().info(
            f'Feedback: x={feedback.current_x:.2f}, '
            f'y={feedback.current_y:.2f}, '
            f'remaining={feedback.remaining_dist:.2f}'
        )

    def result_callback(self, future):
        result = future.result().result

        self.get_logger().info(
            f'Result: total_distance={result.total_distance:.2f}, '
            f'elapsed_time={result.elapsed_time:.2f}'
        )

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)

    target_x = 5.0
    target_y = 3.0

    if len(sys.argv) >= 3:
        try:
            target_x = float(sys.argv[1])
            target_y = float(sys.argv[2])
        except ValueError:
            pass

    node = NavigateClient(target_x, target_y)
    node.send_goal()
    rclpy.spin(node)
    node.destroy_node()


if __name__ == '__main__':
    main()