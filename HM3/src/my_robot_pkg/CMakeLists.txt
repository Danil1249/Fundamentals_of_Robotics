cmake_minimum_required(VERSION 3.8)
project(my_robot_pkg)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(action_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/Navigate.action"
)

install(PROGRAMS
  scripts/navigate_server.py
  scripts/navigate_client.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()