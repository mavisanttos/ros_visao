import numpy as np

def converter_para_cinza(imagem_bgr):
    b, g, r = imagem_bgr[:, :, 0], imagem_bgr[:, :, 1], imagem_bgr[:, :, 2]
    return (0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)

def aplicar_convolucao(imagem, kernel):
    img_h, img_w = imagem.shape
    k_h, k_w = kernel.shape
    pad_h, pad_w = k_h // 2, k_w // 2
    
    imagem_pad = np.pad(imagem, ((pad_h, pad_h), (pad_w, pad_w)), mode='edge')
    output = np.zeros_like(imagem, dtype=np.float32)
    
    for i in range(img_h):
        for j in range(img_w):
            janela = imagem_pad[i : i + k_h, j : j + k_w]
            output[i, j] = np.sum(janela * kernel)
            
    return np.clip(output, 0, 255).astype(np.uint8)

def filtro_gaussiano(imagem):
    kernel = np.array([[1,  4,  7,  4, 1],
                       [4, 16, 26, 16, 4],
                       [7, 26, 41, 26, 7],
                       [4, 16, 26, 16, 4],
                       [1,  4,  7,  4, 1]], dtype=np.float32)
    kernel /= 273.0
    return aplicar_convolucao(imagem, kernel)

def detectar_bordas_sobel(imagem):
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float32)
    
    gx = aplicar_convolucao(imagem, kx).astype(np.float32)
    gy = aplicar_convolucao(imagem, ky).astype(np.float32)
    
    magnitude = np.sqrt(gx**2 + gy**2)
    if magnitude.max() > 0:
        magnitude = (magnitude / magnitude.max()) * 255
    return magnitude.astype(np.uint8)

def remover_ruido(imagem_binaria, limite_vizinhos=3):
    """ Remove pontos brancos isolados (ruído da parede) baseando-se na densidade local """
    h, w = imagem_binaria.shape
    output = imagem_binaria.copy()
    for i in range(2, h - 2):
        for j in range(2, w - 2):
            if imagem_binaria[i, j] == 255:
                # Verifica uma janela 5x5 ao redor do pixel
                janela = imagem_binaria[i-2:i+3, j-2:j+3]
                # Se houver poucos pixels brancos na vizinhança, é ruído solto
                if np.sum(janela) < (limite_vizinhos * 255):
                    output[i, j] = 0
    return output

def dilatar_imagem(imagem_binaria):
    img_h, img_w = imagem_binaria.shape
    output = imagem_binaria.copy()
    for i in range(1, img_h - 1):
        for j in range(1, img_w - 1):
            if imagem_binaria[i, j] == 255:
                output[i-1:i+2, j-1:j+2] = 255
    return output

def extrair_pontos_cartesiano(imagem_binaria, escala=0.015):
    """
    Extrai os pontos acesos da imagem diretamente via NumPy (sem cv2.findContours)
    e ordena-os pelo princípio do Vizinho Mais Próximo.
    """
    h, w = imagem_binaria.shape
    
    # Coleta os índices de todos os pixels brancos (255) na imagem usando puramente NumPy
    indices_y, indices_x = np.where(imagem_binaria == 255)
    
    # Transforma em uma lista de pontos [x, y] flutuantes
    pontos_restantes = [np.array([float(x), float(y)]) for x, y in zip(indices_x, indices_y)]
    
    if not pontos_restantes:
        return []

    pontos_ordenados = []
    pos_atual = np.array([0.0, 0.0])
    
    # Raio limite para decidir se a tartaruga deve levantar a caneta ou continuar desenhando junto
    distancia_pulo_caneta = 10.0 

    while len(pontos_restantes) > 0:
        maior_proximidade = float('inf')
        indice_proximo = 0
        
        # Busca linear pelo pixel mais próximo da posição atual da tartaruga
        for idx, ponto in enumerate(pontos_restantes):
            dist = np.linalg.norm(pos_atual - ponto)
            if dist < maior_proximidade:
                maior_proximidade = dist
                indice_proximo = idx
                
        # Remove o ponto escolhido da lista de pendentes
        ponto_escolhido = pontos_restantes.pop(indice_proximo)
        x, y = ponto_escolhido[0], ponto_escolhido[1]
        
        # Converte para o plano cartesiano do Turtlesim
        pos_x = (x - w / 2) * escala
        pos_y = (h / 2 - y) * escala
        
        # Se o pixel estiver muito longe do anterior, levanta a caneta (1), senão mantém abaixada (0)
        estado_caneta = 1 if maior_proximidade > distancia_pulo_caneta else 0
        
        pontos_ordenados.append((round(pos_x, 2), round(pos_y, 2), estado_caneta))
        
        # Atualiza a posição da "mão" que desenha
        pos_atual = ponto_escolhido
            
    return pontos_ordenados