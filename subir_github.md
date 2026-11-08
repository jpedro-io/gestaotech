# Subir para o GitHub (antes do Fly)

O repositório precisa conter **só o código**. Chaves, senha do Neon e banco local ficam de fora.

---

## 1. Criar o repositório vazio no GitHub

1. https://github.com/new
2. **Repository name:** `gestao-tech-certificados`
3. **Private** (recomendado — o projeto tem dados de pessoas reais; público também funciona,
   mas os CPFs nunca são gravados no código, só o CSV de importação, que é dado pessoal)
4. **NÃO** marque “Add a README”, “Add .gitignore” nem “Choose a license” — o projeto já tem
   esses arquivos, e criar pelo GitHub causa conflito.

Copie o endereço do repositório, algo como
`https://github.com/SEU-USUARIO/gestao-tech-certificados.git`.

## 2. Conferir o `.gitignore` (já configurado)

O arquivo já ignora `.env`, `db.sqlite3`, `participacoes.csv`, `staticfiles/`, `capturas/`,
`__pycache__`, `.venv` e arquivos de editor. Nunca comite o `.env` — ele tem
`SECRET_KEY`, `CPF_PEPPER` e a `DATABASE_URL` do Neon.

Se algum dia precisar versionar uma configuração, use `.env.example` (já está no repositório).

## 3. Primeiro commit (no terminal do VS Code, na pasta do projeto)

```powershell
git init
git add .
git status                # confira: NÃO deve aparecer .env nem db.sqlite3
git commit -m "Site de certificados Gestão Tech (Django + Neon)"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/gestao-tech-certificados.git
git push -u origin main
```

Se o `git` não for reconhecido: instale em https://git-scm.com/download/win (opção
“Git from the command line and also from 3rd-party software”) e reabra o VS Code.

No primeiro `push` o Git pode abrir o navegador para autenticar (GitHub Device Login) —
isso é normal. Alternativa: instalar o **GitHub CLI** (`winget install GitHub.cli`) e rodar
`gh auth login`, que já deixa a autenticação pronta.

## 4. Conferir no GitHub

Recarregue a página do repositório: devem aparecer `Dockerfile`, `fly.toml`,
`entrypoint.sh`, `requirements.txt`, `manage.py`, as pastas `certificados/`, `emissao/`,
`config/`, `importacao/`, `modelos_docx/`, `fontes/`.

Confirme que **NÃO** existe `.env` na lista. Se aparecer, remova do controle de versão:

```powershell
git rm --cached .env
git commit -m "remove .env do versionamento"
git push
```

E, por segurança, **troque a `SECRET_KEY` e o `CPF_PEPPER`** no painel do Fly/Neon depois.

## 5. Alterações do dia a dia

```powershell
git add .
git commit -m "descrição curta da mudança"
git push
```

## Próximo passo

Depois do `push`, siga o **`DEPLOY_FLY.md`**. Com o código no GitHub, o deploy pode ser feito
direto do repositório (o Fly puxa de lá) ou pela pasta local — as duas formas usam o mesmo
`Dockerfile`.
