#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from turtle_service_pkg.srv import SpawnTurtle
from turtlesim.srv import Kill, Spawn


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


class SpawnServer(Node):
    def __init__(self):
        super().__init__('spawn_server')

        self.callback_group = ReentrantCallbackGroup()
        self.run_id = 0

        self.service = self.create_service(
            SpawnTurtle,
            'spawn_turtle',
            self.handle_spawn_request,
            callback_group=self.callback_group
        )

        self.spawn_client = self.create_client(
            Spawn,
            '/spawn',
            callback_group=self.callback_group
        )

        self.kill_client = self.create_client(
            Kill,
            '/kill',
            callback_group=self.callback_group
        )

        while not self.spawn_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /spawn service...')

        while not self.kill_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /kill service...')

        self.get_logger().info('Custom service /spawn_turtle is ready.')

    def call_service(self, client, request, timeout_sec=5.0):
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_sec)

        if future.done():
            return future.result()
        return None

    def handle_spawn_request(self, request, response):
        count = clamp(int(request.count), 2, 8)
        base_name = request.base_name.strip()

        if not base_name:
            base_name = 'demo_turtle'

        self.run_id += 1
        prefix = f'{base_name}_{self.run_id}'
        spawned_names = []

        center_x = 5.54
        center_y = 5.54
        radius = 3.2

        self.get_logger().info(
            f'Received request: count={count}, base_name={base_name}'
        )

        for index in range(count):
            angle = 2.0 * math.pi * index / count
            x_coord = center_x + radius * math.cos(angle)
            y_coord = center_y + radius * math.sin(angle)

            spawn_request = Spawn.Request()
            spawn_request.x = float(x_coord)
            spawn_request.y = float(y_coord)
            spawn_request.theta = 0.0
            spawn_request.name = f'{prefix}_{index + 1}'

            spawn_result = self.call_service(self.spawn_client, spawn_request)
            if spawn_result is None:
                response.success = False
                response.spawned_count = len(spawned_names)
                response.removed_count = 0
                response.message = 'Failed while spawning turtles.'
                return response

            spawned_names.append(spawn_result.name)
            self.get_logger().info(
                f'Spawned: {spawn_result.name} at '
                f'x={x_coord:.2f}, y={y_coord:.2f}'
            )
            time.sleep(0.20)

        self.get_logger().info('All turtles spawned. Waiting before removal...')
        time.sleep(2.0)

        removed_count = 0
        for turtle_name in spawned_names:
            kill_request = Kill.Request()
            kill_request.name = turtle_name

            kill_result = self.call_service(self.kill_client, kill_request)
            if kill_result is not None:
                removed_count += 1
                self.get_logger().info(f'Removed: {turtle_name}')

            time.sleep(0.20)

        response.success = True
        response.spawned_count = len(spawned_names)
        response.removed_count = removed_count
        response.message = (
            f'Spawned {len(spawned_names)} turtles and removed {removed_count} turtles.'
        )

        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = SpawnServer()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()