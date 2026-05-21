import numpy as np


# converte a imagem colorida (BGR) para escala de cinza
def converter_para_cinza(imagem_bgr):

    # separa os canais da imagem em RGB
    b, g, r = imagem_bgr[:, :, 0], imagem_bgr[:, :, 1], imagem_bgr[:, :, 2]

    # aplica a fórmula de conversão para escala de cinza baseada na percepção humana
    return (0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)


# aplica um kernel sobre a imagem
def aplicar_convolucao(imagem, kernel):

    # obtém altura e largura da imagem
    img_h, img_w = imagem.shape

    # obtém altura e largura do kernel
    k_h, k_w = kernel.shape

    # calcula o padding necessário
    pad_h, pad_w = k_h // 2, k_w // 2
    
    # adiciona bordas artificiais ao redor da imagem
    imagem_pad = np.pad(imagem, ((pad_h, pad_h), (pad_w, pad_w)), mode='edge')

    # cria uma matriz de saída vazia
    output = np.zeros_like(imagem, dtype=np.float32)
    
    # percorre cada linha da imagem
    for i in range(img_h):

        # percorre cada coluna da imagem
        for j in range(img_w):

            # extrai uma janela da imagem do mesmo tamanho do kernel
            janela = imagem_pad[i : i + k_h, j : j + k_w]

            # operação de convolução
            output[i, j] = np.sum(janela * kernel)

    return np.clip(output, 0, 255).astype(np.uint8)


# filtro gaussiano na imagem que suaviza e reduz ruídos
def filtro_gaussiano(imagem):

    # define um kernel gaussiano 5x5 com maior influência dos pixels centrais
    kernel = np.array([[1,  4,  7,  4, 1],
                       [4, 16, 26, 16, 4],
                       [7, 26, 41, 26, 7],
                       [4, 16, 26, 16, 4],
                       [1,  4,  7,  4, 1]], dtype=np.float32)

    # normaliza o kernel
    kernel /= 273.0

    # aplica a convolução usando o kernel gaussiano
    return aplicar_convolucao(imagem, kernel)


# detecta bordas usando o operador de Sobel
def detectar_bordas_sobel(imagem):

    # detecta mudanças na direção X
    kx = np.array([[-1, 0, 1],
                   [-2, 0, 2],
                   [-1, 0, 1]], dtype=np.float32)

    # detecta mudanças na direção Y
    ky = np.array([[1, 2, 1],
                   [0, 0, 0],
                   [-1, -2, -1]], dtype=np.float32)
    
    # aplica convolução horizontal
    gx = aplicar_convolucao(imagem, kx).astype(np.float32)

    # aplica convolução vertical
    gy = aplicar_convolucao(imagem, ky).astype(np.float32)
    
    # calcula a magnitude do gradiente
    magnitude = np.sqrt(gx**2 + gy**2)

    # verifica se existe algum valor diferente de zero
    if magnitude.max() > 0:

        # normaliza os valores para o intervalo 0–255
        magnitude = (magnitude / magnitude.max()) * 255

    # retorna a imagem final convertida
    return magnitude.astype(np.uint8)


# remove ruídos da imagem binária baseando-se na densidade local
def remover_ruido(imagem_binaria, limite_vizinhos=3):

    # obtém altura e largura da imagem
    h, w = imagem_binaria.shape

    # cria uma cópia da imagem original
    output = imagem_binaria.copy()

    # percorre a imagem
    for i in range(2, h - 2):

        # percorre colunas
        for j in range(2, w - 2):

            # verifica se o pixel atual é branco
            if imagem_binaria[i, j] == 255:

                # extrai uma janela 5x5 ao redor do pixel
                janela = imagem_binaria[i-2:i+3, j-2:j+3]

                # soma os valores da janela, se houver poucos pixels brancos próximos o pixel é considerado ruído
                if np.sum(janela) < (limite_vizinhos * 255):

                    # remove o ruído transformando em preto
                    output[i, j] = 0

    # retorna imagem limpa
    return output


# aplica dilatação na imagem para engrossar regiões brancas e fechar falhas na imagem
def dilatar_imagem(imagem_binaria):

    # obtém dimensões da imagem
    img_h, img_w = imagem_binaria.shape

    # cria cópia da imagem
    output = imagem_binaria.copy()

    # percorre linhas
    for i in range(1, img_h - 1):

        # percorre colunas
        for j in range(1, img_w - 1):

            # se o pixel atual for branco
            if imagem_binaria[i, j] == 255:

                # transforma toda a vizinhança 3x3 em branco, expandindo a borda
                output[i-1:i+2, j-1:j+2] = 255

    # retorna imagem dilatada
    return output


# extrai coordenadas cartesianas da imagem e organiza os pontos usando o Vizinho Mais Próximo
def extrair_pontos_cartesiano(imagem_binaria, escala=0.015):

    # obtém altura e largura da imagem
    h, w = imagem_binaria.shape
    
    # encontra todos os pixels brancos da imagem
    indices_y, indices_x = np.where(imagem_binaria == 255)
    
    # cria uma lista de pontos
    pontos_restantes = [np.array([float(x), float(y)]) for x, y in zip(indices_x, indices_y)]
    
    # se não houver pontos, retorna lista vazia
    if not pontos_restantes:
        return []

    # lista que armazenará os pontos já organizados
    pontos_ordenados = []

    # posição inicial da tartaruga
    pos_atual = np.array([0.0, 0.0])
    
    # distância máxima considerada contínua
    distancia_pulo_caneta = 10.0 

    # enquanto ainda existirem pontos não visitados
    while len(pontos_restantes) > 0:

        # inicializa a menor distância como infinito
        maior_proximidade = float('inf')

        # índice do ponto mais próximo
        indice_proximo = 0
        
        # busca linear pelo ponto mais próximo
        for idx, ponto in enumerate(pontos_restantes):

            # calcula distância Euclidiana
            dist = np.linalg.norm(pos_atual - ponto)

            # se encontrar ponto mais próximo
            if dist < maior_proximidade:

                # atualiza menor distância
                maior_proximidade = dist

                # guarda índice do ponto
                indice_proximo = idx
                
        # remove da lista o ponto escolhido
        ponto_escolhido = pontos_restantes.pop(indice_proximo)

        # separa coordenadas x e y
        x, y = ponto_escolhido[0], ponto_escolhido[1]
        
        # converte coordenadas da imagem para o plano cartesiano do turtlesim
        pos_x = (x - w / 2) * escala
        pos_y = (h / 2 - y) * escala
        
        # decide se a caneta será levantada
        estado_caneta = 1 if maior_proximidade > distancia_pulo_caneta else 0
        
        # adiciona ponto na lista final
        pontos_ordenados.append((round(pos_x, 2),
                                 round(pos_y, 2),
                                 estado_caneta))
        
        # atualiza posição atual da tartaruga
        pos_atual = ponto_escolhido
            
    # retorna lista final ordenada
    return pontos_ordenados