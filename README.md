# Gestão Tech — site de certificados (Django + Postgres/Neon)

Portal que emite e valida os certificados das oficinas. O certificado é o **DOCX modelo**
preenchido por tags, convertido em PDF pelo LibreOffice e entregue só com a página 1.
As oficinas e as participações vivem no **banco de dados**; o código é só a camada de acesso.

## 🗄️ Banco de dados (Neon/Postgres)

Sem `DATABASE_URL` o site usa o `db.sqlite3` local. Em produção, use o Neon.

### 1. Criar o banco no Neon
1. https://console.neon.tech → **New project**.
2. No painel, abra **Connection string** e copie a versão **Pooled connection**:
   ```
   postgresql://USUARIO:SENHA@ep-xxxx-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

### 2. Configurar o `.env`
```bash
cp .env.example .env     # se ainda não existir
```
Cole a string em `DATABASE_URL=`. As demais variáveis:

| Variável | Para que serve |
| --- | --- |
| `DATABASE_URL` | conexão com o Neon (vazio = SQLite local) |
| `SECRET_KEY` | assinatura dos tokens de download e do CSRF |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | domínio de produção (`*` em desenvolvimento) |
| `SITE_URL` | domínio público que entra no rodapé e no QR Code do certificado |
| `DATA_LIBERACAO` | antes dessa data a busca responde "ainda não liberados" |
| `CPF_PEPPER` | sal do hash do CPF — **nunca troque depois de popular** |
| `LIBREOFFICE_TIMEOUT` | segundos de espera na conversão do PDF |

### 3. Criar as tabelas e popular
```bash
python3 manage.py migrate            # cria as tabelas de oficinas e participações
python3 manage.py seed_oficinas      # as 7 oficinas do projeto (idempotente)
python3 manage.py createsuperuser    # acesso ao /admin/
```

Depois, a cada equipe que enviar os dados, rode **uma vez por arquivo**:
```bash
python3 manage.py seed_participantes --csv equipe_coda.csv
```
O CSV precisa do cabeçalho `nome,cpf,oficina,papel`:
```csv
nome,cpf,oficina,papel
João Pedro Campos Rocha,529.982.247-25,Workspace Integrado: Organizando Projetos e Alinhando Negócios com o Notion,MINISTRANTE
Davi Dias,111.444.777-35,Do Negócio ao Sistema: Traduzindo Requisitos e Dores Organizacionais sem Ruídos,OUVINTE
```

Regras da carga:
- `papel` aceita `OUVINTE`, `MINISTRANTE` ou `ORGANIZADOR`.
- O CPF é validado pelo dígito verificador; linha com CPF inválido é rejeitada.
- Rodar o mesmo CSV duas vezes **não duplica**: o registro existente é atualizado
  (idempotente — é assim que as equipes que faltam entram).
- Cada participação nasce com um código único `OFC-XXXX-XXXX-XXXX`, usado no QR Code.
- O CPF é guardado apenas como hash SHA-256 + 6 dígitos do meio; as telas mostram `***.123.456-**`.

### 4. Conferir o que está no banco
```bash
python3 manage.py exportar_participacoes                     # imprime a tabela
python3 manage.py exportar_participacoes --saida /tmp/part.csv
python3 manage.py gerar_codigos --oficina "..."              # códigos que faltarem
```
Ou abra `/admin/` → **Participações** (nome, CPF mascarado, oficina, papel, código, emitido em).

## Rodar localmente
```bash
python3 -m venv .venv && source .venv/bin/activate   # precisa de Django 5.2.8+ (Python 3.14 ok)
pip install -r requirements.txt
export DATA_LIBERACAO=2000-01-01        # libera antes do evento
python manage.py runserver
```
Precisa do **LibreOffice** instalado (`soffice` no PATH) e das fontes de `fontes/`
copiadas para o sistema (`fc-cache -f`), senão o PDF sai com outra tipografia.

## Rotas

| Rota | O que faz |
|---|---|
| `/` | formulário (nome, CPF com máscara, oficina vinda do banco) |
| `POST /buscar/` | lista os certificados do CPF (um cartão por papel) |
| `/baixar/<token>/` | gera e baixa o PDF (token assinado, válido por 10 min) |
| `/validar/` e `/validar/<CODIGO>/` | validação pública: válido, não encontrado ou cancelado |

## Estrutura

```
config/              settings.py (dotenv + dj-database-url), urls.py, wsgi.py
certificados/        app do banco
  models.py          Oficina, Participacao (hash do CPF, código único, emitido_em)
  dados_oficinas.py  catálogo das 7 oficinas/equipes, ministrantes, nomes incompletos
  admin.py           gestão pelo /admin/
  management/commands/  seed_oficinas, seed_participantes, exportar_participacoes, gerar_codigos
