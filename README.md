# Organizador Automático de PDF

Coloca cada PDF dentro da pasta que tem o **mesmo nome** que ele.

Exemplo: renomeie `20666 - bauru.pdf` para o nome de uma pasta que já existe, como `20666 - bauru`, e ele é movido para dentro dela em cerca de 2 segundos.

Não cria, não renomeia e não apaga pastas.

## Como usar

1. Execute `OrganizadorAutomatico.exe` (não precisa instalar Python).
2. Na primeira vez, escolha:
   - a pasta onde ficam os PDFs (pasta vigiada);
   - a pasta onde estão as pastas com os nomes (destino).
3. Deixe a janela aberta. Renomeie o PDF com o nome exato da pasta.
4. Para parar, feche a janela.

## Regras

- Se não existir pasta com o nome do PDF, ele fica onde está.
- Maiúsculas e minúsculas não importam (`joao.pdf` entra em `Joao`).
- Se já houver um PDF igual na pasta, o novo é salvo como `nome (1).pdf`.
- Se houver mais de uma pasta com o mesmo nome, o PDF não é movido e um aviso aparece.
- Se o PDF estiver aberto em outro programa, o programa tenta de novo até conseguir.
- PDFs que já estavam na pasta vigiada quando o programa abriu são ignorados, até serem renomeados.

## Trocar as pastas

Clique em **Alterar pastas** na janela do programa. A escolha é salva em `organizador_config.ini`, ao lado do `.exe`.

## Abrir junto com o Windows (opcional)

1. Botão direito no `.exe` → **Criar atalho**.
2. Pressione `Win + R`, digite `shell:startup` e pressione Enter.
3. Mova o atalho para a pasta que abrir.

## Gerar o .exe a partir do código

Requer Python 3.10 ou mais novo.

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name OrganizadorAutomatico organizador_automatico.py
```

O executável é gerado em `dist\OrganizadorAutomatico.exe`.

## Arquivos

| Arquivo | Descrição |
|---|---|
| `organizador_automatico.py` | Código-fonte do programa |
| `.gitignore` | Arquivos que não entram no repositório |
| `README.md` | Este arquivo |

## Requisitos

- Windows 10 ou 11 (64 bits), para o `.exe`.
- Python 3.10+, apenas para rodar o `.py` ou gerar o `.exe`. Usa somente bibliotecas nativas (`tkinter`, `shutil`, `pathlib`).
