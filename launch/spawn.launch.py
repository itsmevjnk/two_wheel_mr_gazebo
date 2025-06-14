# Copyright 2019 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition

def launch_spawner(context):
    urdf_path = os.path.join(
        get_package_share_directory('two_wheel_mr_gazebo'), 'sdf',
        'two_wheel_mr.sdf'
    )

    x_pose = LaunchConfiguration('x_pose', default='0.0').perform(context)
    y_pose = LaunchConfiguration('y_pose', default='0.0').perform(context)
    yaw_pose = LaunchConfiguration('yaw_pose', default='0.0').perform(context)
    namespace = LaunchConfiguration('namespace').perform(context)
    publish_static = LaunchConfiguration('publish_static')
    
    has_ns = len(namespace) > 0

    return [
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            name=f'two_wheel_mr{f"_{namespace}" if has_ns else ""}_spawner',
            arguments=[
                '-entity', namespace,
                '-file', urdf_path,
                '-x', x_pose,
                '-y', y_pose,
                '-z', '0.01',
                '-Y', yaw_pose,
            ] + (['-robot_namespace', namespace] if has_ns else []),
            output='screen'
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name=f'two_wheel_mr{f"_{namespace}" if has_ns else ""}_base_footprint_pub',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint'],
            output='screen',
            condition=IfCondition(publish_static)
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name=f'two_wheel_mr{f"_{namespace}" if has_ns else ""}_base_scan_pub',
            arguments=['0', '0', '0.255', '0', '0', '0', 'base_link', 'base_scan'],
            output='screen',
            condition=IfCondition(publish_static)
        ),
    ]

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'x_pose', default_value='0.0',
            description='Initial X position (in metres)'
        ),

        DeclareLaunchArgument(
            'y_pose', default_value='0.0',
            description='Initial Y position (in metres)'
        ),

        DeclareLaunchArgument(
            'yaw_pose', default_value='0.0',
            description='Initial yaw angle (in radians)'
        ),

        DeclareLaunchArgument(
            'namespace', default_value='',
            description='The namespace of the robot to be spawned (optional)'
        ),

        DeclareLaunchArgument(
            'publish_static', default_value='true',
            description='Publish static transforms from base_link to base_footprint and base_scan'
        ),

        OpaqueFunction(function=launch_spawner)
    ])
