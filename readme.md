# Sistema Gráfico Interativo
## INE5420 - Computação Gráfica
Este repositório contém um Sistema Gráfico Interativo (SGI), capaz de representar e manipular objetos tridimensionais em modelo de arame.

## Execução
O programa recebe como argumento um arquivo .obj com a lista de objetos a serem inicializados. Caso nenhum argumento seja passado, ou o arquivo não seja encontrado, o SGI executa sem nenhum objeto pré-inicializado.
```
python3 src/main.py <filepath>
```

## Controles
As utilidades do SGI são acessíveis por meio das seguintes entradas de instruções
- **Navegação:** `a,w,s,d` para se mover pare esquerda, cima, baixo e direita respectivamente. Além disso, clicar com o botão direito do mouse na tela irá centralizar a posição da janela no ponto clicado.
- **Zoom:** Scroll do mouse para cima para aumentar e baixo para diminuir
- **Inserir objetos:** Por padrão, cada clique na tela insere um ponto na posição clicada. O usuário pode apertar o botão "Build" para entrar em modo construção. Durante esse modo, os pontos inseridos serão armazenados para construir um objeto. Quando satisfeito, o usuário pode usar os botões "Lines" e "Polygon" para encerrar a construção. Lines consolidará o conjunto de linhas já pre-visualizado durante o modo de construção enquanto Polygon irá construir uma nova linha que liga o primeiro e último ponto construídos de forma a fechar um polígono.
- **Alterar propriedades dos objetos:** No canto direito inferior da interface, se encontra uma lista de todos os objetos armazenados no SGI, basta clicar no objeto desejado e usar os outros botões da interface para escolher qual atributo será alterado e qual será o novo valor.
- **Objetos de auxílio:** Ao apertar o botão do meio do mouse, pode-se ativar a visualização de linhas que facilitam a identificação do centro da tela e, também, um ponto que indica a origem do mundo.