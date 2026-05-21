import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportAbsolute, SetPen
import json
import os
import threading
import time

class BulldogDrawer(Node):

    def __init__(self):

        # define o nome do nó ROS como 'bulldog_drawer'
        super().__init__('bulldog_drawer')

        self.teleport_cli = self.create_client(
            TeleportAbsolute,
            '/turtle1/teleport_absolute'
        )
        
        self.pen_cli = self.create_client(
            SetPen,
            '/turtle1/set_pen'
        )
        
        while not self.teleport_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Aguardando o Turtlesim ficar pronto...')
            
        while not self.pen_cli.wait_for_service(timeout_sec=1.0):

            self.get_logger().info('Aguardando o serviço de caneta...')

        # cria uma thread que executará a função start_drawing
        self.thread = threading.Thread(target=self.start_drawing)

        # inicia a thread
        self.thread.start()


    # configura a caneta da tartaruga
    def call_set_pen(self, r, g, b, width, off):
        req = SetPen.Request()
        req.r, req.g, req.b, req.width, req.off = r, g, b, width, off
        future = self.pen_cli.call_async(req)
        while rclpy.ok() and not future.done():
            time.sleep(0.001)


    # teletransporta a tartaruga
    def call_teleport(self, x, y):
        req = TeleportAbsolute.Request()
        req.x, req.y, req.theta = x, y, 0.0
        future = self.teleport_cli.call_async(req)
        while rclpy.ok() and not future.done():
            time.sleep(0.001)


    # função responsável pelo desenho
    def start_drawing(self):
        json_path = os.path.expanduser(
            '~/eng_comp/2_ano/modulo_6/programacao/ponderada/ros_visao/output/pontos_turtle.json'
        )
        try:
            with open(json_path, 'r') as f:

                # carrega os dados JSON para a variável pontos
                pontos = json.load(f)
            self.get_logger().info(
                f"Iniciando desenho de {len(pontos)} pontos."
            )
            for i, dado_ponto in enumerate(pontos):
                px, py, estado_caneta = dado_ponto
                offset_x = 6.8 
                offset_y = 5.8  
                tx = px + offset_x
                ty = py + offset_y
                tx = max(0.2, min(10.8, tx))
                ty = max(0.2, min(10.8, ty))
                
                # estado da caneta
                if estado_caneta == 1:

                    # levanta a caneta
                    self.call_set_pen(0, 0, 0, 0, 1)
                    time.sleep(0.01)
                    self.call_teleport(tx, ty)

                    # abaixa a caneta
                    self.call_set_pen(255, 255, 255, 2, 0)

                else:
                    self.call_teleport(tx, ty)

                if i % 100 == 0:

                    # progresso do desenho
                    self.get_logger().info(
                        f"Desenhando ponto {i}/{len(pontos)}..."
                    )
                
                time.sleep(0.001)

            # Mensagem final de sucesso
            self.get_logger().info("Desenho finalizado perfeitamente!")
            
        except Exception as e:
            self.get_logger().error(
                f"Erro crítico no loop de desenho: {e}"
            )

# roda o ROS2
def main():
    rclpy.init()
    node = BulldogDrawer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()