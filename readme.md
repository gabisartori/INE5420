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
As utilidades do SGI são acessíveis por meio das seguintes entradas de instruções:
- **Display file:** O SGI recebe como argumentos caminhos para arquivos que podem ser usados para carregar objetos já existentes ou para armazenar os objetos criados durante a execução. Detalhes em [#Execução] .
- **Navegação:** 
  - Eixo X: `(a, d)`
  - Eixo Y: `(w,s)`
  - Eixo Z: `(q,e)`
- **Girar câmera:**
  - Eixo X: `(r, t)`
  - Eixo Y: `(f, g)`
  - Eixo Z: `(v, b)`
- **Zoom:** Scroll do mouse para cima para aumentar e baixo para diminuir.
- **Inserir objetos:**
  - **Ponto:** Cada clique no canva por padrão irá inserir um ponto;
  - **Linhas:** O botão *Build* faz com que os pontos inseridos por cliques formem linhas interconectadas;
  - **Polígonos:** No modo *Build*, após inserir os pontos desejados, clicar no botão *Polígono* vai unir o primeiro e último ponto inseridos para fechar o polígono;  
  - **Curvas:** No modo *Build*, colocar ao menos 4 pontos e clicar no botão *Curva* irá inserir curvas. Para escolher o tipo (Bezier ou B-Spline), acesse o menu de *Configurações -> Curvas*. Clicar no botão *Curva* sem estar no modo *Build* irá abrir uma janela para inserir os pontos textualmente. É possível alterar os pontos da curva no menu de *Propriedades* do objeto;
  - **Superfícies:** Ao clicar no botão de *Superficie*, é possível inserir os pontos de controle e gerar uma curva. É possível fazer alterações nos parâmetros de construção no menu de configurações;
- **Manipulação de objetos:** Na lista de objetos, clique no objeto cuja propriedade deseja alterar e siga as instruções condizentes.
  - **Translação:** Preencha os valores de deslocamento no eixo X e Y e aperte o botão *Deslocar* ;
  - **Rotações em torno:**
    - **do próprio eixo:** Com os campos X e Y vazios, e o campo de *ângulo* preenchido, aperte o botão *Girar*. Caso *ângulo* não seja um número válido, o objeto será girado em 15º;
    - **de um ponto específico:** Preencha os campos *X* e *Y* e proceda como na rotação em torno do próprio eixo;
    - **da origem:** Apenas aplicar a rotação em ponto específico no ponto (0, 0);
  - **Escalonamento natural:** Preencha o campo *Fator* e aperte o botão *Escalar* .
  - **Outras propriedades:** Detalhes como cor, grossura da linha, etc são acessíveis no menu pelo botão de *propriedades* ou clicando em cima do objeto na tabela com o botão direito do mouse;
- **Rotacionar Window:** Preencha o campo *ângulo* e aperte o botão *Rotacionar Window* .
- **Selecionar método de clipagem:** Na sessão *Métodos* do menu acima, selecione a opção desejada.
