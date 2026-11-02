"""
app.py - "criativa ferramentas"

Como as peças conversam (de cima para baixo):

    App ──────────────► cria e posiciona os dois painéis
     │
     ├─ FrameDaEsquerda   só tem botões. Quando um botão é clicado, ele chama
     │                    uma função que o App entregou (o dicionário `comandos`).
     │                    Ele NÃO sabe que existe tabela nem PDF.
     │
     ├─ FrameDaDireita    título, informações e a tabela (tksheet).
     │                    Sabe ler/escrever os dados da tabela, mas não sabe de PDF.
     │
     └─ pdf_listas        gera e lê PDF. Não sabe que existe interface.

    O App é o "maestro": pega o DataFrame da direita e entrega ao pdf_listas
    (salvar), ou pega o DataFrame do pdf_listas e entrega à direita (abrir).
"""

import re
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd
from tksheet import Sheet

from pdf_listas import gerar_pdf, ler_pdf

# ---------------------------------------------------------------- constantes
MAX_COLUNAS = 5  # contando a coluna ID
CABECALHOS_PADRAO = ["ID", "Código", "Nome", "Qtd", "Info"]
LARGURAS = [50, 130, 260, 70, 230]  # largura inicial de cada coluna, em px
LINHAS_INICIAIS = 8

COR_FUNDO = "#100c08"
COR_PAINEL = "#1c1814"
COR_BORDA = "#3a3228"
COR_DESTAQUE = "#ce4c11"
COR_DESTAQUE_HOVER = "#a33d0e"
COR_ROTULO = "#5e4f52"
COR_BOTAO = "#2e2822"
COR_BOTAO_HOVER = "#3a3228"
COR_TEXTO = "#f2e9e1"
COR_TEXTO_SUAVE = "#8a7f73"
RAIO = 12

# cores da tabela (tksheet) combinando com o resto do app
TEMA_TABELA = {
    "table_bg": COR_PAINEL,
    "table_fg": COR_TEXTO,
    "table_grid_fg": COR_BORDA,
    "table_selected_cells_border_fg": COR_DESTAQUE,
    "table_selected_cells_bg": "#3a2418",
    "table_selected_cells_fg": COR_TEXTO,
    "table_selected_rows_border_fg": COR_DESTAQUE,
    "table_selected_rows_bg": "#3a2418",
    "table_selected_rows_fg": COR_TEXTO,
    "header_bg": "#2a231d",
    "header_fg": COR_DESTAQUE,
    "header_grid_fg": COR_BORDA,
    "header_border_fg": COR_BORDA,
    "header_selected_cells_bg": "#4a2e1e",
    "header_selected_cells_fg": COR_TEXTO,
    "header_selected_columns_bg": "#4a2e1e",
    "header_selected_columns_fg": COR_TEXTO,
    "frame_bg": COR_PAINEL,
}

ctk.set_appearance_mode("dark")


