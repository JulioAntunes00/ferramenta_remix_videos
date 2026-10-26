# 🚀 Remix Vídeos Anti-Ban | SaaS de Escala de Criativos

> **Plataforma profissional para criação automatizada de variações em vídeo em larga escala para TikTok, Reels e Shorts, com proteção ativa contra punições de conteúdo não original (Anti-Ban).**

---

## 📌 Visão Geral do Projeto

No mercado de tráfego pago e produção de conteúdo, criadores e agências precisam testar dezenas de criativos diferentes toda semana. No entanto, produzir e editar manualmente dezenas de variações no Premiere ou CapCut consome dias de trabalho.

O **Remix Vídeos** automatiza esse processo combinando de forma inteligente 3 blocos estruturais de vídeo:
1. 🎣 **Gancho (Hook)** - Os primeiros 3 a 5 segundos de retenção.
2. 📦 **Apresentação / Corpo (Body)** - Demonstração da oferta e do produto.
3. 🎯 **Chamada para Ação (CTA)** - O fechamento com o comando de compra ou clique.

A partir desses blocos, o sistema calcula todas as permutações possíveis (ex: $4 \times 4 \times 4 = 64$ vídeos únicos), renderiza em lote e entrega tudo pronto para download em `.zip`.

---

## 🛡️ Diferenciais & Proteção Anti-Ban TikTok

O algoritmo do TikTok e Meta detecta repetições de criativos através de **metadados de gravação**, **assinatura visual de quadros (frame hash)** e **ondas sonoras**. Para evitar advertências de "conteúdo não original" ou bloqueio de alcance:

* **Sanitização de Metadados (`-map_metadata -1`):** Remove dados de câmeras, marcas, modelos de smartphone, datas e GPS.
* **Score Preventivo de Similaridade:** Avalia o tempo compartilhado entre os vídeos do lote e classifica cada criativo:
  * 🟢 **Verde:** Baixo compartilhamento de tempo (excelente para postar em sequência).
  * 🟡 **Amarelo:** Similaridade média (recomendado espaçar a postagem).
  * 🔴 **Vermelho:** Alta similaridade (risco de flag de duplicidade se postados no mesmo dia).
* **Fundo Desfocado Inteligente (*Blurred Background*):** Converte vídeos horizontais (16:9) em verticais (9:16) com desfoque cinematográfico dinâmico no fundo, sem esticar ou cortar a imagem.
* **Normalização de Áudio (`loudnorm`):** Nivela o volume sonoro de todos os clipes (-16 LUFS) para que não haja disparidade sonora entre o gancho e o meio.
* **Política de Resíduo Zero (Zero-Storage):** Ao atualizar ou sair da página, os arquivos do lote são purgados automaticamente, garantindo privacidade ao cliente e custo zero de armazenamento.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.12, FastAPI, Pydantic, Uvicorn
- **Motor de Vídeo:** FFmpeg 9.0.2 & FFprobe
- **Frontend:** React 19, Vite, Tailwind CSS, Lucide React
- **Padrões de Arquitetura:** Clean Code, separação estrita de domínios, sanitização binária (*Magic Bytes*) e proteção contra *Path Traversal*.

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- [Python 3.10+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)
- [FFmpeg](https://ffmpeg.org/) instalado no sistema

### 1. Clonar o repositório
```bash
git clone https://github.com/JulioAntunes00/ferramenta_remix_videos.git
cd ferramenta_remix_videos
```

### 2. Inicialização Rápida (Windows)
Dê um duplo clique no executável:
```text
iniciar_sistema.bat
```
O sistema iniciará o backend na porta `8000`, o frontend na porta `5173` e abrirá automaticamente no navegador em:
👉 `http://localhost:5173`

---

## 🗺️ Roadmap de Evolução (Próximos Passos)
- [x] Motor de permutação e concatenação combinatória
- [x] Sanitização Anti-Ban e remoção de metadados
- [x] Algoritmo de cálculo de score de similaridade
- [x] Upload via Arrastar e Soltar (Drag & Drop)
- [x] Fundo desfocado para vídeos horizontais
- [x] Purga automática de arquivos em encerramento de sessão
- [ ] Integração com banco de dados (Supabase / PostgreSQL)
- [ ] Autenticação de usuários (JWT / Magic Link)
- [ ] Assinatura e planos de cobrança (Stripe / Mercado Pago / Asaas)
- [ ] Fila de renderização em nuvem escalável (Redis + Celery)

---

Desenvolvido com foco em alta performance e escalabilidade.
