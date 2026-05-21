#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from turtlesim.srv import TeleportAbsolute, SetPen
import json
import os
import threading
import time

class BulldogDrawer(Node):
    def __init__(self):
        super().__init__('bulldog_drawer')
        
        # Cria os clientes de serviço
        self.teleport_cli = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute')
        self.pen_cli = self.create_client(SetPen, '/turtle1/set_pen')
        
        # Aguarda os serviços iniciais
        while not self.teleport_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Aguardando o Turtlesim ficar pronto...')
            
        while not self.pen_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Aguardando o serviço de caneta...')

        # O PULO DO GATO: Dispara o desenho em uma thread separada para não travar o ROS 2
        self.thread = threading.Thread(target=self.start_drawing)
        self.thread.start()

    def call_set_pen(self, r, g, b, width, off):
        req = SetPen.Request()
        req.r, req.g, req.b, req.width, req.off = r, g, b, width, off
        
        # Faz a chamada síncrona com segurança
        future = self.pen_cli.call_async(req)
        # Pequeno truque para esperar o envio sem travar tudo
        while rclpy.ok() and not future.done():
            time.sleep(0.001)

    def call_teleport(self, x, y):
        req = TeleportAbsolute.Request()
        req.x, req.y, req.theta = x, y, 0.0
        
        future = self.teleport_cli.call_async(req)
        while rclpy.ok() and not future.done():
            time.sleep(0.001)

    def start_drawing(self):
        json_path = os.path.expanduser('~/eng_comp/2_ano/modulo_6/programacao/ponderada/ros_visao/output/pontos_turtle.json')
        
        try:
            with open(json_path, 'r') as f:
                pontos = json.load(f)
            
            self.get_logger().info(f"Iniciando desenho inteligente de {len(pontos)} pontos.")

            for i, dado_ponto in enumerate(pontos):
                # Desempacota as coordenadas e o estado da caneta salvos no JSON
                px, py, estado_caneta = dado_ponto
                
                # ==================== TRECHO MODIFICADO ANCORA AQUI ====================
                # Mudamos de 5.5 para valores maiores para "empurrar" o bulldog.
                # Como ele estava cortado na esquerda, colocar 6.8 joga ele para a direita.
                # Como estava cortado embaixo, colocar 5.8 joga ele um pouco para cima.
                offset_x = 6.8  
                offset_y = 5.8  
                
                tx = px + offset_x
                ty = py + offset_y
                
                # Mudamos os limites de (0.5, 10.5) para (0.2, 10.8) 
                # Isso dá mais espaço útil antes da tartaruga travar na parede
                tx = max(0.2, min(10.8, tx))
                ty = max(0.2, min(10.8, ty))
                # =======================================================================
                
                if estado_caneta == 1:
                    # LEVANTA A CANETA (off=1) para mover até o início da nova linha
                    self.call_set_pen(0, 0, 0, 0, 1)
                    time.sleep(0.01)
                    self.call_teleport(tx, ty)
                    # ABAIXA A CANETA (off=0) com cor branca e espessura 2 para começar a desenhar
                    self.call_set_pen(255, 255, 255, 2, 0)
                else:
                    # Apenas se move com a caneta abaixada
                    self.call_teleport(tx, ty)

                if i % 100 == 0:
                    self.get_logger().info(f"Desenhando ponto {i}/{len(pontos)}...")
                
                time.sleep(0.001)

            self.get_logger().info("Bulldog finalizado perfeitamente!")
            
        except Exception as e:
            self.get_logger().error(f"Erro crítico no loop de desenho: {e}")

def main():
    rclpy.init()
    node = BulldogDrawer()
    try:
        # Mantém o nó do ROS vivo escutando os callbacks do simulador
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()