emissao/
  views.py           emitir, buscar, baixar, validar
  dados.py           consultas ao banco — só devolve cpf_parcial
  certificado.py     substitui as tags, gera o QR, converte com LibreOffice, recorta a página 1
  cpf.py             normalizar / valido / mascarar
  templates/         base.html, emitir.html, resultado.html, validar.html
  static/            css (telas + componentes), js (máscaras e estados), img, fonts
modelos_docx/        ouvinte.docx, ministrante.docx, organizador.docx (7 tags)
fontes/              Montserrat, Inter, JetBrains Mono
pessoas_exemplo.csv  amostra para testar a importação
```

Atualizações de dados (novos alunos, correções, novas oficinas): veja **`ATUALIZAR_BANCO.md`**.

## Vínculo do aluno com a oficina

A tabela `participacao` tem nome, CPF (hash + meio mascarado), forma de participação
(`OUVINTE` / `MINISTRANTE` / `ORGANIZADOR`), oficina e um código de validação próprio de
cada aluno — o mesmo CPF pode ter um código por oficina/papel.

## Quem usa o site precisa instalar algo?

Não. O LibreOffice roda **no servidor**: o navegador do participante só recebe o PDF pronto.
Ele é necessário apenas onde o Django está sendo executado (seu PC em desenvolvimento e o
container em produção — o `Dockerfile` já instala `libreoffice-writer`).

```bash
python manage.py check_certificado   # confere LibreOffice, modelos e fontes
```

## Docker e deploy

```bash
docker build -t gestao-tech .
docker run -p 8000:8000 --env-file .env -e PORT=8000 gestao-tech
```

O container usa `entrypoint.sh`: aplica `migrate`, opcionalmente semeia o banco
(`SEMEAR=1`) e sobe o gunicorn. O deploy no Fly.io está descrito em **`DEPLOY_FLY.md`**
(`fly.toml` já configurado).
O `Dockerfile` instala `libreoffice-writer`, copia as fontes e sobe com **1 worker e 4
threads** — necessário para o rate limit (`django-ratelimit` com cache local). Use uma máquina
com **1 GB de RAM**: o LibreOffice precisa de memória para converter o DOCX.

## Testes rápidos

```bash
DATA_LIBERACAO=2000-01-01 python3 - <<'PY'
import os, re, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings"); django.setup()
from django.test import Client
c = Client()
r = c.post("/buscar/", {"nome": "João Pedro", "cpf": "529.982.247-25", "oficina": ""})
tok = re.findall(r'/baixar/([^/"]+)/', r.content.decode())[0]
pdf = c.get(f"/baixar/{tok}/")
print(pdf.status_code, pdf["Content-Type"], len(pdf.content))
PY
```

## Pendências antes de publicar

1. Colar a `DATABASE_URL` do Neon no `.env` e rodar `migrate` + seeds lá.
2. Receber das equipes nome completo + CPF de todos os participantes.
3. Trocar `SITE_URL` pelo domínio final (rodapé e QR mudam juntos) e ajustar `DATA_LIBERACAO`.
4. CAPTCHA (Turnstile) na busca, que hoje é o ponto mais sensível.
