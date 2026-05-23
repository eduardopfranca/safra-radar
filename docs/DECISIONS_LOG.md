# DECISIONS_LOG — Safra Radar
**Versao | 21/05/2026 | Append-only**

> Registro de decisoes arquiteturais, padroes de trabalho e licoes aprendidas.
> Consultar antes de propor mudancas estruturais. Toda decisao listada aqui deve ser respeitada ate ser explicitamente revisada via novo registro datado.

---

## Decisoes Arquiteturais

### D01 — Safra Radar e modulo do Safra Segura (Madcap)
**Data:** 21/05/2026
**Decisao:** o Safra Radar e um modulo do Safra Segura, produto da Madcap.
**Impacto:** Safra Radar e projeto independente; futuramente sera integrado como modulo do Safra Segura.

### D02 — Eduardo administra todo o stack tecnico
**Data:** 21/05/2026
**Decisao:** Eduardo administra repositorio, Supabase, Render, Vercel, Lovable, dominio e qualquer infraestrutura tecnica.
**Impacto:** Toda configuracao manual (env vars, SQL, Edge Functions) e responsabilidade de Eduardo.

### D03 — MVP com atualizacao pull-based, sem cronjob
**Data:** 21/05/2026
**Decisao:** no MVP nao havera cronjob nem coleta automatica em background. Cada bloco da tela tem botao "atualizar" proprio + badge de desatualizacao com timestamp.
**Justificativa:** simplifica drasticamente a infraestrutura inicial. Permite validar a viabilidade de cada fonte de dado antes de investir em scheduling. Evita custo de execucao continua durante validacao do produto.
**Impacto:** o primeiro usuario que abrir cada bloco do dia paga o custo da chamada externa. Aceitavel no MVP. Migrara para cronjob/cache central quando volume justificar.
**Threshold de desatualizacao por bloco:** definir caso a caso (ex: precos 15min, calendario 24h, ENSO 7 dias).

### D04 — Safra Radar nunca recomenda venda
**Data:** 21/05/2026
**Decisao:** o produto nunca produzira recomendacao de venda ("venda X% agora", "trave isso"). Entrega dado, contexto historico e visual claro. Decisao e do produtor.
**Justificativa:** filosofica (respeito a autonomia do produtor) e juridica (sem responsabilidade por orientacao financeira a terceiros). Posicionamento do produto se baseia em servir como **catalisador de procura pela mesa**, nao como advisor.
**Impacto:** qualquer feature que se aproxime de recomendacao automatica precisa de aval explicito de Eduardo em DECISIONS_LOG antes de ser implementada. Mesmo em fases futuras.

### D05 — Linguagem do produto e o portugues do produtor
**Data:** 21/05/2026
**Decisao:** todo texto exibido ao usuario final usa portugues coloquial do produtor brasileiro: "saca", "trava", "premio porto", "alta/baixa". Termos tecnicos (basis, hedge, MTM, bushel) so com glossario inline ou tooltip.
**Justificativa:** publico alvo (medio produtor 500–3.000 ha) nao tem letramento em mercado financeiro. Traducao e diferencial central do produto.
**Impacto:** Glossary.md sera mantido como fonte de verdade dos termos publicos. Conteudo editorial pos-evento segue a mesma regra.

### D10 — Probes-first para fontes novas
**Data:** 22/05/2026
**Decisao:** todo provedor de dado externo novo passa por probe de descoberta antes da implementacao do client. O probe nao chuta — lista o universo real (atributos, commodities, paises, statisticat categories) usando os endpoints meta da propria API quando disponiveis (`/commodityAttributes`, `/commodities`, `/countries`, etc.).
**Justificativa:** descobrimos na sessao de 22/05/2026 que chutar IDs/categorias gera bugs silenciosos dificeis de detectar (atributo mapeado com ID errado passa em todos os testes mas retorna dado incorreto).
**Impacto:** todo novo client em `connections/` deve ter um `scripts/probe_*.py` correspondente executado e revisado antes da implementacao.

