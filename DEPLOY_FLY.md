# Deploy no Fly.io — passo a passo

O site roda em container (Docker). O `Dockerfile` já instala o **LibreOffice** e as fontes,
então o PDF funciona no servidor **sem precisar de nada no PC de quem acessa**.

Arquivos de deploy no projeto:

| Arquivo | Para que serve |
|---|---|
| `Dockerfile` | imagem com Python, LibreOffice, fontes e o site |
| `entrypoint.sh` | aplica `migrate`, semeia o banco e sobe o gunicorn |
| `fly.toml` | configuração do app (porta, região, saúde, release) |
| `.dockerignore` | evita subir `.env`, `db.sqlite3` e lixo para a imagem |

---

## 0. Antes de começar

Você precisa de: **flyctl** instalado, o **`DATABASE_URL` do Neon** em mãos e as duas chaves
que estão no seu `.env` (`SECRET_KEY` e `CPF_PEPPER`).

> ⚠️ O `CPF_PEPPER` do Fly **tem que ser exatamente o mesmo** que já gerou os hashes no Neon.
> Se você só populou o Neon com o `.env` atual, copie esse valor. Se trocar, os CPFs
> cadastrados deixam de ser encontrados — e a correção seria reimportar o CSV.

---

## 1. Instalar o flyctl

No PowerShell:

```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

Feche e reabra o terminal e confira:

```powershell
flyctl version
```

## 2. Entrar / criar conta

```powershell
flyctl auth signup      # ou: flyctl auth login
```

## 3. Primeiro deploy (sem criar app ainda)

> O código já está no GitHub (veja `subir_github.md`)? Então rode `flyctl launch --no-deploy`
> a partir da pasta local mesmo — ele usa o `Dockerfile` do repositório clonado. Não é preciso
> configurar integração com o GitHub para funcionar.



Na pasta do projeto (`...\gestao-tech`):

```powershell
flyctl launch --no-deploy
```

Ele pergunta:

- **App name:** `gestao-tech` (ou outro; se estiver ocupado, use `gestao-tech-ifba`)
- **Region:** `gru` (São Paulo) — é a mais próxima da Bahia
- **Postgres/Redis:** **No** (o banco é o Neon)
- **Deploy now?** **No**

Ele cria/ajusta o `fly.toml`. Se o app name mudar, ajuste também as três linhas de endereço
dentro de `[env]` (`ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_URL`) para o nome escolhido.

## 4. Definir os segredos

```powershell
flyctl secrets set DATABASE_URL="COLE_AQUI_A_DO_NEON"
flyctl secrets set CPF_PEPPER="COLE_AQUI_O_DO_ENV"
flyctl secrets set SECRET_KEY="COLE_AQUI_O_DO_ENV"
```

(Com aspas, para o `?` e o `&` da URL não quebrarem no PowerShell.)

## 5. Deploy

```powershell
flyctl deploy
```

A primeira vez demora **5–10 minutos** (baixa a imagem base e instala o LibreOffice).
No fim ele mostra o endereço, algo como `https://gestao-tech.fly.dev`.

Ao subir, o `entrypoint.sh` roda automaticamente:
`migrate` → `seed_oficinas` → `seed_participantes` (do `importacao/participantes.csv`).
Como tudo é idempotente, cada deploy posterior não duplica ninguém.

## 6. Conferir se subiu

```powershell
flyctl status
flyctl logs
```

E no navegador:

1. `https://gestao-tech.fly.dev/` — o formulário deve abrir com as 7 oficinas.
2. Busque `Maria Luiza Santos Rocha Granja` / `033.151.065-09` → 1 certificado.
3. Clique em **Baixar PDF** — agora o LibreOffice roda no servidor, então funciona mesmo
   sem nada instalado no seu PC.
4. `https://gestao-tech.fly.dev/validar/` → cole um código `OFC-…` e confira.
5. `https://gestao-tech.fly.dev/admin/` → crie seu usuário:
   ```powershell
   flyctl ssh console -C "python manage.py createsuperuser"
   ```

## 7. Domínio próprio (opcional)

```powershell
flyctl certs add certificados.seudominio.com
```

O Fly mostra os registros DNS (CNAME/A) para colar no seu provedor. Depois ajuste:

```powershell
flyctl secrets set SITE_URL="https://certificados.seudominio.com"
```

E edite `[env]` do `fly.toml` (`ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`) e rode `flyctl deploy`
de novo. **Isso importa:** o `SITE_URL` é o endereço que vai impresso no rodapé do certificado
e dentro do QR Code — se estiver errado, o QR aponta para lugar nenhum.

---

## Custos e limites

- `shared-cpu-2x` com 1 GB é o mínimo confortável: o LibreOffice precisa de memória para
  converter o DOCX. Em máquina de 256 MB a conversão morre por falta de memória.
- `auto_stop_machines = "suspend"` faz a máquina dormir quando ninguém acessa (economia).
  O primeiro acesso depois disso leva alguns segundos — e depois do "sono" o LibreOffice
  converte normalmente.
- Um único worker (`GUNICORN_WORKERS=1`) é intencional: o rate limit usa cache em memória
  do processo; com vários workers o limite por IP valeria por worker.

## Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| `502` no primeiro acesso | a máquina estava dormindo; recarregue a página |
| `DisallowedHost` | `ALLOWED_HOSTS` no `fly.toml` está com outro domínio — ajuste e faça deploy |
| `CSRF verification failed` no admin | `CSRF_TRUSTED_ORIGINS` sem `https://` ou com domínio errado |
| PDF dá erro 500 | veja `flyctl logs`: se for `soffice`, a imagem não subiu com o LibreOffice (confira o `Dockerfile`) |
| Busca não acha ninguém | `DATABASE_URL` aponta para outro banco, ou o `CPF_PEPPER` do Fly é diferente do usado na importação |
| "Os certificados ainda não foram liberados" | `DATA_LIBERACAO` no futuro; ajuste no `fly.toml` |
