#!/usr/bin/env python3

import sys

import rclpy
from rclpy.node import Node

from turtle_service_pkg.srv import SpawnTurtle


class SpawnClient(Node):
    def __init__(self):
        super().__init__('spawn_client')

        self.client = self.create_client(SpawnTurtle, 'spawn_turtle')

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for custom service /spawn_turtle...')

    def send_request(self, count, base_name):
        request = SpawnTurtle.Request()
        request.count = int(count)
        request.base_name = base_name

        self.get_logger().info(
            f'Sending request: count={count}, base_name={base_name}'
        )

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        return future.result()


def main(args=None):
    rclpy.init(args=args)
    node = SpawnClient()

    if len(sys.argv) == 3:
        count = int(sys.argv[1])
        base_name = sys.argv[2]
    else:
        count = 6
        base_name = 'demo_turtle'

    response = node.send_request(count, base_name)

    if response is not None:
        node.get_logger().info(
            f'Response: success={response.success}, '
            f'spawned_count={response.spawned_count}, '
            f'removed_count={response.removed_count}, '
            f'message="{response.message}"'
        )
    else:
        node.get_logger().error('No response received from service.')

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()