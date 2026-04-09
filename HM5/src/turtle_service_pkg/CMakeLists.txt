cmake_minimum_required(VERSION 3.8)
project(turtle_service_pkg)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(turtlesim REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/SpawnTurtle.srv"
)

install(PROGRAMS
  turtle_service_pkg/spawn_server.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME spawn_server
)

install(PROGRAMS
  turtle_service_pkg/spawn_client.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME spawn_client
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()