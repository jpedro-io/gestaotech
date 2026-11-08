# Gestão Tech — Portal de Certificados

Site para **emitir e validar os certificados** das oficinas do projeto **Gestão Tech**, do
Bacharelado em Sistemas de Informação do **IFBA — Campus Vitória da Conquista**.

O participante informa nome, CPF e a oficina; o site localiza o certificado no banco de dados
e entrega o PDF pronto para impressão, com código de validação e QR Code. Qualquer pessoa pode
conferir a autenticidade de um certificado pela página de validação, sem login.

---

## Para quem participou

1. Acesse a página inicial e preencha **nome completo**, **CPF** e a **oficina**
   (deixe em "Todas as oficinas" para ver todos os seus certificados).
2. O site mostra um cartão por participação, indicando o papel: **ouvinte**, **ministrante**
   ou **organizador(a)**.
3. Clique em **Baixar PDF**. O arquivo sai em uma página, formato paisagem A4, pronto para
   impressão ou envio digital.
4. Não é preciso instalar nada, criar conta ou fazer login. Funciona no computador e no celular.

Cada certificado traz:

- nome completo e CPF parcialmente oculto (`***.123.456-**`);
- a oficina, a data, a carga horária e o papel exercido;
- um **código de validação** exclusivo (formato `OFC-XXXX-XXXX-XXXX`);
- um **QR Code** que leva à página de conferência.

## Para quem precisa conferir um certificado

Na página **Validar certificado**, digite o código impresso no rodapé do documento (ou leia o
QR Code). A resposta é imediata e mostra um destes estados:

| Resultado | Significado |
|---|---|
| **Certificado válido** | emitido por este projeto; exibe nome, oficina, papel e carga horária |
| **Não encontrado** | o código não existe — documento não emitido por nós |
| **Cancelado** | o certificado existiu, mas foi revogado depois da emissão |

A validação é pública, mas não lista participantes e nunca mostra o CPF.

---

## Como funciona por dentro

| Camada | Tecnologia |
|---|---|
| Aplicação | Python + Django 5.2 |
| Banco de dados | PostgreSQL (Neon) em produção; SQLite no desenvolvimento |
| Geração do PDF | modelo DOCX preenchido por tags + conversão pelo LibreOffice + recorte da 1ª página |
| Interface | HTML/CSS puro, responsivo, com fontes próprias (sem CDN) |
| Deploy | container Docker no Fly.io, com o LibreOffice dentro da imagem |

O certificado não é uma imagem pronta: o servidor preenche um **modelo DOCX** (um para cada
papel), substitui as tags `((NOME))`, `((CPF))`, `((OFICINA))`, `((CODIGO))`,
`((DATA_EMISSAO))`, `((URL_VALIDACAO))` e `((QRCODE))`, converte em PDF e entrega apenas a
primeira página. O PDF é gerado no momento do download — nunca fica armazenado.

### Privacidade do CPF

O CPF completo **não é gravado no banco**. São guardados apenas:

- um **hash SHA-256** com uma chave secreta do servidor (usado para localizar o certificado);
- os **6 dígitos do meio**, para montar `***.123.456-**` na tela e no documento.

Por isso, quem esquece o CPF não pode ser atendido por busca no banco — é preciso o número
informado no ato da inscrição.

### Dados

Duas tabelas sustentam o site:

- **Oficinas** — as sete oficinas do projeto, com a equipe responsável. É daqui que sai a
  caixa de seleção da página inicial.
- **Participações** — uma linha por pessoa × oficina × papel, com o código de validação
  exclusivo, a data de emissão e a marcação de revogação.

A carga é **idempotente**: rodar a mesma planilha duas vezes atualiza os registros em vez de
duplicá-los. Novos participantes e novas oficinas aparecem no site imediatamente, sem
precisar publicar uma nova versão.

---

## Rotas

| Rota | O que faz |
|---|---|
| `/` | formulário de emissão (nome, CPF com máscara, oficina) |
| `POST /buscar/` | lista os certificados encontrados, um cartão por papel |
| `/baixar/<token>/` | gera e entrega o PDF (link assinado, válido por 10 minutos) |
| `/validar/` e `/validar/<CODIGO>/` | conferência pública do certificado |
| `/admin/` | gestão de oficinas e participações (acesso restrito) |

---

## Rodando o projeto

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # preencha DATABASE_URL, SECRET_KEY e CPF_PEPPER
python manage.py migrate
python manage.py seed_oficinas
python manage.py seed_participantes --csv importacao/participantes.csv
python manage.py runserver
```

Requisitos: **Python 3.10+** (testado no 3.14), **LibreOffice** para a conversão do PDF e as
fontes da pasta `fontes/` instaladas no sistema.

### Variáveis de ambiente

| Variável | Para que serve |
|---|---|
| `DATABASE_URL` | conexão com o Postgres (vazio = SQLite local) |
| `SECRET_KEY` | assinatura dos links de download e do CSRF |
| `CPF_PEPPER` | sal do hash do CPF — **nunca trocar depois de popular o banco** |
| `SITE_URL` | endereço público que entra no rodapé do certificado e no QR Code |
| `DATA_LIBERACAO` | antes dessa data a busca responde "ainda não liberados" |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | domínio de produção |
| `SOFFICE_BIN` | caminho do LibreOffice, quando não está no PATH (Windows) |

### Comandos úteis

```bash
python manage.py seed_oficinas                              # cadastra as 7 oficinas
python manage.py seed_participantes --csv arquivo.csv       # importa/atualiza participantes
python manage.py add_participante --nome "..." --cpf ... --oficina notion
python manage.py exportar_participacoes                     # confere o que está no banco
python manage.py check_certificado                          # testa LibreOffice, modelos e fontes
python manage.py createsuperuser                            # acesso ao /admin/
```

Formato do CSV: `nome,cpf,oficina,papel`, com `papel` em `OUVINTE`, `MINISTRANTE` ou
`ORGANIZADOR` e `oficina` igual ao nome exato cadastrado (ou `TODAS`).

### Deploy

```bash
docker build -t gestao-tech .
flyctl secrets set DATABASE_URL="..." CPF_PEPPER="..." SECRET_KEY="..."
flyctl deploy
```

O container instala o LibreOffice, aplica as migrations e cadastra as oficinas ao iniciar.
Como a conversão do PDF depende do LibreOffice **no servidor**, quem acessa o site não precisa
instalar nada.

---

## Estrutura

```
config/              configuração do Django
certificados/        modelos, admin e comandos de carga (oficinas e participações)
emissao/             telas, busca, geração do PDF e validação
modelos_docx/        modelos do certificado (ouvinte, ministrante, organizador)
fontes/              tipografia usada no documento e no site
importacao/          planilhas/CSVs de participantes
```

---

## Créditos

Projeto **Gestão Tech** — Bacharelado em Sistemas de Informação,
Instituto Federal de Educação, Ciência e Tecnologia da Bahia (IFBA) — Campus Vitória da Conquista.

Apoio institucional: PROEX, UESB e FAINOR.

Dúvidas sobre certificados: **jprocha.tech@gmail.com**
