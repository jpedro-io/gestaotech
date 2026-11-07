# COMO RODAR NO PC (Windows) — Gestão Tech

Passo a passo do zero até o site abrindo no navegador e o banco no Neon.

---

## 1. O que instalar no PC

| Programa | Para que serve | Link |
|---|---|---|
| **Python 3.12** (marque “Add python.exe to PATH” na instalação) | roda o site | https://www.python.org/downloads/ |
| **LibreOffice** (versão completa, não o “LibreOffice Portable”) | converte o DOCX do certificado em PDF | https://pt-br.libreoffice.org/download/ |
| **VS Code** | editor + terminal | https://code.visualstudio.com/ |
| Extensão **Python** (da Microsoft) no VS Code | atalho para rodar/escolher o interpretador | aba Extensões → “Python” |

O **ZIP** `gestao-tech-certificados.zip` é o projeto. Não precisa instalar Git nem Docker.

> LibreOffice é obrigatório: sem ele o site até abre, mas o botão “Baixar PDF” dá erro 500.
> No Windows ele fica em `C:\Program Files\LibreOffice\program\soffice.exe`, que já está no PATH
> por padrão. Para conferir, no terminal: `soffice --version`.

---

## 2. Descompactar e abrir no VS Code

1. Descompacte o ZIP em um caminho **sem espaços e sem acento** — ex.: `C:\projetos\gestao-tech`.
2. VS Code → **File → Open Folder** → escolha a pasta `gestao-tech`.
3. Abra o terminal integrado: **Ctrl + '** (ou menu Terminal → New Terminal).
   Confirme que está na pasta certa:

```powershell
pwd     # deve mostrar ...\gestao-tech
```

---

## 3. Criar o ambiente e instalar as dependências

```powershell
py -m venv .venv
```

Ativar o ambiente — **escolha a opção que funcionar** (a 1 é a mais garantida):

**Opção 1 — Prompt de Comando (cmd), sem depender de política do PowerShell**
```powershell
.\ativar.bat
```
(o arquivo `ativar.bat` vem no projeto e chama `.venv\Scripts\activate.bat`)

Se preferir abrir uma janela cmd já ativada: `start ativar.bat cmd`

**Opção 2 — cmd aberto à mão**
```powershell
cmd
.venv\Scripts\activate.bat
```
(funciona sem `Set-ExecutionPolicy`; o `cmd` é o terminal clássico do Windows)

**Opção 3 — PowerShell, liberando a política de execução uma vez**
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```
Se der `CommandNotFoundException` mesmo assim, o `.venv` não foi criado nessa pasta:
`dir .venv\Scripts` deve listar `activate.bat`, `Activate.ps1`, `python.exe`.
Se a pasta `.venv` não existir, o `python -m venv .venv` acima falhou (veja o erro dele).

Depois de ativado, a linha do terminal começa com `(.venv)` e aí sim:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> O nome da pasta do ambiente já está no `.gitignore`. Sempre que abrir o terminal de novo,
> reative com `.\.\ativar.bat` (ou `.\.venv\Scripts\Activate.ps1` no PowerShell). Quando a
> ativação dá certo, a linha do terminal começa com `(.venv)` — é esse o sinal de que funcionou.

---

## 3b. Opção que nunca falha: rodar sem ativar o ambiente

Não precisa ativar nada. Chame o Python de dentro do `.venv` pelo caminho completo:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Daí em diante, troque `python manage.py ...` por `.\.venv\Scripts\python.exe manage.py ...`:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_oficinas
.\.venv\Scripts\python.exe manage.py runserver
```

Para encurtar, guarde o caminho numa variável do PowerShell:

```powershell
$py = ".\.venv\Scripts\python.exe"
& $py manage.py runserver
```

Se `py` não for reconhecido, use `python`; se nenhum dos dois for reconhecido, o Python não está
instalado (ou não está no PATH) — instale de https://www.python.org/downloads/ marcando
**“Add python.exe to PATH”** e **feche/reabra o VS Code**.

