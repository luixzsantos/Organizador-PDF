"""
organizador_automatico.py
Vigia uma pasta e, quando encontra um PDF com o mesmo nome de uma pasta que
JÁ EXISTE no destino, coloca o PDF dentro dela.
Ex.: "20666 - bauru.pdf"  ->  Destino/20666 - bauru/20666 - bauru.pdf
O programa NUNCA cria nem renomeia pastas. Se não houver pasta com o nome
idêntico, o PDF fica onde está.
Usa apenas bibliotecas nativas do Python (nada para instalar com pip).
"""

import configparser
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from tkinter import Tk, Button, Frame, Label, Listbox, Scrollbar, filedialog, messagebox

# Intervalo entre cada verificação da pasta (em milissegundos)
INTERVALO_MS = 2000
# De quanto em quanto tempo a lista de pastas do destino é relida (em segundos)
ATUALIZAR_PASTAS_S = 5

# config.ini fica ao lado do .exe (ou do .py) e guarda as pastas escolhidas
if getattr(sys, "frozen", False):
    PASTA_DO_PROGRAMA = Path(sys.executable).parent
else:
    PASTA_DO_PROGRAMA = Path(__file__).resolve().parent
ARQUIVO_CONFIG = PASTA_DO_PROGRAMA / "organizador_config.ini"


def ler_config() -> tuple[Path | None, Path | None]:
    """Lê as pastas salvas. Retorna (pasta_vigiada, pasta_destino) ou None se não houver."""
    config = configparser.ConfigParser()
    try:
        config.read(ARQUIVO_CONFIG, encoding="utf-8-sig")
    except configparser.Error:
        return None, None
    if not config.has_section("pastas"):
        return None, None
    vigiada = config["pastas"].get("vigiar", "").strip()
    destino = config["pastas"].get("destino", "").strip()
    return (Path(vigiada) if vigiada else None, Path(destino) if destino else None)


def salvar_config(vigiada: Path, destino: Path) -> None:
    config = configparser.ConfigParser()
    config["pastas"] = {"vigiar": str(vigiada), "destino": str(destino)}
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
        arquivo.write("; Pastas do Organizador Automático (pode editar no Bloco de Notas)\n")
        config.write(arquivo)


def caminho_livre(destino: Path) -> Path:
    """Se já existir um arquivo com esse nome, gera 'nome (1).pdf', 'nome (2).pdf'..."""
    if not destino.exists():
        return destino
    contador = 1
    while True:
        candidato = destino.with_name(f"{destino.stem} ({contador}){destino.suffix}")
        if not candidato.exists():
            return candidato
        contador += 1


def mapear_pastas(raiz: Path, ignorar: Path) -> dict[str, list[Path]]:
    """Lista todas as pastas dentro de 'raiz' (incluindo subpastas), agrupadas
    pelo nome em minúsculas (o Windows não diferencia maiúsculas)."""
    pastas: dict[str, list[Path]] = {}
    ignorar_str = os.path.normcase(str(ignorar))
    for atual, subpastas, _ in os.walk(raiz):
        # Não entra na pasta vigiada, caso ela fique dentro do destino
        subpastas[:] = [
            s for s in subpastas
            if os.path.normcase(os.path.join(atual, s)) != ignorar_str
        ]
        for nome in subpastas:
            pastas.setdefault(nome.strip().lower(), []).append(Path(atual) / nome)
    return pastas


