# Trabalho 1.1 - Sistema básico com Window e Viewport
O objetivo dos exercícios propostos na Parte I é a construção, passo a passo, de um Sistema Gráfico Interativo capaz de representar, em perspectiva realista, objetos em 3d como modelos de arame e também como superfícies bicúbicas renderizadas como malhas de curvas. Os exercícios são progressivos e construídos sobre os anteriores, o que significa que você necessita ter implementado o exercício anterior para poder implementar o atual, pois vai usar o código que produziu como ponto de partida para o novo exercício.
Neste seu primeiro trabalho, vamos lançar as bases do seu sistema, iniciando pela implementação de conceitos como window, viewport e display file. Para tanto, implemente o sistema básico de CG 2D contendo:
- [-] Display file para 2D capaz de representar pontos, segmentos de retas e polígonos (listas de pontos interconectados), onde: Cada objeto possui um nome, tipo e uma lista de coordenadas de tamanho variável dependendo de seu tipo. Para facilitar sua vida mais tarde, chame o objeto polígono de wireframe;
- [-] Transformação de viewport em 2D;
- [-] Funções de panning/navegação 2D (movimentação da window);
- [-] Funções de Zooming (modificação do tamanho da window);

## Requisitos
- Use a linguagem python 3;
- Use uma biblioteca como Tkinter ou pyQt para implementar a GUI;
- Use apenas as diretivas de desenho de pontos e linhas para exibir os objetos no canvas, não use *drawPolygon*
- Caso a entrada das coordenadas não seja feita com cliques do mouse no canvas, o sistema de aceitar entradas no seguinte padrão: (x1, y1),(x2, y2)...
- A transformada de viewport não pode distorcer os objetos.

# Trabalho 1.2 - Implementação de Transformações 2D e Coordenadas Homogêneas
Neste trabalho você vai expandir o seu SGI para suportar as 3 transformações básicas e a rotação arbitrárias em 2D.
Para tanto, você vai criar uma rotina de transformação genérica que aceita uma matriz de transformação em coordenadas homogêneas e um objeto qualquer para ser transformado e devolve este objeto após a aplicação da matriz. Esta rotina nada mais é do que uma forma extremamente simples de se implementar um engine gráfico. Para alimentar esta rotina você deve criar um conjunto de rotinas de "preparo" da matriz de transformação que serão específicas para cada transformação.
Para poder aplicar uma transofrmação sobre um determinado objeto do mundo, você deve permitir ao usuário que selecione um dos objetos de seu mundo na lista de objetos, escolha a transformação que deseja aplicar e entre com os dados para esta transformação em uma interface para isso.
Alternativamente você pode implementar a interação com os objetos através do mouse: permita ao usuário usar o botão direito do mouse para abrir um menu de context que permite aplicar uma transformação ao objeto sob o mouse. Em 2D isso é muito fácil de se implementar, Mais tarde, quando estiver trabalhando em 3D, você verá que necessita de um algoritmo *buffer* de profundidade para saber qual é o objeto mais próximo ao mouse na tela.

## Requisitos
- [-] Translações
- [-] Escalonamento "natural" em torno do centro do objeto
- [-] Rotações:
  - [-]Em torno do centro do mundo
  - [-]Em torno do centro do objeto
  - [-]Em torno de um ponto arbitrário
- [-] Adicionalmente, o sistema deve permitir que o usuário defina uma cor de pintura para os objetos do mundo na criação deles. Esta é a cor apenas das retas.

# Trabalho 1.3 - Implemente ao seu SGI a capacidade de realizar rotações na windows.
Como implementa a rotação da window durante a navegação?
- Considere a window como um objeto gráfico qualquer e aplique a rotação de objetos sobre um ponto arbitrário à window em WC.
- Recalcule as coordenadas do mundo em PPC aplique o algoritmo gerar descrição em ppc
  - Observe que o mundo será girado na direção contrária àquela que você girou a window.

Acrescente ao seu sistema gráfico interativo a capacidade de ralizar rotações na window. Para tal:
- Altere a representação dos objetos do mundo para superotar representação em um dos sistemas de coordenadas vistos em aula: Sistema de coordenadas normalizada (SCN) ou sistema de coordenadas do plano de projeção. Agora a transformada de viewport é feita com estas coordenadas novas.
- Atualize a translação e zoom da window tendo em vista o novo sistema de coordenadas. A transição emp articular, tanto da window qunato dos objetos, deve levar em conta sempre o"para cima" do ponto de vista do usuário.
- Implemente a rotação implementando o algoritmo para gerar a descrição no sistema de coordenadas escolhido..
- Atualize a interface da aplicação para que o usuário possa rotacionar a window também. Como a rotação é sempre ao redor do centro da window, basta um campo para colocar o ângulo de rotação.
- Atenção as coordenadas dos objetos não podem se modificar com a rotação da window. Essa transformação ocorre ou na cache que seu display file possui ou na hora do desenho.

