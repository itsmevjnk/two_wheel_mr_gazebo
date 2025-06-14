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
from launch.actions import DeclareLaunchArgument, OpaqueFunction, IncludeLaunchDescription, GroupAction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource, AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition

def launch_spawner(context):
    spawn_file = os.path.join(
        get_package_share_directory('two_wheel_mr_gazebo'),
        'launch', 'spawn.launch.py'
    )
    bridge_file = os.path.join(
        get_package_share_directory('two_wheel_mr_gazebo'),
        'launch', 'bridge.launch.xml'
    )

    x_pose = LaunchConfiguration('x_pose', default='0.0').perform(context)
    y_pose = LaunchConfiguration('y_pose', default='0.0').perform(context)
    yaw_pose = LaunchConfiguration('yaw_pose', default='0.0').perform(context)
    domain = LaunchConfiguration('domain').perform(context)
    # publish_static = LaunchConfiguration('publish_static', default=True)

    robot_name = f'robot{domain}'
    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(spawn_file),
            launch_arguments={
                'x_pose': x_pose,
                'y_pose': y_pose,
                'yaw_pose': yaw_pose,
                'namespace': robot_name,
                'publish_static': 'false' # we'll handle it ourselves
            }.items()
        ),
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(bridge_file),
            launch_arguments={
                'namespace': robot_name,
                'domain': domain
            }.items()
        ),
        GroupAction([
            SetEnvironmentVariable('ROS_DOMAIN_ID', domain),
            Node(
                package='odom_tf_publisher',
                executable='pub_node',
                name=f'two_wheel_mr_{robot_name}_odom_tf',
                output='screen',
                parameters=[
                    {
                        'use_sim_time': True
                    }
                ]
            ),
            Node(
                package='tf2_ros',
                executable='static_transform_publisher',
                name=f'two_wheel_mr_{robot_name}_base_footprint_pub',
                arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint'],
                output='screen',
                # condition=IfCondition(publish_static)
            ),
            Node(
                package='tf2_ros',
                executable='static_transform_publisher',
                name=f'two_wheel_mr_{robot_name}_base_scan_pub',
                arguments=['0', '0', '0.255', '0', '0', '0', 'base_link', 'base_scan'],
                output='screen',
                # condition=IfCondition(publish_static)
            ),
        ])
        
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
            'domain', default_value='0',
            description='The domain to launch the robot in'
        ),

        # DeclareLaunchArgument(
        #     'publish_static', default_value='true',
        #     description='Publish static transforms from base_link to base_footprint and base_scan'
        # ),

        OpaqueFunction(function=launch_spawner)
    ])
