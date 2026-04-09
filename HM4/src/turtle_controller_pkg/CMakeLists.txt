cmake_minimum_required(VERSION 3.8)
project(turtle_controller_pkg)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(turtlesim REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  ${PROJECT_NAME}/publisher.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME publisher
)

install(PROGRAMS
  ${PROJECT_NAME}/subscriber.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME subscriber
)

ament_package()