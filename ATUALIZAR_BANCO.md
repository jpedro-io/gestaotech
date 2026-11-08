# Como atualizar o banco quando chegarem novos dados

O site não tem lista fixa: **tudo o que aparece na caixa de seleção vem da tabela
`certificados_oficina`**, e cada aluno vem da tabela `certificados_participacao`.
Cadastrou → aparece no site na hora, sem precisar reiniciar ou fazer deploy.

---

## 1. Chegou uma planilha de equipe → CSV

Formato (uma linha por pessoa × oficina):

```csv
nome,cpf,oficina,papel
Emilly Santos,123.456.789-09,Gestão de Processos e Produtividade Inteligente com Coda e Coda AI,MINISTRANTE
Davi Dias,111.444.777-35,Do Negócio ao Sistema: Traduzindo Requisitos e Dores Organizacionais sem Ruídos,OUVINTE
```

- `nome`: nome completo como deve sair no certificado.
- `cpf`: com ou sem pontuação; é validado pelo dígito verificador.
- `oficina`: o **nome exato** de uma das 7 oficinas. Para participantes de todas, use `TODAS`.
- `papel`: `OUVINTE`, `MINISTRANTE` ou `ORGANIZADOR`.

Salve como UTF-8 (o Excel: “CSV UTF-8”). Se usar vírgula decimal ou ponto e vírgula como
separador, prefira exportar como “CSV (separado por vírgulas)”.

## 2. Importar

**Opção A — pela sua máquina, direto no banco do Neon** (o `.env` precisa ter a `DATABASE_URL`):

```powershell
.\.venv\Scripts\python.exe manage.py seed_participantes --csv importacao\equipe_coda.csv
```

**Opção B — pela própria aplicação no Fly** (útil quando quem manda o arquivo não tem o projeto):

```powershell
flyctl ssh sftp shell
# dentro do console:  put importacao\equipe_coda.csv /app/importacao/equipe_coda.csv
flyctl ssh console -C "python manage.py seed_participantes --csv /app/importacao/equipe_coda.csv"
```

**Opção C — uma pessoa por vez, pelo navegador:** `/admin/` → Participações → *Adicionar*.
Preencha nome, CPF, oficina e papel. O admin mostra o CPF mascarado e gera o código sozinho.

## 2b. Uma pessoa por vez, pelo terminal (sem CSV)

```powershell
.\.venv\Scripts\python.exe manage.py add_participante --nome "Fulano de Tal" --cpf 123.456.789-09 --oficina notion --papel OUVINTE
```

Saída: `criada: Fulano de Tal · Workspace Integrado: … · OUVINTE · CPF ***.456.789-** · OFC-XXXX-XXXX-XXXX`

- `--oficina` aceita um trecho do nome (`notion`, `coda`, `jira`, `list`, `dashboards`,
  `estoque`, `requisitos`) ou `TODAS`. Trecho ambíguo ele recusa e lista as opções.
- `--papel` é opcional: `OUVINTE` (padrão), `MINISTRANTE` ou `ORGANIZADOR`.
- `--seco` mostra o que faria, sem gravar.
- Rodar duas vezes para a mesma pessoa **atualiza** (mesmo código), não duplica.
- CPF inválido é recusado antes de gravar.

No Fly, a mesma coisa:

```powershell
flyctl ssh console -C 'python manage.py add_participante --nome "Fulano de Tal" --cpf 123.456.789-09 --oficina notion'
```

## 2c. Edições manuais pelo navegador

`/admin/` (usuário criado com `createsuperuser`):

| Quero… | Onde |
|---|---|
| adicionar uma pessoa | Participações → **Adicionar** (nome, CPF, oficina, papel) |
| corrigir nome | Participações → buscar → editar **Nome** → salvar |
| corrigir CPF | Participações → abrir → preencher **CPF** (mostra `***.456.789-**`; em branco = mantém) |
| revogar um certificado | Participações → marcar **revogado** |
| criar uma oficina | Oficinas → **Adicionar** (aparece no select na hora) |
| ver quem já emitiu | Participações → coluna **emitido em** |

Nada disso exige deploy nem reiniciar o site.

## 3. O comando é idempotente

Rodar o mesmo CSV dez vezes **não duplica**: ele procura por CPF + oficina + papel e atualiza
(nome, CPF). Por isso é seguro reenviar uma planilha corrigida — mudou uma grafia ou entrou
gente nova, é só rodar de novo.

Saída esperada:

```
CSV: 12 criada(s), 3 atualizada(s), 0 ignorada(s). Total no banco: 28.
```

Linhas com CPF inválido, papel errado ou oficina vazia são **ignoradas com aviso**
(`linha 7: CPF inválido (Fulano) — ignorada`), e o resto do arquivo entra normalmente.

## 4. Nomes e CPFs errados

- **Corrigir um nome:** `/admin/` → Participações → busque pelo nome ou código → edite.
- **Corrigir um CPF:** abra a participação, preencha o campo **CPF** (o atual aparece como
  `***.982.247-**`) e salve. Deixar em branco mantém o CPF que já está lá.
- **Trocar de oficina:** edite a participação, ou reenvie o CSV com a oficina certa.
  Atenção: o comando casa por CPF + oficina + papel, então mudar de oficina **cria uma nova
  participação**; apague a antiga no admin (ou marque **revogado**).

## 5. Certificado emitido errado

Se alguém já baixou o PDF e depois o dado foi corrigido:

1. corrija o nome/CPF/oficina;
2. no admin, marque **revogado** na participação antiga (o código antigo passa a responder
   “cancelado” na validação pública);
3. crie/selecione a participação correta — ela tem um **código novo**
   (o código é imutável; não dá para reaproveitar o antigo).

## 6. Nova oficina

Se aparecer uma oficina que não está nas 7:

```powershell
flyctl ssh console -C "python manage.py shell -c \"from certificados.models import Oficina; Oficina.objects.get_or_create(nome='Nome da nova oficina', defaults={'equipe': 'Equipe X'})\""
```

(ou `/admin/` → Oficinas → Adicionar). Ela aparece no select imediatamente.
Se quiser que ela exista também no `seed_oficinas` (para deploys futuros), acrescente em
`certificados/dados_oficinas.py` e faça commit.

## 7. Backup antes de mexer em muita coisa

```powershell
.\.venv\Scripts\python.exe manage.py exportar_participacoes --saida backup_2026-11-08.csv
```

O CSV tem nome, oficina, papel, código e CPF mascarado — serve de conferência, mas **não**
para reimportar (falta o CPF completo, que nunca é gravado por privacidade).
Se precisar refazer a carga, use os CSVs originais das equipes.

## 8. O que NÃO fazer

- **Não troque o `CPF_PEPPER`** depois de haver dados: os hashes não batem mais e ninguém
  consegue emitir. (Se acontecer, é preciso reimportar todos os CSVs.)
- **Não edite `cpf_hash` à mão** no admin/SQL: use o campo CPF do admin.
- **Não apague uma oficina** que tenha participações (o banco bloqueia; é proteção).
- **Não rode `seed_participantes` sem `--csv`** em produção: ele cadastra as equipes pelo
  catálogo, com CPF vazio, e essas pessoas não conseguem emitir.
