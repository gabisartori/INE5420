# Trabalho 1.1 - Sistema básico com Window e Viewport
O objetivo dos exercícios propostos na Parte I é a construção, passo a passo, de um Sistema Gráfico Interativo capaz de representar, em perspectiva realista, objetos em #d como modelos de arame e também como superfícies bicúbicas renderizadas como malhas de curvas. Os exercícios são progressivos e construídos sobre os anteriores, o que significa que você necessita ter implementado o exercício anterior para poder implementar o atual, pois vai usar o código que produziu como ponto de partida para o novo exercício.
Neste seu primeiro trabalho, vamos lançar as bases do seu sistema, iniciando pela implementação de conceitos como window, viewport e display file. Para tanto, implemente o sistema básico de CG 2D contendo:
- Display file para 2D capaz de representar pontos, segmentos de retas e polígonos (listas de pontos interconectados), onde: Cada objeto possui um nome, tipo e uma lista de coordenadas de tamanho variável dependendo de seu tipo. Para facilitar sua vida mais tarde, chame o objeto polígono de wireframe;
- Transformação de viewport em 2D;
- Funções de panning/navegação 2D (movimentação da window);
Funções de Zooming (modificação do tamanho da window);

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
- Translações
- Escalonamento "natural" em torno do centro do objeto
- Rotações:
  - Em torno do centro do mundo
  - Em torno do centro do objeto
  - Em torno de um ponto arbitrário
Adicionalmente, o sistema deve permitir que o usuário defina uma cor de pintura para os objetos do mundo na criação deles. Esta é a cor apenas das retas.

# Trabalho 1.3 - Implemente ao sey SGI a capacidade de realizar rotações na windows.
Como implementa a rotação da window durante a navegação?
- Considere a window como um objeto gráfico qualquer e aplique a rotação de objetos sobre um ponto arbitrário à window em WC.
- Recakcyke as ciirdebadas di nybdi en OOC aokucabdi i algoritmo gerar descrição em ppc
  - Observe que o mundo será girado na direção contrária àquela que você girou a window.