---

## 3c. “python não é reconhecido”, mas o Python já está instalado

Acontece quando o instalador **não marcou “Add python.exe to PATH”** (ou quando quem instalou
foi outro usuário do Windows). Diagnosticar, nesta ordem:

```powershell
py --version
```
1. **Se `py` funcionar** (ex.: `Python 3.12.7`) — não precisa reinstalar nada. Use `py` no lugar
   de `python`:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe manage.py runserver
   ```
2. **Se `py` também não for reconhecido**, descubra onde o Python foi instalado:
   ```powershell
   Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Directory
   Get-ChildItem "C:\Program Files" -Filter "Python*" -Directory
   ```
   Se aparecer algo como `...\Programs\Python\Python312`, use o caminho completo:
   ```powershell
   & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
   ```
3. **Se não aparecer nada**, aí sim reinstale: abra o instalador do python.org → **Modify**
   (ou *Repair*) → marque **“Add Python to environment variables”** → Install.
   Depois **feche e reabra o VS Code** (o terminal só lê o PATH novo ao abrir).

### Se o `python` abre a Microsoft Store
O Windows tem um atalho falso de `python.exe`. Desligue em:
**Configurações → Aplicativos → Configurações avançadas de aplicativos → Aliases de execução
de aplicativo** → desative **python.exe** e **python3.exe**. Reabra o terminal.

---

## 3d. Sua versão do Python é a 3.14

O projeto roda nela, desde que a **Django seja 5.2.8 ou mais nova** (o suporte ao Python 3.14
entrou nessa versão). O `requirements.txt` já pede `Django>=5.2.8,<6.0`, então basta instalar
normalmente:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m django --version
```

A última linha deve mostrar `5.2.x` (x ≥ 8). Se mostrar `5.1` ou menos, o pacote foi instalado
antes: rode o `pip install -r requirements.txt` de novo dentro do `.venv`.

> No Windows, se o `pip` reclamar de compilador (raro, com `psycopg[binary]` e `qrcode[pil]`
> já há pacotes prontos para 3.14), atualize o pip antes — é o primeiro comando do bloco acima.

---

## 4. Configurar o `.env`

```powershell
copy .env.example .env
```

Abra o `.env` no VS Code e ajuste:

```ini
DATABASE_URL=          # vazio = SQLite local. Cole a do Neon quando for usar o Postgres.
SECRET_KEY=uma-string-longa-e-aleatoria
DEBUG=1
ALLOWED_HOSTS=*
SITE_URL=http://localhost:8000
DATA_LIBERACAO=2000-01-01     # em produção: 2026-11-06
CPF_PEPPER=troque-por-uma-string-longa
```

Para gerar uma `SECRET_KEY`/`CPF_PEPPER` de verdade:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

> **Não troque o `CPF_PEPPER`** depois de cadastrar participantes: o hash do CPF deixaria de
> bater e ninguém acharia o próprio certificado.

---

## 5. Criar o banco e popular

Com `DATABASE_URL` vazio (SQLite local, mais rápido para testar):

```powershell
python manage.py migrate
python manage.py seed_oficinas
python manage.py criar_superuser
python manage.py seed_participantes --csv pessoas_exemplo.csv
```

Saída esperada:

```
Oficinas: 7 criada(s), 0 atualizada(s), 7 no banco.
CSV: 3 criada(s), 0 atualizada(s), 0 ignorada(s). Total no banco: 3.
```

Para usar o **Neon** em vez do SQLite, cole a connection string **pooled** no `.env`
(`postgresql://usuario:senha@ep-xxxx-pooler...neon.tech/neondb?sslmode=require`) e repita
os mesmos comandos — eles criam as tabelas e populam o banco na nuvem.

Depois, para cada equipe que mandar o CSV (`nome,cpf,oficina,papel`):

