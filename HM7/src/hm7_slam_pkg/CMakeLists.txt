cmake_minimum_required(VERSION 3.8)
project(hm7_slam_pkg)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)

install(PROGRAMS
  hm7_slam_pkg/slam_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME slam_node
)

ament_package()
