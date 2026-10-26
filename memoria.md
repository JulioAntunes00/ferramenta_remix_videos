# MEMORIA DO PROJETO: REMIX VÍDEOS (SAAS DE VÍDEO ANTI-BAN)

> **Regra de Manutenção do Projeto:**
> Sempre consultar este arquivo antes de alterar código ou adicionar dependências. Toda evolução de arquitetura, novos módulos ou decisões estratégicas devem ser registrados aqui para manter o contexto consistente e economizar tokens.

---

## 1. Visão Geral do Produto
- **Objetivo:** Aplicação web para criadores de conteúdo e gestores de tráfego (foco principal: TikTok, Reels, Shorts).
- **Mecânica Principal:** O usuário envia blocos de vídeos divididos em 3 categorias ordenadas:
  1. **Gancho (Hook)** - Introdução do vídeo
  2. **Meio (Body/Explicativo)** - Apresentação da oferta/produto
  3. **CTA (Call to Action)** - Encerramento/chamada de ação
- **Saída:** O sistema gera todas as permutações possíveis (ex: $4 \times 4 \times 4 = 64$ vídeos), sempre na ordem estrita: `Gancho -> Meio -> CTA`.
- **Diferencial Anti-Ban TikTok:**
  - Limpeza total de metadados de gravação (`-map_metadata -1`) e injeção de novos timestamps limpos para evitar detecção algorítmica.
  - Avaliação de similaridade entre os vídeos do lote (Score com Badges):
    - 🟢 **Verde:** Baixa similaridade com os demais do lote (ótimo para postar em sequência).
    - 🟡 **Amarelo:** Similaridade média (recomendado espaçar a postagem).
    - 🔴 **Vermelho:** Alta similaridade estrutural (mais de 65% de tempo idêntico).
- **Segurança de Execução Local:** Trava configurável inicial de até $4 \times 4 \times 4$ (máximo 64 variações simultâneas) para não sobrecarregar disco/processador do usuário.

---

## 2. Padrões de Engenharia & Clean Code
- **Modularidade Estrita:** Camadas de domínio (regras de negócio e processamento de vídeo) são desacopladas da camada de apresentação (web).
- **Princípio da Responsabilidade Única (SRP):** Cada serviço tem uma única função bem definida.
- **Transição Local -> Produção:** A base de código atual roda 100% offline/local sem custos mensais, mas foi projetada para receber autenticação, fila Redis/Celery e gateway de pagamento (Stripe/Asaas) no futuro sem refatoração do motor principal.
- **Design de Interface:** Visual moderno, profissional, responsivo (Desktop e Mobile), sem clichês visuais de IA, inspirado em ferramentas SaaS de alta performance (*Linear, Raycast, Vercel*).

---

## 3. Estrutura de Diretórios do Projeto
```text
C:\Users\Note\Desktop\site_montagem/
├── memoria.md                    # Fonte da verdade do projeto
├── .gitignore                    # Bloqueio de arquivos de vídeo e dependências
├── backend/                      # Camada de regras de negócio e API
│   ├── app/
│   │   ├── api/                  # Endpoints REST (upload, render, status, download)
│   │   ├── core/                 # Configurações globais e constantes
│   │   ├── services/             # Regras de negócio
│   │   │   ├── video_engine.py   # Manipulação FFmpeg, normalização e strip de metadados
│   │   │   ├── similarity.py     # Algoritmo de cálculo de similaridade e score
│   │   │   └── storage.py        # Gerenciamento de arquivos locais e limpeza
│   │   └── main.py               # Ponto de entrada do backend
│   └── requirements.txt          # Dependências Python
├── frontend/                     # Interface de usuário (Desktop & Mobile)
│   ├── public/
│   ├── src/
│   │   ├── components/           # Componentes modulares (UploadColumn, VideoCard, ProgressBar)
│   │   ├── hooks/                # Hooks de estado e chamadas de API
│   │   ├── styles/               # Padrões visuais
│   │   └── App.jsx
│   └── package.json
└── docs/                         # Documentações complementares
```

---

## 4. Repositório Git
- **URL Remota:** `https://github.com/JulioAntunes00/ferramenta_remix_videos.git`
- **Branch Principal:** `main`

---

## 5. Histórico de Alterações e Marcos
- **2026-10-26:**
  - Definição do escopo, requisitos de negócio e anti-ban TikTok.
  - Inicialização do repositório Git local e criação do `memoria.md` e `.gitignore`.
  - Decisão da trava de segurança inicial $4 \times 4 \times 4$.
  - Instalação automatizada do FFmpeg 9.0.2 e configuração no PATH do Windows.
  - Criação do Backend FastAPI modular (`video_engine.py`, `similarity.py`, `storage.py`, `routes.py`).
  - Implementação da sanitização Anti-Ban (`-map_metadata -1`, áudio loudnorm, injeção de metadados limpos).
  - Criação do Frontend Vite + React + Tailwind CSS com visual SaaS moderno (Desktop & Mobile).
  - Criação do script de inicialização `iniciar_sistema.bat`.
  - Push de todas as alterações para o GitHub (`main`).