Cuidado para não quebrar as funcionalidades que já existem. Por exemplo, o que acontece ocm uma translação de um objeto quando a window está rotacionada em um ângulo qualquer? Em geral, o que deve ocorrer com a inclusao de um novo objeto quando a window se encontra fora de sua orientação padrão?

## Requisitos adicionais:
O código entregue com este trabalho deve ser capaz de ler/escrever um mundo em formato wavefront.obj file, devendo incluir todas as rotinas para leitura/escrita de arquivos .obj
Sugestões de modelagem:
- [ ] Crie uma classe "descritorOBJ" capaz de transcrever um objeto gráfico para o formato .obj, tomando seu nome, tipo, vertices e arestas.
- [ ] Assim você só precisa se preocupar com o cabeçalho do .obj. O resto se resolve através de um percurso do display file com seu descritor.

# Trabalho 1.4 - Clipping Incremente seu SGI para suportar clipping dos objetos no mundo
Implemente as principais técnicas de clipagem para windows retangulares vistas neste capítulo, utilizando clipagem de pontos e clipagem por C-S, L-B ou NLN para retas, de forma a integrá-las ao seu sistema gráfico de maneira que a transformada de viewport seja aplicada apenas aos objetos resultantes do clipping.

No one will ever believe you

Para ter certeza de que a clipagem está funcionando e não é o algoritmo de clipagem da interface que está usando, faça sua viewport ser menor do que o seu objeto de desenho.

## Requisitos
Clipagem:
- Clipagem de pontos
- 2 técnicas distintas de clipagem de retas, que o usuário pode escolher qual usar pela interface
- Clipagem de polígonos, uma técnica à escolha.
Representação:
- Faça sua viewport ser menor que o objeto de desenho para facilitar visualização da clipagem
- Estenda seu SGi para suportar polígonos preenchidos, utilizando as primitivas da ferramenta que estiver utilizando, o usuário escolhe se o polígono é preenchido ou arame.

# 1.5 - Implemente curvas em 2d usando blending functions
Implemente a curva de hermite ou bezier como mais um objeto gráfico de seu sistema
- Um objeto curva2d poderá conter uma ou mais curvas com continuidade no mínimo G(0)
- Crie uma interface para entrar com estes dados no padrão (x1,y1),(x2,y2)... Deve ser possível informar um número infinito de pontos para implementar continuidade.
- Implemente clipping para esta curva utilizando o método descrito em aula

# 1.6 - Implemente no seu programa gráfico B-splines utilizando forward differences
O usuário deve inserir no mínimo 4 pontos de controle

# 1.7 - Implementação da classe ponto3d, objetos3d e projeção paralela ortogonal
- Implemente uma classe ponto 3d capaz de realizar as 3 transformações básicas
- Implemente uma classe objeto3d para representar um modelo de arame com as seguintes característas:
 - Possui uma lista de segmentos de reta constituídos por um par de pontos3d
 - É capaz de realizar as 3 operações básicas e também a rotação em torno de um eixo arbitrário
- Implemente as operações de navegação da window no espaço 3d
- Implemente o que foi visto hoje sobre projeção paralela ortogonal
- O primeiro ponto pode ser o VRP
- Lembre-se que ao final do algoritmo VPN, deve ser (0, 0, 1). Ou seja, paralelo ao eixo.

# 1.8 - Implementação de projeção em perspectiva
Implemente projeção em perspectiva realizando clipping 2d.

## Requisitos
- Tomar uma cena composta por um conjunto de pelo menos 2 objetos 3d na forma de modelos de arame armazenados no display file e mostrá-los em perspectiva.
- Variar a posição do centro de projeção, permitindo distorções do tipo grande angular e teleobjetiva
- Carregar pelo menos um modelo de arame de paralelepípedo em formato .obj para mostrar em perspectiva

# 1.9 - Desenhando superfícies bicúbicas de bézier
- Estenda seu SGI para representar superfícies 3d através de suas matrizes de geometria
- Cada superfície pode ser representada por uma lista de matriz, cada matriz representando um "retalho"
- Crie uma tela de entrada de dados onde você pode entrar com conjuntos de pontos de controle, 16 a 16, no mesmo padrão dos outros objetos com as linhas da matriz separadas por ";"
- Carregue uma superfície composta por pelo menos 3 retalhos
- Clipping 2d

# 1.10 - Implementação de superfícies bicúbicas utilizando diferenças adiante
- O SGI automaticamente fará a subdivisão em submatriz, que serão desenhadas pelo método das forwad differences conforme explicado em aula. Você pode utilizar o código-exemplo em processing disponibilizado pelo professor para se basear, lembrando que o algoritmo fornecido por foley & van dam possui dois erros.
