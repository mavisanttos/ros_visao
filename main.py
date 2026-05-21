import cv2
import os
import numpy as np
import processamento as proc
import json
import matplotlib.pyplot as plt

def main():
    img_original = cv2.imread('dog.jpg')
    if img_original is None: return

    # --- PIPELINE DE IMAGEM (O que já fizemos) ---
    img_cinza = proc.converter_para_cinza(img_original)
    img_suave = proc.filtro_gaussiano(img_cinza)
    img_sobel = proc.detectar_bordas_sobel(img_suave)

    # Binarização por zonas
    h, w = img_sobel.shape
    img_binaria = np.zeros_like(img_sobel)
    colunas = np.arange(w)
    
    mask_parede = (colunas / w * 10 < 1.8)
    mask_linha_corpo = (colunas / w * 10 >= 1.8) & (colunas / w * 10 < 3.0)
    mask_resto = (colunas / w * 10 >= 3.0)

    img_binaria[:, mask_parede] = np.where(img_sobel[:, mask_parede] >= 110, 255, 0)
    img_binaria[:, mask_linha_corpo] = np.where(img_sobel[:, mask_linha_corpo] >= 30, 255, 0)
    img_binaria[:, mask_resto] = np.where(img_sobel[:, mask_resto] >= 85, 255, 0)

    limite_x = 265 
    img_binaria[:, :limite_x] = 0

    # Limpeza e Dilatação
    img_limpa = proc.remover_ruido(img_binaria, limite_vizinhos=5)
    img_final = proc.dilatar_imagem(img_limpa)

    # --- AMOSTRAGEM INTELIGENTE (RESOLVE OS 30 MIL PONTOS CAÓTICOS) ---
    print("Filtrando e reduzindo a densidade de pontos para a tartaruga...")
    # Coleta os índices de onde há borda
    indices_y, indices_x = np.where(img_final == 255)
    
    # Criamos um passo de amostragem. Pega 1 pixel a cada 4 para aliviar o processamento.
    # Isso reduz drasticamente o número de pontos sem perder a silhueta do cachorro.
    passo = 4 
    indices_x_filtrados = indices_x[::passo]
    indices_y_filtrados = indices_y[::passo]
    
    # Reconstrói a imagem final limpa e reduzida para o extrator cartesiano ler de forma leve
    img_amostrada = np.zeros_like(img_final)
    img_amostrada[indices_y_filtrados, indices_x_filtrados] = 255

    # --- MAPEAMENTO CARTESIANO ---
    print("Gerando pontos estruturados com Vizinho Mais Próximo...")
    lista_pontos = proc.extrair_pontos_cartesiano(img_amostrada, escala=0.015)

    # Criação da pasta de saída se não existir
    if not os.path.exists('output'): 
        os.makedirs('output')
    
    # Salvamento passo a passo usando Matplotlib (Consistente com o edital)
    print("Salvando todas as etapas em 'output/' com Matplotlib...")
    plt.imsave('output/passo1_cinza.jpg', img_cinza, cmap='gray')
    plt.imsave('output/passo2_suavizado.jpg', img_suave, cmap='gray')
    plt.imsave('output/passo3_sobel.jpg', img_sobel, cmap='gray')
    plt.imsave('output/passo4_binaria_zonas.jpg', img_binaria, cmap='gray')
    plt.imsave('output/passo5_limpa.jpg', img_limpa, cmap='gray')
    plt.imsave('output/passo6_final_dilatada.jpg', img_amostrada, cmap='gray') # Salva a versão amostrada ideal
    
    # Exportação das coordenadas para o JSON do ROS
    caminho_json = os.path.join(os.path.dirname(__file__), 'output/pontos_turtle.json')
    with open(caminho_json, 'w') as f:
        json.dump(lista_pontos, f)

    print(f"Sucesso! {len(lista_pontos)} pontos gerados de forma otimizada em 'output/pontos_turtle.json'")

if __name__ == "__main__":
    main()