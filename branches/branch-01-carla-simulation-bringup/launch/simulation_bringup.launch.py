import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sensors_json_path = os.path.join(pkg_dir, 'config', 'sensors.json')

    # Arguments
    host_arg = DeclareLaunchArgument('host', default_value='127.0.0.1', description='CARLA Host IP')
    port_arg = DeclareLaunchArgument('port', default_value='2000', description='CARLA Port')
    town_arg = DeclareLaunchArgument('town', default_value='Town01', description='CARLA Town/Map')
    synchronous_mode_arg = DeclareLaunchArgument('synchronous_mode', default_value='True', description='Sync Mode')

    # 1. CARLA ROS Bridge Node
    carla_ros_bridge_node = Node(
        package='carla_ros_bridge',
        executable='bridge',
        name='carla_ros_bridge',
        output='screen',
        parameters=[{
            'host': LaunchConfiguration('host'),
            'port': LaunchConfiguration('port'),
            'town': LaunchConfiguration('town'),
            'synchronous_mode': LaunchConfiguration('synchronous_mode'),
            'fixed_delta_seconds': 0.05
        }]
    )

    # 2. CARLA Ego Vehicle Spawner with multi-modal sensor rig
    carla_spawn_object_node = Node(
        package='carla_spawn_objects',
        executable='carla_spawn_objects',
        name='carla_ego_spawner',
        output='screen',
        parameters=[{
            'objects_definition_file': sensors_json_path
        }]
    )

    # 3. Telemetry Health Monitor Node
    health_monitor_node = Node(
        package='pothole_simulation_bringup',
        executable='telemetry_health_monitor.py',
        name='telemetry_health_monitor',
        output='screen'
    )

    return LaunchDescription([
        host_arg,
        port_arg,
        town_arg,
        synchronous_mode_arg,
        carla_ros_bridge_node,
        carla_spawn_object_node,
        health_monitor_node
    ])