### D11 — Camada de comparacao fica em engines, nao em clients
**Data:** 22/05/2026
**Decisao:** a SPEC ja estabelece que connections sao I/O puro, mas isso foi explicitamente confirmado em decisao: calculos de variacao (YoY, WoW, vs. media 5 anos) vivem em `engines/`, com atomicos reutilizaveis em `utils.py`. Clients retornam dado bruto P06-wrapped e nunca fazem aritmetica sobre os valores.
**Justificativa:** separacao de responsabilidades — um bug de calculo nao contamina a camada de coleta e vice-versa.
**Impacto:** engines nao foram criados ainda — serao criados quando houver multiplos consumidores da logica de comparacao. Por ora os blocos `if __name__ == "__main__":` dos clients importam `utils.py` diretamente para simular o produto final durante desenvolvimento.

---

## Padroes de trabalho

### P01 — Documentacao objetiva
**Data:** 21/05/2026

### P02 — Uma etapa por vez, com confirmacao
**Data:** 21/05/2026
**Padrao:** Claude nunca empilha multiplas execucoes em um unico prompt. Cada migration SQL, cada arquivo de codigo, cada prompt para agente executor e enviado individualmente, com confirmacao de Eduardo antes de avancar.
**Justificativa:** Evita erros caros, mantem controle.

### P03 — Nunca trabalhar em arquivo sem conteudo completo
**Data:** 21/05/2026
**Padrao:** Claude nunca propoe edicao em arquivo sem que Eduardo cole o conteudo atual completo no chat. Nao assumir o que existe.
**Justificativa:** drift entre o que Claude lembra e a realidade no repo gera bugs silenciosos.

### P04 — Teste de fronteira antes de cada prompt
**Data:** 21/05/2026
**Padrao:** antes de redigir qualquer prompt para Claude Code, Lovable ou Supabase Dashboard, aplicar o teste: "esse prompt toca apenas uma camada?". Se nao, decompor.

### P05 — Git push e responsabilidade de Eduardo
**Data:** 21/05/2026
**Padrao:** Claude Code prepara commits, mas o push e feito manualmente por Eduardo (`git push origin master:main`). Documentacao .md atualizada via Claude Code sempre com instrucao explicita "nao commitar, nao pushar".
**Justificativa:** controle de versao consciente. Eduardo decide quando e o que sobe.

### P06 — Citar fonte e timestamp em todo dado externo
**Data:** 21/05/2026
**Padrao:** todo endpoint que retorna dado externo (preco, evento, indicador) inclui no payload: `source` (string), `source_url` (string, opcional), `fetched_at` (ISO 8601), `source_timestamp` (ISO 8601 quando disponivel). Frontend exibe ao usuario.
**Justificativa:** confiabilidade da fonte e parte central da promessa do produto. Usuario precisa saber de onde veio e quando.

---

## Licoes aprendidas

### L04 — Endpoints meta de APIs governamentais economizam horas
**Data:** 22/05/2026
APIs como USDA FAS PSD expoe endpoints especificos para listar atributos (`/commodityAttributes`), commodities (`/commodities`), paises (`/countries`). Sempre buscar esses endpoints meta antes de redigir probe de descoberta — eles sao a fonte canonica e evitam adivinhacao. Buscar primeiro na documentacao oficial; se nao houver, no Swagger/OpenAPI; se nem isso, em SDKs comunitarios.

### L05 — Prompt grande no PowerShell trunca silenciosamente
**Data:** 22/05/2026
O PowerShell tem buffer limitado para colagem direta. Prompts longos colados sao silenciosamente cortados — o agente recebe metade e executa so essa metade. Sintoma: agente cumpre so uma fracao das tarefas listadas sem reportar erro. Solucao: salvar prompt em arquivo e usar `Get-Content prompt.txt | claude`, ou usar a UI integrada do VS Code (Claude Code extension) que nao tem esse problema.

### L06 — Agentes diferentes tem capacidades muito diferentes
**Data:** 22/05/2026
GitHub Copilot e Claude Code coexistem no VS Code e parecem intercambiaveis na UI, mas modelos e limites sao distintos. Copilot Raptor mini falhou com 408 em prompt medio que Claude Code Sonnet executou sem problema. Identificar a extensao correta antes de mandar trabalho tecnico — nao assumir que qualquer assistente de codigo serve para qualquer tarefa.

---

*Fim do documento — DECISIONS_LOG.md*
