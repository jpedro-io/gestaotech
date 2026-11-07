# -*- coding: utf-8 -*-
"""As 7 oficinas do projeto Gestão Tech e suas equipes.

Fonte única da carga inicial (`python manage.py seed`), também usada para
conferência no admin. Quando uma equipe mandar os nomes completos + CPF,
basta atualizar aqui e rodar o seed de novo (ele é idempotente) ou editar
direto no admin do Django.
"""

# (oficina, equipe como veio, [nomes das pessoas])
OFICINAS = [
    ("Gestão de Processos e Produtividade Inteligente com Coda e Coda AI",
     "Emilly, Erica e Heloísa",
     ["Emilly", "Erica", "Heloísa"]),

    ("Utilização de sistema de decisões gerenciais com dashboards dinâmicos",
     "Wesley, Gabriel, Pedro Henrique, Henrique e Fellipe",
     ["Wesley", "Gabriel", "Pedro Henrique", "Henrique", "Fellipe"]),

    ("Utilização de sistema de gerenciamento integrado de estoque e finanças",
     "Guilherme Bacelar, Felipe Juan, Raphael, Paulo Vinícius e Nicolas Prado",
     ["Guilherme Bacelar", "Felipe Juan", "Raphael", "Paulo Vinícius", "Nicolas Prado"]),

    ("Workspace Integrado: Organizando Projetos e Alinhando Negócios com o Notion",
     "Leandro, Gilberto Júnior, João Vitor Guimarães, João Filipe de Andrade, "
     "Nicolas Prado e João Pedro Campos",
     ["Leandro", "Gilberto Júnior", "João Vitor Guimarães", "João Filipe de Andrade",
      "Nicolas Prado", "João Pedro Campos Rocha"]),

    ("Do Negócio ao Sistema: Traduzindo Requisitos e Dores Organizacionais sem Ruídos",
     "Davi Dias, Isabela Argolo, Leonardo Vitor Lacerda, Nícolas Amaral e Samuel Novaes",
     ["Davi Dias", "Isabela Argolo", "Leonardo Vitor Lacerda", "Nícolas Amaral", "Samuel Novaes"]),

    ("Utilização do Jira como ferramenta de otimização do processo administrativo (PODC)",
     "Hiago, Helder, Fernanda, Débora, Mateus Rodrigues, Mateus Oliveira",
     ["Hiago", "Helder", "Fernanda", "Débora", "Mateus Rodrigues", "Mateus Oliveira"]),

    ("Utilização do Microsoft List para integração da comunicação interna",
     "Davi Antunes, Samuel Bernardo, Vanderson Gomes, Guilherme Sulz, Mateus Alves e Enzo",
     ["Davi Antunes", "Samuel Bernardo", "Vanderson Gomes", "Guilherme Sulz",
      "Mateus Alves", "Enzo"]),
]

# Quem é ministrante da própria oficina. Todos os outros entram como ouvinte.
# Chave: nome completo; valor: nome da oficina em que ministra.
MINISTRANTES = {
    "João Pedro Campos Rocha":
        "Workspace Integrado: Organizando Projetos e Alinhando Negócios com o Notion",
}

# Observações de cadastro: nomes que ainda não são nomes completos.
NOMES_INCOMPLETOS = {"Emilly", "Erica", "Heloísa", "Wesley", "Gabriel", "Henrique",
                     "Fellipe", "Raphael", "Leandro", "Hiago", "Helder", "Fernanda",
                     "Débora", "Enzo", "Nicolas Prado", "Pedro Henrique"}


def pessoas_por_oficina():
    """[(nome_oficina, nome_pessoa, papel)] pronto para o seed."""
    linhas = []
    for nome_oficina, _, pessoas in OFICINAS:
        for pessoa in pessoas:
            papel = "MINISTRANTE" if MINISTRANTES.get(pessoa) == nome_oficina else "OUVINTE"
            linhas.append((nome_oficina, pessoa, papel))
    return linhas
