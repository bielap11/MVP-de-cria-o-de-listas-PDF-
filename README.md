# MVP-de-cria-o-de-listas-PDF-
um pequeno projeto que desenvolvi enquanto trabalhava na loja criativa

nesse projeto eu decidi utilizar somente python puramente para que ficasse o mais simples de manter e utilizar futuramente. 
_____________________________________________________________________
|
|
|
_______________________________
quais bibliotecas foram usadas?
Pandas customtkinter pdf reader tkinter e o principal que faz a magica acontecer eu utilizei tksheet para mexer com tabelas 
_______________________________

O que o app faz?
_________________
Menu à esquerda com Nova lista, Adicionar linha, Remover linha(s), Abrir PDF e Salvar em PDF no fundo.
Título e informações curtas no topo da direita, e a tabela tksheet com 5 colunas: ID, Código, Nome, Qtd e Info.
O ID é automático e não editável. Dois cliques no cabeçalho renomeiam a coluna.
O PDF sai com título, informações, data e uma caixinha vazia no fim de cada linha.
Abrir PDF lê de volta um PDF gerado pelo app. Se o PDF tiver mais de 5 colunas, o app avisa em vez de quebrar.
Ctrl+S salva e Ctrl+O abre.
Como as peças conversam
FrameDaEsquerda só tem botões. O App entrega a ele as funções de cada botão, então ele não sabe que existe tabela nem PDF.
FrameDaDireita guarda título, informações e tabela, e sabe entregar e receber um DataFrame.
pdf_listas.py gera e lê PDF e não sabe que existe interface.
O App é o intermediário: ao salvar, pega o DataFrame da direita e entrega ao pdf_listas. Ao abrir, faz o caminho contrário.

Para estudar, leia nesta ordem: pdf_listas.py, FrameDaEsquerda, FrameDaDireita e App. O comentário no topo do app.py resume esse fluxo.
