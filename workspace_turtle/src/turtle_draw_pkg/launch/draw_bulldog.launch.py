import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Abre o simulador do Turtlesim automaticamente
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='simulador_turtlesim'
        ),
        # 2. Abre o seu nó de desenho logo em seguida
        Node(
            package='turtle_draw_pkg',
            executable='drawer_node',
            name='desenhista_bulldog',
            output='screen' # Faz os prints do log aparecerem neste terminal
        )
    ])