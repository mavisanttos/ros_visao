# Turtle Draw: desenhando com robô a partir de uma imagem

Este projeto integra **Visão Computacional** e **Robótica Móvel com ROS 2**. O objetivo principal é processar uma imagem digital de um Cachorro (`dog.jpg`), extrair suas bordas e contornos de forma matemática, e transpor esses dados em comandos geométricos e de controle de atuador para que o nó simulado do **Turtlesim** redesenhe a imagem.

## Como Executar o Projeto

Siga os passos abaixo em ordem cronológica para preparar o ambiente, processar a imagem e iniciar a simulação.

### 1. Pré-requisitos e Dependências

Certifique-se de que possui o **ROS 2 (Jazzy, Humble ou Desktop completo)** instalado em seu sistema, além do gerenciador de pacotes do Python.

Instale as dependências de Python necessárias executando no seu terminal:

```bash
pip3 install numpy opencv-python
```

### 2. Clonando o Repositório e Estruturando

Abra o seu terminal na pasta onde costuma clonar seus projetos e execute:

```bash
git clone https://github.com/mavisanttos/ros_visao.git
cd ros_visao
```

### 3. Executando o Pipeline de Visão Computacional

Precisamos processar a imagem para extrair a matriz matemática de coordenadas e salvar o arquivo de tráfego de dados `pontos_turtle.json`.

Na raiz do repositório, execute:

```bash
python3 main.py
```

Isso criará a pasta `output/` contendo o arquivo JSON de trajetórias e o passo a passo em imagens do pipeline, permitindo verificar a integridade visual do processamento antes de chamar o nó do ROS.

### 4. Compilando o Workspace do ROS 2

Navegue para a pasta do ambiente workspace configurado para a simulação:

```bash
cd workspace_turtle
```

Compile o pacote usando o colcon e carregue as variáveis de ambiente locais:

```bash
colcon build --packages-select turtle_draw_pkg
source install/setup.bash
```

### 5. Executando o Projeto via Arquivo Launch

Criei um script de automação de inicialização (launch). Com apenas um único comando, o ROS abrirá a interface visual azul do `turtlesim_node` e disparará o nó inteligente de desenho `drawer_node` de forma integrada no mesmo terminal:

```bash
ros2 launch turtle_draw_pkg draw_bulldog.launch.py
```

A tartaruga iniciará o rastreamento, limpando e redesenhando as bordas do Cachorro na tela.

## Estrutura de Pastas do Repositório

Os pacotes compilados e locais de hardware (`build`, `install`, `log`) foram adicionados ao `.gitignore` para manter o código limpo.

```
ros_visao/
│
├── output/                           # Gerado pela main.py (Imagens intermediárias e dados)
│   ├── passo1_cinza.jpg              # Conversão em tons de cinza
│   ├── passo2_suavizado.jpg          # Filtro gaussiano contra ruído de alta frequência
│   ├── passo3_sobel.jpg              # Magnitude de gradientes e bordas brutas
│   ├── passo4_binaria_zonas.jpg      # Limiarização adaptativa por regiões
│   ├── passo5_limpa.jpg              # Filtro de densidade local (remoção de artefatos)
│   ├── passo6_final_dilatada.jpg     # Alinhamento e espessura final das trilhas
│   └── pontos_turtle.json            # Coordenadas vetoriais estruturadas (X, Y, Estado_Caneta)
│
├── workspace_turtle/                 # Ambiente de Desenvolvimento ROS 2
│   ├── src/
│   │   └── turtle_draw_pkg/          # Pacote customizado do ROS 2
│   │       ├── launch/
│   │       │   └── draw_bulldog.launch.py  # Arquivo de inicialização e orquestração simultânea
│   │       ├── turtle_draw_pkg/
│   │       │   ├── __init__.py
│   │       │   └── drawer_node.py   # Nó do ROS
│   │       ├── package.xml           # Declaração de dependências do ecossistema ROS
│   │       └── setup.py              # Script de mapeamento, pontos de entrada e build do pacote
│
├── .gitignore                        # Regras para ignorar arquivos e pastas
├── dog.jpg                           # Imagem de entrada do projeto
├── main.py                           # Arquivo centralizador do pipeline de visão computacional
├── processamento.py                  # Módulo contendo o processamento da imagem para vizualização das bordas
└── README.md                         # Documentação técnica detalhada do projeto
```

## Processamento de Imagem

As principais etapas do pipeline contidas no arquivo `processamento.py` foram programadas baseadas em matrizes do numpy, evitando abstrações comerciais como Canny.

