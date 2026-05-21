import cv2
import os
import numpy as np
import processamento as proc
import json
import matplotlib.pyplot as plt

def main():

    # carrega a imagem do cachorro
    img_original = cv2.imread('dog.jpg')
    if img_original is None: return

    # converte a imagem original para escala de cinza
    img_cinza = proc.converter_para_cinza(img_original)

    # aplica um filtro gaussiano para suavizar a imagem, reduzindo ruídos
    img_suave = proc.filtro_gaussiano(img_cinza)

    # aplica o operador de sobel para detectar bordas
    img_sobel = proc.detectar_bordas_sobel(img_suave)

    # obtém altura (h) e largura (w) da imagem sobel
    h, w = img_sobel.shape

    # cria uma nova imagem vazia com o mesmo tamanho da imagem sobel com todos os pixels pretos
    img_binaria = np.zeros_like(img_sobel)

    # cria um array com os índices das colunas da imagem
    colunas = np.arange(w)
    
    # cria uma máscara booleana para a região da parede
    # converte a posição horizontal em uma escala de 0 a 10
    # tudo menor que 1.8 pertence à parede
    mask_parede = (colunas / w * 10 < 1.8)

    # cria uma máscara para a linha do corpo do cachorro
    # seleciona colunas entre 1.8 e 3.0
    mask_linha_corpo = (colunas / w * 10 >= 1.8) & (colunas / w * 10 < 3.0)

    # cria uma máscara para o restante da imagem
    # tudo que for maior ou igual a 3.0
    mask_resto = (colunas / w * 10 >= 3.0)

    # aplica binarização apenas na região da parede
    # se o pixel da imagem sobel for maior ou igual a 110: vira branco (255)
    # caso contrário: vira preto (0)
    img_binaria[:, mask_parede] = np.where(img_sobel[:, mask_parede] >= 110, 255, 0)

    # aplica binarização na linha do corpo
    # usa limiar menor (30) porque essa região possui bordas mais fracas
    img_binaria[:, mask_linha_corpo] = np.where(img_sobel[:, mask_linha_corpo] >= 30, 255, 0)

    # aplica binarização no restante da imagem
    # usa limiar intermediário (85)
    img_binaria[:, mask_resto] = np.where(img_sobel[:, mask_resto] >= 85, 255, 0)

    # define um limite horizontal
    limite_x = 265 

    # remove completamente tudo que estiver antes desse limite
    # todas as colunas até 265 viram preto
    # elimina partes indesejadas da imagem
    img_binaria[:, :limite_x] = 0

    # remove ruídos da imagem binária
    # o parâmetro limite_vizinhos=5: um pixel só permanece se tiver pelo menos 5 vizinhos ativos
    img_limpa = proc.remover_ruido(img_binaria, limite_vizinhos=5)

    # aplica dilatação na imagem
    # a dilatação engrossa as bordas brancas
    img_final = proc.dilatar_imagem(img_limpa)

    # encontra todos os pixels brancos da imagem final
    indices_y, indices_x = np.where(img_final == 255)

    # passo da amostragem onde a cada 4 pixels encontrados, apenas 1 será mantido
    passo = 4
    indices_x_filtrados = indices_x[::passo]

    # faz a mesma filtragem para os índices y
    indices_y_filtrados = indices_y[::passo]

    # cria uma nova imagem vazia
    img_amostrada = np.zeros_like(img_final)

    # marca de branco apenas os pixels filtrados
    img_amostrada[indices_y_filtrados, indices_x_filtrados] = 255

    # converte os pixels brancos da imagem em coordenadas cartesianas
    # escala=0.015 reduz as coordenadas para o sistema do ROS/turtlesim
    lista_pontos = proc.extrair_pontos_cartesiano(img_amostrada, escala=0.015)

    # verifica se a pasta 'output' NÃO existe
    if not os.path.exists('output'): 
        # cria a pasta 'output'
        os.makedirs('output')

    # imagens processadas
    print("Salvando todas as etapas em 'output/'...")
    plt.imsave('output/passo1_cinza.jpg', img_cinza, cmap='gray')
    plt.imsave('output/passo2_suavizado.jpg', img_suave, cmap='gray')
    plt.imsave('output/passo3_sobel.jpg', img_sobel, cmap='gray')
    plt.imsave('output/passo4_binaria_zonas.jpg', img_binaria, cmap='gray')
    plt.imsave('output/passo5_limpa.jpg', img_limpa, cmap='gray')
    plt.imsave('output/passo6_final_dilatada.jpg', img_amostrada, cmap='gray') 
    

    # caminho para o arquivo JSON
    caminho_json = os.path.join(os.path.dirname(__file__), 'output/pontos_turtle.json')
    with open(caminho_json, 'w') as f:
        # salva a lista de pontos dentro do arquivo JSON
        json.dump(lista_pontos, f)

    print(f"{len(lista_pontos)} pontos gerados em 'output/pontos_turtle.json'")

if __name__ == "__main__":
    main()