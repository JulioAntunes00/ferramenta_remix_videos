import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Layers, 
  Flame, 
  Package, 
  Target, 
  Download, 
  RefreshCw, 
  ShieldCheck, 
  CheckCircle,
  PlaySquare,
  X
} from 'lucide-react';
import { UploadCard } from './components/UploadCard';
import { VideoResultCard } from './components/VideoResultCard';

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [uploads, setUploads] = useState({ hook: [], body: [], cta: [] });
  const [previewData, setPreviewData] = useState(null);
  const [renderStatus, setRenderStatus] = useState({ status: 'idle', progress: 0, results: [] });
  const [activeModalVideo, setActiveModalVideo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Inicializar nova sessão ao carregar a página ou resetar
  const initSession = async (oldSessionId = null) => {
    // Se havia uma sessão anterior (ex: ao clicar em "Novo Lote"), purga os arquivos dela
    if (oldSessionId) {
      try {
        fetch(`http://127.0.0.1:8000/api/session/purge/${oldSessionId}`, { 
          method: 'POST',
          keepalive: true 
        }).catch(() => {});
      } catch (e) {}
    }

    try {
      const res = await fetch('http://127.0.0.1:8000/api/session/create', { method: 'POST' });
      const data = await res.json();
      setSessionId(data.session_id);
      setUploads({ hook: [], body: [], cta: [] });
      setPreviewData(null);
      setRenderStatus({ status: 'idle', progress: 0, results: [] });
    } catch (err) {
      console.error('Erro ao conectar com API:', err);
    }
  };

  useEffect(() => {
    initSession();

    // Limpeza automática ao dar F5, fechar a aba ou sair do site
    const handleBeforeUnload = () => {
      if (sessionId) {
        // Envia beacon nativo para apagar imediatamente os arquivos do disco
        navigator.sendBeacon(`http://127.0.0.1:8000/api/session/purge/${sessionId}`);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [sessionId]);

  // Upload individual de arquivo
  const handleUpload = async (category, file) => {
    if (!sessionId) return;
    setIsLoading(true);
    const formData = new FormData();
    formData.append('category', category);
    formData.append('file', file);

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/upload/${sessionId}`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setUploads((prev) => ({
          ...prev,
          [category]: [
            ...prev[category],
            {
              name: data.filename,
              is_horizontal: data.is_horizontal,
              resolution: data.resolution,
              duration: data.duration,
            },
          ],
        }));
      } else {
        alert(data.detail || 'Erro ao enviar vídeo.');
      }
    } catch (err) {
      alert('Erro de conexão ao enviar vídeo.');
    } finally {
      setIsLoading(false);
    }
  };

  // Carregar pré-visualização de combinações e score
  useEffect(() => {
    const fetchPreview = async () => {
      if (!sessionId) return;
      if (uploads.hook.length > 0 && uploads.body.length > 0 && uploads.cta.length > 0) {
        try {
          const res = await fetch(`http://127.0.0.1:8000/api/preview/${sessionId}`);
          if (res.ok) {
            const data = await res.json();
            setPreviewData(data);
          }
        } catch (err) {
          console.error(err);
        }
      } else {
        setPreviewData(null);
      }
    };
    fetchPreview();
  }, [uploads, sessionId]);

  // Iniciar Renderização
  const handleStartRender = async () => {
    if (!sessionId) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/render/${sessionId}`, { method: 'POST' });
      if (res.ok) {
        setRenderStatus((prev) => ({ ...prev, status: 'processing', progress: 0 }));
      }
    } catch (err) {
      alert('Erro ao disparar renderização.');
    }
  };

  // Polling de status durante renderização
  useEffect(() => {
    let interval = null;
    if (renderStatus.status === 'processing') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://127.0.0.1:8000/api/status/${sessionId}`);
          if (res.ok) {
            const data = await res.json();
            setRenderStatus(data);
            if (data.status === 'completed' || data.status === 'error') {
              clearInterval(interval);
            }
          }
        } catch (err) {
          console.error(err);
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [renderStatus.status, sessionId]);

  const totalCalculated = uploads.hook.length * uploads.body.length * uploads.cta.length;

  return (
    <div className="min-h-screen pb-20">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-[#0f172a]/70 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg text-slate-100 tracking-tight flex items-center gap-2">
                Remix Vídeos <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 rounded-md">Anti-Ban 2.0</span>
              </span>
              <p className="text-xs text-slate-400">Escala de Criativos para TikTok, Reels e Shorts</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => initSession(sessionId)}
              className="px-3.5 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl border border-slate-700 transition-all flex items-center gap-2"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Novo Lote
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {/* Anti-Ban Status Banner */}
        <div className="mb-8 p-4 bg-gradient-to-r from-indigo-950/40 via-slate-900 to-slate-900 border border-indigo-500/20 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400 shrink-0">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100">Proteção Ativa de Metadados & Hash</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Os vídeos gerados têm seus dados de câmera e GPS limpos (`-map_metadata -1`) e áudio nivelado automaticamente.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 bg-slate-800/80 rounded-xl border border-slate-700 text-slate-300">
            <span>Trava de Segurança:</span>
            <span className="text-indigo-400 font-mono font-bold">Máx 64 variações (4x4x4)</span>
          </div>
        </div>

        {/* 3 Upload Columns */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <UploadCard
            title="1. Gancho (Hook)"
            subtitle="Primeiros 3 a 5 seg para reter"
            category="hook"
            icon={Flame}
            badgeColor="bg-rose-500"
            files={uploads.hook}
            onUpload={handleUpload}
            disabled={isLoading || renderStatus.status === 'processing'}
          />

          <UploadCard
            title="2. Apresentação (Meio)"
            subtitle="Demonstração ou explicação do produto"
            category="body"
            icon={Package}
            badgeColor="bg-indigo-500"
            files={uploads.body}
            onUpload={handleUpload}
            disabled={isLoading || renderStatus.status === 'processing'}
          />

          <UploadCard
            title="3. Chamada (CTA)"
            subtitle="Fechamento com chamada para ação"
            category="cta"
            icon={Target}
            badgeColor="bg-emerald-500"
            files={uploads.cta}
            onUpload={handleUpload}
            disabled={isLoading || renderStatus.status === 'processing'}
          />
        </div>

        {/* Barra de Ação & Pré-visualização Combinatória */}
        <div className="bg-[#131b2e] border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-400" />
                Matriz de Combinação
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                {totalCalculated > 0 ? (
                  <span>
                    <strong className="text-indigo-400">{uploads.hook.length}</strong> Ganchos × {' '}
                    <strong className="text-indigo-400">{uploads.body.length}</strong> Corpos × {' '}
                    <strong className="text-indigo-400">{uploads.cta.length}</strong> CTAs = {' '}
                    <strong className="text-emerald-400 font-semibold text-sm">{totalCalculated} vídeos únicos</strong>
                  </span>
                ) : (
                  'Envie pelo menos 1 clipe em cada coluna para habilitar a geração.'
                )}
              </p>
            </div>

            <div className="flex items-center gap-4 w-full md:w-auto">
              {renderStatus.status === 'completed' && (
                <a
                  href={`http://127.0.0.1:8000/api/download-zip/${sessionId}`}
                  className="w-full md:w-auto px-5 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm rounded-xl transition-all shadow-lg shadow-emerald-600/30 flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" /> Baixar Todos em .ZIP
                </a>
              )}

              <button
                onClick={handleStartRender}
                disabled={totalCalculated === 0 || renderStatus.status === 'processing' || isLoading}
                className="w-full md:w-auto px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-bold text-sm rounded-xl transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2"
              >
                {renderStatus.status === 'processing' ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Renderizando ({renderStatus.progress}%)
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" /> Gerar {totalCalculated || ''} Variações
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Barra de Progresso */}
          {renderStatus.status === 'processing' && (
            <div className="mt-6 pt-6 border-t border-slate-800">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                <span>Processando vídeos com Anti-Ban e loudnorm...</span>
                <span className="font-mono font-bold text-indigo-400">{renderStatus.completed} de {renderStatus.total} vídeos</span>
              </div>
              <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden border border-slate-800">
                <div
                  className="bg-indigo-600 h-full rounded-full transition-all duration-300 shadow-md shadow-indigo-500"
                  style={{ width: `${renderStatus.progress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Resultados & Análise Anti-Ban */}
        {(renderStatus.results.length > 0 || (previewData && previewData.combinations.length > 0)) && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-100">
                  {renderStatus.results.length > 0 ? 'Vídeos Gerados com Selo Anti-Ban' : 'Prévia de Similaridade das Combinações'}
                </h3>
                <p className="text-xs text-slate-400">Classificação algorítmica preventiva para postagem segura no TikTok.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {(renderStatus.results.length > 0 ? renderStatus.results : previewData.combinations).map((item, idx) => (
                <VideoResultCard
                  key={idx}
                  video={item}
                  onSelectPreview={(url) => setActiveModalVideo(`http://127.0.0.1:8000${url}`)}
                />
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Modal de Prévia do Vídeo */}
      {activeModalVideo && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#131b2e] border border-slate-800 rounded-2xl overflow-hidden max-w-sm w-full shadow-2xl relative">
            <div className="flex items-center justify-between p-3 border-b border-slate-800">
              <span className="text-xs font-bold text-slate-200">Prévia do Criativo</span>
              <button
                onClick={() => setActiveModalVideo(null)}
                className="p-1 text-slate-400 hover:text-white rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-3 bg-black flex justify-center">
              <video
                src={activeModalVideo}
                controls
                autoPlay
                className="rounded-xl max-h-[60vh] w-auto aspect-[9/16] object-cover"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