### 1. Conversão para Tons de Cinza Ponderada (`converter_para_cinza`)

Em vez de uma simples média aritmética dos canais RGB, foi implementada a fórmula baseada na luminosidade perceptiva humana (padrão ITU-R BT.601):

$$\text{Y} = 0.299 \cdot R + 0.587 \cdot G + 0.114 \cdot B$$

O olho humano possui maior sensibilidade ao verde e menor ao azul. Essa ponderação preserva os contrastes reais das rugas do cachorro e remove as distorções cromáticas do fundo.

### 2. Filtro de Suavização Gaussiana (`filtro_gaussiano`)

Foi aplicada uma operação de convolução utilizando um Kernel Gaussiano de tamanho $5 \times 5$ com fator de normalização de $1/273$:

```python
kernel = np.array([[1,  4,  7,  4, 1],
                   [4, 16, 26, 16, 4],
                   [7, 26, 41, 26, 7],
                   [4, 16, 26, 16, 4],
                   [1,  4,  7,  4, 1]], dtype=np.float32) / 273.0
```

As bordas puras geram ruído de alta frequência (falsas descontinuidades). O blur gaussiano remove pequenas imperfeições e texturas da imagem sem destruir o alinhamento das bordas principais (focinho, orelhas).

### 3. Detector de Bordas Sobel (`detectar_bordas_sobel`)

Diferente de filtros simples de derivadas, o Sobel calcula a aproximação do gradiente espacial da intensidade de cor de forma independente para as componentes horizontal e vertical através de convoluções com kernels $3 \times 3$:

$$K_x = \begin{bmatrix} -1 & 0 & 1 \\ -2 & 0 & 2 \\ -1 & 0 & 1 \end{bmatrix}, \quad K_y = \begin{bmatrix} 1 & 2 & 1 \\ 0 & 0 & 0 \\ -1 & -2 & -1 \end{bmatrix}$$

A magnitude final de cada pixel é obtida através de:

$$G = \sqrt{G_x^2 + G_y^2}$$

O operador Sobel introduz uma ponderação de suavização no elemento central (fator 2), tornando a detecção muito mais resistente a ruídos localizados e mapeando perfeitamente as transições abruptas de intensidade.

### 4. Binarização Customizada por Zonas de Interesse

Uma limiarização fixa global (Global Thresholding) falharia miseravelmente neste cenário por causa das diferenças de iluminação da foto. A orelha esquerda possui alto contraste com a parede, enquanto as linhas inferiores do corpo confundem-se com as sombras. Foi criada uma binarização vetorial baseada em máscaras de colunas:

- **Zona 1 (Parede/Fundo):** Limiar estrito ($\ge 110$) para barrar oscilações do plano traseiro.
- **Zona 2 (Ombro e Corpo):** Limiar ultra sensível ($\ge 30$) para capturar as linhas mais fracas do corpo do cachorro.
- **Zona 3 (Rosto e Feições):** Limiar equilibrado ($\ge 85$) para desenhar os olhos, dobras e detalhes internos com precisão.

### 5. Remoção de Ruído Local e Janela de Densidade

Para sumir com ruídos sal-e-pimenta isolados, foi programado o método `remover_ruido`. Ele inspeciona uma vizinhança $5 \times 5$ ao redor de qualquer pixel ativo. Caso a soma da intensidade dos vizinhos seja inferior a um teto específico (`limite_vizinhos = 3`), o pixel central é sumariamente descartado (definido como preto).

### 6. Amostragem de Densidade e Extração de Pontos por Nuvem Cartesianas

O código mapeia todos os pixels brancos ativos na imagem utilizando indexação matricial (`np.where`). 
Para evitar o colapso do sistema por sobrecarga de dados (um contorno complexo gera dezenas de milhares de pontos), implementou-se uma amostragem estatística na `main.py` recolhendo 1 a cada 4 pixels (redução de densidade de 75%), preservando totalmente a silhueta geométrica para o envio ao simulador.

## Desafios Geométricos Encontrados

Durante o ciclo de desenvolvimento da aplicação, o projeto passou por problemas que demandaram correções na modelagem matemática e algorítmica.

### Desafio 1: O Fenômeno da "Parede Sólida de Tinta" no Turtlesim

**O Problema:** Inicialmente, o código varria a imagem binarizada de forma linear (linha por linha, da esquerda para a direita, como uma impressora antiga). Como o traço da caneta do Turtlesim possui espessura fixa e o robô recebia uma nuvem maciça de milhares de pontos colados pertencentes às bordas grossas, o rastro se sobrepunha tanto que o resultado virava um bloco branco gigante na tela, em vez de um desenho de linhas.