# ------------------------------------------------------------- painel esquerdo
class FrameDaEsquerda(ctk.CTkFrame):
    def __init__(self, master, comandos, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_propagate(False)  # agora o width/height valem
        self.grid_columnconfigure(0, weight=1)  # botões ocupam a largura toda
        self.grid_rowconfigure(5, weight=1)  # linha "mola": empurra o PDF para baixo

        self.label = ctk.CTkLabel(
            self,
            text="Menu de ferramentas criativa",
            text_color=COR_DESTAQUE,
            fg_color=COR_ROTULO,
            corner_radius=30,
            wraplength=170,  # quebra o texto: evita cortar no Ubuntu
        )
        self.label.grid(row=0, column=0, padx=20, pady=20)

        self.botao_nova = self._criar_botao("Nova lista", comandos["nova_lista"], 1)
        self.botao_adicionar = self._criar_botao(
            "Adicionar linha", comandos["adicionar_linha"], 2
        )
        self.botao_remover = self._criar_botao(
            "Remover linha(s)", comandos["remover_linhas"], 3
        )
        self.botao_abrir = self._criar_botao("Abrir PDF", comandos["abrir_pdf"], 4)

        self.botao_pdf = self._criar_botao(
            "Salvar em PDF", comandos["salvar_pdf"], 6, destaque=True
        )
        self.botao_pdf.grid_configure(pady=(6, 20))

    def _criar_botao(self, texto, comando, linha, destaque=False):
        botao = ctk.CTkButton(
            self,
            text=texto,
            command=comando,  # sem parênteses: roda no clique, não na criação
            height=36,
            corner_radius=RAIO,
            fg_color=COR_DESTAQUE if destaque else COR_BOTAO,
            hover_color=COR_DESTAQUE_HOVER if destaque else COR_BOTAO_HOVER,
            text_color=COR_TEXTO,
        )
        botao.grid(row=linha, column=0, padx=20, pady=6, sticky="ew")
        return botao


# -------------------------------------------------------------- painel direito
class FrameDaDireita(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # a tabela absorve o espaço que sobra

        self.entrada_titulo = ctk.CTkEntry(
            self,
            placeholder_text="Título da lista",
            height=40,
            corner_radius=RAIO,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=COR_FUNDO,
            border_color=COR_BORDA,
            text_color=COR_TEXTO,
        )
        self.entrada_titulo.grid(row=0, column=0, padx=20, pady=(20, 8), sticky="ew")

        self.entrada_info = ctk.CTkEntry(
            self,
            placeholder_text="Informações curtas (responsável, setor, observação...)",
            height=34,
            corner_radius=RAIO,
            fg_color=COR_FUNDO,
            border_color=COR_BORDA,
            text_color=COR_TEXTO,
        )
        self.entrada_info.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="ew")

        self.tabela = Sheet(
            self,
            headers=list(CABECALHOS_PADRAO),
            data=[[""] * len(CABECALHOS_PADRAO) for _ in range(LINHAS_INICIAIS)],
            theme="dark",
            show_row_index=False,  # o ID já é uma coluna nossa
            show_top_left=False,
            height=400,
        )
        self.tabela.set_options(**TEMA_TABELA)
        self.tabela.enable_bindings(
            "single_select",
            "drag_select",
            "select_all",
            "row_select",
            "column_select",
            "column_width_resize",
            "double_click_column_resize",
            "arrowkeys",
            "right_click_popup_menu",
            "rc_select",
            "copy",
            "cut",
            "paste",
            "delete",
            "undo",
            "edit_cell",
            "edit_header",  # duplo clique no cabeçalho para renomear a coluna
        )
        self.tabela.readonly_columns(0)  # ID é automático, não editável
        self._ajustar_larguras()
        self.tabela.grid(row=2, column=0, padx=20, pady=0, sticky="nsew")

        self.status = ctk.CTkLabel(
            self,
            text="Dê dois cliques no cabeçalho para renomear uma coluna.",
            text_color=COR_TEXTO_SUAVE,
            anchor="w",
        )
        self.status.grid(row=3, column=0, padx=20, pady=(8, 14), sticky="ew")

        self._renumerar()

    # --- pequenos auxiliares
    def _ajustar_larguras(self):
        for i in range(self.tabela.get_total_columns()):
            self.tabela.column_width(column=i, width=LARGURAS[min(i, len(LARGURAS) - 1)])

    def _renumerar(self):
        """Reescreve a coluna ID como 1, 2, 3... (a tabela é a dona dos dados)."""
        total = self.tabela.get_total_rows()
        self.tabela.set_column_data(0, values=[str(i + 1) for i in range(total)])

    def mostrar_status(self, texto):
        self.status.configure(text=texto)

    # --- título e informações
    def obter_titulo(self):
        return self.entrada_titulo.get().strip()

    def obter_info(self):
        return self.entrada_info.get().strip()

    # --- dados da tabela
    def obter_dataframe(self):
        """Lê a tabela e devolve um DataFrame (sem as linhas totalmente vazias)."""
        cabecalhos = []
        for i, h in enumerate(self.tabela.headers()):
            h = str(h).strip()
            cabecalhos.append(h if h else f"Coluna {i + 1}")

        linhas = [[str(c).strip() for c in linha] for linha in self.tabela.get_sheet_data()]
        linhas = [linha for linha in linhas if any(linha[1:])]  # ignora o ID
        for numero, linha in enumerate(linhas, start=1):
            linha[0] = str(numero)
        return pd.DataFrame(linhas, columns=cabecalhos)

    def carregar_dataframe(self, df, titulo="", info=""):
        """Joga um DataFrame na tabela (usado ao abrir um PDF)."""
        self.tabela.set_sheet_data(df.values.tolist(), reset_col_positions=False)
        self.tabela.headers([str(c) for c in df.columns])
        self._ajustar_larguras()
        self._renumerar()
        self.entrada_titulo.delete(0, "end")
        self.entrada_titulo.insert(0, titulo)
        self.entrada_info.delete(0, "end")
        self.entrada_info.insert(0, info)

    def limpar(self):
        self.carregar_dataframe(
            pd.DataFrame(
                [[""] * len(CABECALHOS_PADRAO) for _ in range(LINHAS_INICIAIS)],
                columns=CABECALHOS_PADRAO,
            )
        )

    def tem_dados(self):
        """True se o usuário já digitou alguma coisa (para pedir confirmação)."""
        if self.obter_titulo() or self.obter_info():
            return True
        return any(any(linha[1:]) for linha in self.tabela.get_sheet_data())

    def adicionar_linha(self):
        self.tabela.insert_row()  # sem argumentos: acrescenta no fim
        self._renumerar()
        ultima = self.tabela.get_total_rows() - 1
        self.tabela.select_cell(ultima, 1)
        self.tabela.see(ultima, 1)

    def remover_linhas_selecionadas(self):
        """Remove as linhas selecionadas; devolve quantas foram removidas."""
        linhas = sorted(self.tabela.get_selected_rows(get_cells_as_rows=True))
        if not linhas:
            return 0
        self.tabela.delete_rows(linhas)
        self._renumerar()
        return len(linhas)


# ------------------------------------------------------------------------- app
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("criativa ferramentas")
        self.geometry("1100x650")
        self.minsize(900, 500)
        self.configure(fg_color=COR_FUNDO)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # esquerda: largura fixa
        self.grid_columnconfigure(1, weight=1)  # direita: ocupa o resto

        # o App entrega ao menu as funções que cada botão deve chamar
        comandos = {
            "nova_lista": self.nova_lista,
            "adicionar_linha": self.adicionar_linha,
            "remover_linhas": self.remover_linhas,
            "abrir_pdf": self.abrir_pdf,
            "salvar_pdf": self.salvar_pdf,
        }

        # um único frame de cada lado (sem duplicata na mesma célula do grid)
        self.frame_esquerda = FrameDaEsquerda(
            master=self,
            comandos=comandos,
            width=230,
            fg_color=COR_PAINEL,
            corner_radius=RAIO,
            border_width=0,
            border_color=COR_BORDA,
        )
        self.frame_esquerda.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="ns")

        self.frame_direita = FrameDaDireita(
            master=self,
            fg_color=COR_PAINEL,
            corner_radius=RAIO,
            border_width=0,
            border_color=COR_BORDA,
        )
        self.frame_direita.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")

        # atalhos de teclado
        self.bind("<Control-s>", lambda evento: self.salvar_pdf())
        self.bind("<Control-o>", lambda evento: self.abrir_pdf())

    # --- ações dos botões
    def nova_lista(self):
        if self.frame_direita.tem_dados() and not messagebox.askyesno(
            "Nova lista", "A lista atual será apagada. Continuar?"
        ):
            return
        self.frame_direita.limpar()
        self.frame_direita.mostrar_status("Nova lista criada.")

    def adicionar_linha(self):
        self.frame_direita.adicionar_linha()

    def remover_linhas(self):
        removidas = self.frame_direita.remover_linhas_selecionadas()
        if removidas:
            self.frame_direita.mostrar_status(f"{removidas} linha(s) removida(s).")
        else:
            self.frame_direita.mostrar_status(
                "Selecione uma linha (clique no número ou na célula) para remover."
            )

    def salvar_pdf(self):
        direita = self.frame_direita
        df = direita.obter_dataframe()  # 1) pega os dados da tabela
        if df.empty:
            messagebox.showwarning("Lista vazia", "Preencha pelo menos uma linha.")
            return

        titulo = direita.obter_titulo()
        nome_sugerido = re.sub(r'[\\/:*?"<>|]+', "", titulo).strip() or "lista"
        caminho = filedialog.asksaveasfilename(
            title="Salvar lista em PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"{nome_sugerido}.pdf",
        )
        if not caminho:  # usuário cancelou
            return

        try:
            gerar_pdf(df, caminho, titulo, direita.obter_info())  # 2) entrega ao PDF
        except Exception as erro:  # ex.: arquivo aberto em outro programa
            messagebox.showerror("Erro ao salvar", str(erro))
            return
        direita.mostrar_status(f"{len(df)} item(ns) salvos em {caminho}")

    def abrir_pdf(self):
        direita = self.frame_direita
        caminho = filedialog.askopenfilename(
            title="Abrir lista em PDF", filetypes=[("PDF", "*.pdf")]
        )
        if not caminho:
            return
        if direita.tem_dados() and not messagebox.askyesno(
            "Abrir PDF", "A lista atual será substituída. Continuar?"
        ):
            return

        try:
            titulo, info, df = ler_pdf(caminho)  # 1) PDF vira DataFrame
            df = self._preparar_colunas(df)
        except Exception as erro:
            messagebox.showerror("Não consegui abrir", str(erro))
            return
        direita.carregar_dataframe(df, titulo, info)  # 2) entrega à tabela
        direita.mostrar_status(f"{len(df)} item(ns) carregados de {caminho}")

    @staticmethod
    def _preparar_colunas(df):
        """Garante que a primeira coluna é o ID e que cabem no máximo MAX_COLUNAS."""
        if str(df.columns[0]).strip().lower() != "id":
            df.insert(0, "ID", [str(i + 1) for i in range(len(df))])
        if df.shape[1] > MAX_COLUNAS:
            raise ValueError(
                f"Este PDF tem {df.shape[1]} colunas (contando o ID). "
                f"O app aceita até {MAX_COLUNAS}."
            )
        return df


if __name__ == "__main__":
    app = App()
    app.mainloop()
