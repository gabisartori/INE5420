# Sistema Gráfico Interativo
## INE5420 - Computação Gráfica
Este repositório contém um Sistema Gráfico Interativo (SGI), capaz de representar e manipular objetos tridimensionais em modelo de arame.

## Execução
```
python src/main.py -i <input file> -o <output file>
```
Ambos argumentos são opcionais. Caso não haja arquivo de entrada, o SGI inciará sem nenhum objeto pré-criado e, caso não haja arquivo de saída, o SGI não tentará salvar seus objetos ao final da execução.

```
python3 src/main.py -h
```

Retorna a lista de funcionalidades do programa

## Controles
As utilidades do SGI são acessíveis por meio das seguintes entradas de instruções
- **Navegação:** `a,w,s,d` para se mover pare esquerda, cima, baixo e direita respectivamente. Além disso, clicar com o botão direito do mouse na tela irá centralizar a posição da janela no ponto clicado.
- **Zoom:** Scroll do mouse para cima para aumentar e baixo para diminuir
- **Inserir objetos:** Por padrão, cada clique na tela insere um ponto na posição clicada. O usuário pode apertar o botão "Build" para entrar em modo construção. Durante esse modo, os pontos inseridos serão armazenados para construir um objeto. Quando satisfeito, o usuário pode usar os botões "Lines" e "Polygon" para encerrar a construção. Lines consolidará o conjunto de linhas já pre-visualizado durante o modo de construção enquanto Polygon irá construir uma nova linha que liga o primeiro e último ponto construídos de forma a fechar um polígono.
- **Alterar propriedades dos objetos:** No canto direito inferior da interface, se encontra uma lista de todos os objetos armazenados no SGI, basta clicar no objeto desejado e usar os outros botões da interface para escolher qual atributo será alterado e qual será o novo valor.
- **Objetos de auxílio:** Ao apertar o botão do meio do mouse, pode-se ativar a visualização de linhas que facilitam a identificação do centro da tela e, também, um ponto que indica a origem do mundo.
- **Transformadas 2D:** Todas as transformadas exigem que um objeto esteja selecionado. 
- **Rotação de objetos:** Por padrão, um objeto será rotacionado em torno do seu próprio eixo. Para rotacionar ao longo de outro ponto ou em torno da origem do mundo(0,0), basta fornecê-lo no input "Around Point". Se nenhum valor for fornecido, o objeto será rotacionado em 15 graus.
- **Rotação da Window:** Quando ângulo específico não for inserido, rotaciona a janela em 5 graus.