**A Solução:** Modifiquei a extração de pontos para lidar com Nuvens de Pontos via Numpy. A matriz sofre uma forte amostragem (pulo matricial) reduzindo a densidade de pontos sem perder a geometria. Isso desincha as massas sobrepostas e forma traços organizados.

### Desafio 2: Falta de Controle de Atuador (Riscos Conectando Tudo)

**O Problema:** Como a imagem é composta por partes separadas (ex: o olho esquerdo não encosta na orelha direita), o robô se deslocava com a caneta abaixada de uma ponta a outra da tela, cruzando o desenho ao meio com linhas indesejadas e destruindo as bordas.

**A Solução:** Modifiquei a estrutura de dados para exportar uma tupla contendo 3 elementos: `(X, Y, Estado_Caneta)`. O parâmetro `Estado_Caneta` assume valor `1` sempre que uma nova linha independente começa e `0` no meio da linha. No `drawer_node.py`, criei um cliente de serviço que chama a API do Turtlesim `/turtle1/set_pen`. Sempre que o estado é `1`, o robô levanta a caneta (`off=1`), faz o teleporte rápido até a nova coordenada e abaixa a caneta (`off=0`) aplicando a cor branca para iniciar o traço.

### Desafio 3: Trajetórias Aleatórias

**O Problema:** A extração via `np.where` gera a nuvem de pontos varrendo a imagem de cima para baixo. Se entregássemos essa matriz bruta, o robô cruzaria a tela inteira em zigue-zague infinito emulando uma impressora, demorando horas para desenhar traços simples.

**A Solução:** Implementei o algoritmo do **Vizinho Mais Próximo (Nearest Neighbor)** diretamente sobre as coordenadas do arquivo `processamento.py`. Um loop iterativo calcula a distância Euclidiana entre a tartaruga e TODOS os pixels ainda não visitados na imagem, saltando para o ponto espacialmente mais vantajoso. Além de rotear de forma fluida, o sistema detecta se o ponto escolhido exige um salto considerável na tela (distância ao último ponto), desativando e reativando a caneta automaticamente para evitar rabiscar a conexão vazia.

### Desafio 4: Achatamento de Estruturas nas Paredes Invisíveis e Ajuste de Escala

**O Problema:** O plano cartesiano padrão do Turtlesim vai estritamente de `0.0` a `11.0`. No começo, o cachorro estava sendo renderizado muito grande, colidindo com as paredes e gerando linhas retas achatadas na base e na lateral esquerda da janela gráfica.

**A Solução:** Implementei três eixos de calibragem dinâmica:

- **Corte de Coordenadas em Pixel (`limite_x`):** Criei um descarte na `main.py` eliminando ruídos gerados no fundo esquerdo da foto para limpar a área inicial de desenho.
- **Redução de Escala Cartesiana (`escala`):** Reduzi e controlei o multiplicador escalar para `0.015`, fazendo o diâmetro total ocupado pelo cachorro caber de maneira segura dentro da tela do simulador.
- **Offsets de Transposição (`offset_x` e `offset_y`):** Em vez de centralizar na média geométrica pura que causava cortes, o nó do ROS adiciona dinamicamente `6.8` no eixo X e `5.8` no eixo Y antes de chamar o teleporte, deslocando o cachorro milimetricamente para fora do alcance de colisão das paredes e deixando o desenho centralizado e gigante na tela.

## Demonstração Prática em Vídeo

Assista ao vídeo explicativo clicando no link abaixo:
👉 [**Vídeo de Demonstração**](https://youtube.com/ou-drive-do-video)

## Conclusão

O projeto cumpre o objetivo de integrar visão computacional aplicada e robótica móvel. Partindo de uma imagem comum, o pipeline desenvolvido foi capaz de:
1. Isolar e refinar matrizes de bordas usando filtragem espacial matemática (convoluções de Blur e Sobel).
2. Filtrar ruídos de iluminação e fundo através de limiarização regional e análise de densidade local.
3. Converter a nuvem de pixels espalhados em coordenadas cartesianas discretas organizadas por proximidade espacial (Vizinho Mais Próximo).
4. Orquestrar a simulação no ROS 2 enviando comandos síncronos de teletransporte e controle de atuador (caneta liga/desliga).

O resultado final é um pacote ROS 2 modular, automatizado via arquivo Launch, que faz a tartaruga reproduzir fielmente os contornos do Bulldog Francês na tela sem colisões com as paredes e sem traçados caóticos, validando os conceitos de controle e processamento digital de sinais.