```powershell
python manage.py seed_participantes --csv equipe_coda.csv
```

Rodar o mesmo arquivo de novo **não duplica** — só atualiza.

---

## 6. Rodar o site

```powershell
python manage.py runserver
```

Abra <http://127.0.0.1:8000/>. O admin fica em <http://127.0.0.1:8000/admin/>.
Para parar, **Ctrl + C** no terminal.

Teste rápido de que o PDF funciona: busque `João Pedro Campos Rocha` / `529.982.247-25`
e clique em **Baixar PDF**. A primeira geração leva alguns segundos (o LibreOffice abre em
segundo plano).

---

## 7. Comandos do dia a dia

| Situação | Comando |
|---|---|
| reativar o ambiente | `.\.venv\Scripts\Activate.ps1` |
| rodar o site | `python manage.py runserver` |
| ver o que está no banco | `python manage.py exportar_participacoes` |
| exportar para planilha | `python manage.py exportar_participacoes --saida participantes.csv` |
| gerar códigos que faltam | `python manage.py gerar_codigos` |
| criar outro acesso ao admin | `python manage.py criar_superuser` |
| conferir se há erro de configuração | `python manage.py check` |

---

## 8. Problemas comuns

| Mensagem | Causa e solução |
|---|---|
| `python não é reconhecido` | Python não entrou no PATH. Reinstale marcando “Add python.exe to PATH” ou use `py` no lugar de `python`. |
| `Activate.ps1 : O termo ... não é reconhecido` | O PowerShell não achou o arquivo: ou o `.venv` não existe nessa pasta, ou a política bloqueia o script. Use `.\ativar.bat` (Opção 1) — não depende de política nenhuma. |
| `Activate.ps1 não pode ser carregado` | Rode `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e abra o terminal de novo. |
| `soffice: comando não encontrado` / erro 500 no PDF | LibreOffice não instalado ou fora do PATH. Reinstale com a opção padrão, ou adicione `C:\Program Files\LibreOffice\program` ao PATH e reabra o VS Code. |
| PDF sai com letra diferente do modelo | As fontes de `fontes/` não estão instaladas. Selecione os `.ttf`, clique com o botão direito → **Instalar para todos os usuários**, e reinicie o LibreOffice/site. |
| `DisallowedHost` ao abrir no navegador | `ALLOWED_HOSTS` no `.env` deve ser `*` em desenvolvimento. |
| `connection refused` / timeout no Neon | `DATABASE_URL` errada, sem `?sslmode=require`, ou projeto Neon suspenso (abra o console do Neon para reativar). |
| “Os certificados ainda não foram liberados” | `DATA_LIBERACAO` no futuro. Use `2000-01-01` para testar. |
| Mudei o `.env` e nada mudou | O servidor lê o `.env` ao iniciar: pare (**Ctrl + C**) e rode `python manage.py runserver` de novo. |
| Quero recomeçar o banco local do zero | Apague `db.sqlite3` e repita o passo 5. |

---

## 9. Publicar (quando for a hora)

O projeto já tem `Dockerfile` e `render.yaml`. No Render, além de subir o código,
configure as variáveis do `.env` no painel (**Environment**), com atenção a:
`DATABASE_URL` (Neon), `SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS=seudominio.com`,
`CSRF_TRUSTED_ORIGINS=https://seudominio.com`, `SITE_URL=https://seudominio.com`
e `DATA_LIBERACAO=2026-11-06`.

---

## 10. Quem usa o site NÃO precisa de LibreOffice

O LibreOffice roda **no servidor**, não no PC do participante. Quando alguém clica em
“Baixar PDF”, o servidor preenche o DOCX, chama o `soffice` da própria máquina e devolve
o PDF pronto — o navegador só recebe o arquivo. No PC do aluno basta um navegador.

Para conferir se um servidor está com o LibreOffice certo:

```powershell
python manage.py check_certificado
```
