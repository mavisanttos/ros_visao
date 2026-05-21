import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # abre o simulador do Turtlesim automaticamente
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='simulador_turtlesim'
        ),
        # abre o nó de desenho
        Node(
            package='turtle_draw_pkg',
            executable='drawer_node',
            name='desenhista_bulldog',
            output='screen' # print dos logs
        )
    ])