# Importação dos participantes

Arquivos desta pasta:

| Arquivo | O que é |
|---|---|
| `participantes_recebidos.json` | os 25 registros recebidos (nome, e-mail, CPF), guardados como vieram |
| `participantes.csv` | CSV `nome,cpf,oficina,papel` **pronto para importar** |
| `schema_postgres.sql` | DDL opcional das duas tabelas, para quem quiser criar à mão no Neon |

## Regra aplicada

Todos os 25 são da oficina do **Notion**:

> `Workspace Integrado: Organizando Projetos e Alinhando Negócios com o Notion`

- **João Pedro Campos Rocha** (CPF 179.280.476-83) → `MINISTRANTE` nessa oficina.
- **Os outros 24** → `OUVINTE` nessa mesma oficina.

Total: **25 participações, 25 códigos de validação** (um por pessoa).

## Como importar

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_oficinas
.\.venv\Scripts\python.exe manage.py seed_participantes --csv importacao\participantes.csv
.\.venv\Scripts\python.exe manage.py exportar_participacoes
```

Rodar o mesmo comando duas vezes é seguro: o que já existe é atualizado, não duplicado.

> Não importe o `pessoas_exemplo.csv` no banco de produção: ele tem CPFs fictícios
> (111.444.777-35 etc.) usados só para teste.

## Quando as outras equipes enviarem os dados

Mesmo formato, só trocando a coluna `oficina` pelo nome exato da outra oficina:

```csv
nome,cpf,oficina,papel
Maria Luiza Santos Rocha Granja,03315106509,Gestão de Processos e Produtividade Inteligente com Coda e Coda AI,OUVINTE
```

Os nomes exatos das 7 oficinas aparecem no select do site ou em
`certificados/dados_oficinas.py`. Para conferir o que já está cadastrado:

```powershell
.\.venv\Scripts\python.exe manage.py exportar_participacoes
```

## Trocar oficina/papel de alguém depois

Edite o CSV (nome ou CPF + oficina + papel) e rode o comando de novo. Para remover alguém,
use o `/admin/` → Participações.