class Organizador:
    def __init__(self, janela: Tk) -> None:
        self.janela = janela
        self.vigiada, self.destino = ler_config()
        # Guarda (tamanho, data de modificação) de cada arquivo na verificação anterior.
        # Só movemos quando o arquivo "parou de mudar", para não pegar um PDF
        # que ainda está sendo gravado.
        self.ultimo_estado: dict[Path, tuple[int, float]] = {}
        # Evita repetir o mesmo aviso a cada 2 segundos
        self.avisados: dict[Path, str] = {}
        # Cache da lista de pastas do destino
        self.pastas: dict[str, list[Path]] = {}
        self.pastas_lidas_em = 0.0

        # --- Monta a janela ---
        janela.title("Organizador Automático de PDF")
        janela.geometry("660x380")
        janela.minsize(480, 260)

        self.rotulo_pastas = Label(janela, justify="left", anchor="w")
        self.rotulo_pastas.pack(fill="x", padx=10, pady=(10, 4))

        botoes = Frame(janela)
        botoes.pack(fill="x", padx=10)
        Button(botoes, text="Alterar pastas", command=self.escolher_pastas).pack(side="left")
        Button(botoes, text="Abrir pasta de destino", command=self.abrir_destino).pack(side="left", padx=6)

        quadro_log = Frame(janela)
        quadro_log.pack(fill="both", expand=True, padx=10, pady=10)
        barra = Scrollbar(quadro_log)
        barra.pack(side="right", fill="y")
        self.log = Listbox(quadro_log, yscrollcommand=barra.set)
        self.log.pack(side="left", fill="both", expand=True)
        barra.config(command=self.log.yview)

        Label(
            janela,
            text="Dê ao PDF o mesmo nome de uma pasta existente e ele entra nela. "
            "Nenhuma pasta é criada. Feche esta janela para parar.",
            fg="gray",
        ).pack(pady=(0, 8))

        # Primeira vez (ou pastas apagadas): pede para escolher
        if not (self.vigiada and self.vigiada.is_dir() and self.destino and self.destino.is_dir()):
            janela.after(200, self.escolher_pastas)
        else:
            self.atualizar_rotulo()
            self.registrar("Vigiando a pasta...")

        janela.after(INTERVALO_MS, self.verificar)

    # --- Utilidades da interface ---
    def registrar(self, mensagem: str) -> None:
        hora = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{hora}] {mensagem}")
        self.log.see("end")

    def avisar_uma_vez(self, arquivo: Path, mensagem: str) -> None:
        if self.avisados.get(arquivo) != mensagem:
            self.avisados[arquivo] = mensagem
            self.registrar(f"{arquivo.name}: {mensagem}")

    def atualizar_rotulo(self) -> None:
        self.rotulo_pastas.config(
            text=f"Pasta vigiada (onde ficam os PDFs):  {self.vigiada}\n"
            f"Onde estão as pastas com os nomes:  {self.destino}"
        )

    def escolher_pastas(self) -> None:
        vigiada = filedialog.askdirectory(
            title="1/2 - Escolha a pasta onde ficam os PDFs (pasta VIGIADA)",
            initialdir=self.vigiada or Path.home() / "Downloads",
        )
        if not vigiada:
            if not self.vigiada:
                self.registrar("Nenhuma pasta escolhida. Clique em 'Alterar pastas'.")
            return
        destino = filedialog.askdirectory(
            title="2/2 - Escolha a pasta onde ESTÃO as pastas com os nomes (ex.: '20666 - bauru')",
            initialdir=self.destino or vigiada,
        )
        if not destino:
            return
        if Path(vigiada).resolve() == Path(destino).resolve():
            messagebox.showwarning(
                "Atenção", "A pasta vigiada e a de destino precisam ser diferentes."
            )
            return
        self.vigiada, self.destino = Path(vigiada), Path(destino)
        salvar_config(self.vigiada, self.destino)
        self.ultimo_estado.clear()
        self.avisados.clear()
        self.pastas_lidas_em = 0.0
        self.atualizar_rotulo()
        self.registrar("Pastas salvas. Vigiando...")

    def abrir_destino(self) -> None:
        if self.destino and self.destino.is_dir():
            os.startfile(self.destino)  # abre no Explorador de Arquivos

    # --- Lógica principal: roda a cada INTERVALO_MS ---
    def verificar(self) -> None:
        try:
            self.processar_pasta()
        finally:
            # Agenda a próxima verificação, mesmo se algo der errado nesta
            self.janela.after(INTERVALO_MS, self.verificar)

    def processar_pasta(self) -> None:
        if not (self.vigiada and self.destino and self.vigiada.is_dir() and self.destino.is_dir()):
            return

        estado_atual: dict[Path, tuple[int, float]] = {}
        for arquivo in self.vigiada.iterdir():
            # Etapa 1: só arquivos PDF
            if not (arquivo.is_file() and arquivo.suffix.lower() == ".pdf"):
                continue

            # Etapa 2: só mexe se o arquivo não mudou desde a última verificação
            try:
                info = arquivo.stat()
            except OSError:
                continue
            estado = (info.st_size, info.st_mtime)
            estado_atual[arquivo] = estado
            if self.ultimo_estado.get(arquivo) != estado:
                continue

            # Etapa 3: procura uma pasta JÁ EXISTENTE com o nome idêntico ao do PDF
            if time.monotonic() - self.pastas_lidas_em > ATUALIZAR_PASTAS_S:
                self.pastas = mapear_pastas(self.destino, self.vigiada)
                self.pastas_lidas_em = time.monotonic()
            encontradas = self.pastas.get(arquivo.stem.strip().lower(), [])
            if not encontradas:
                continue  # não há pasta com esse nome: o PDF fica onde está
            if len(encontradas) > 1:
                lista = ", ".join(str(p) for p in encontradas)
                self.avisar_uma_vez(arquivo, f"[AVISO] existe mais de uma pasta com esse nome, não movido: {lista}")
                continue
            pasta_final = encontradas[0]

            # Etapa 4: move para dentro da pasta (sem sobrescrever nada que já esteja lá)
            caminho_final = caminho_livre(pasta_final / arquivo.name)
            try:
                shutil.move(str(arquivo), str(caminho_final))
            except OSError as erro:
                # Normalmente: o PDF está aberto em outro programa. Tenta de novo depois.
                self.avisar_uma_vez(arquivo, f"[ERRO] não foi possível mover ({erro}). Tentando de novo...")
                continue

            estado_atual.pop(arquivo, None)
            self.avisados.pop(arquivo, None)
            extra = f" (já havia um igual; salvo como {caminho_final.name})" if caminho_final.name != arquivo.name else ""
            self.registrar(f"{arquivo.name}  →  {pasta_final}{extra}")

        self.ultimo_estado = estado_atual


if __name__ == "__main__":
    janela = Tk()
    Organizador(janela)
    janela.mainloop()
