import React from 'react';
import { ShieldCheck, AlertCircle, AlertTriangle, Play, Download } from 'lucide-react';

export const VideoResultCard = ({ video, onSelectPreview }) => {
  const getBadgeConfig = (badge) => {
    switch (badge) {
      case 'VERDE':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: ShieldCheck,
          label: 'Excelente (Baixa similaridade)',
        };
      case 'AMARELO':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: AlertTriangle,
          label: 'Atenção (Espaçar postagem)',
        };
      case 'VERMELHO':
      default:
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          icon: AlertCircle,
          label: 'Risco de Duplicidade (TikTok)',
        };
    }
  };

  const badgeConfig = getBadgeConfig(video.score_badge);
  const Icon = badgeConfig.icon;

  return (
    <div className="bg-[#131b2e] border border-slate-800 hover:border-slate-700/80 rounded-2xl p-4 flex flex-col justify-between transition-all group">
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="font-bold text-slate-200 text-sm">{video.file_name || video.id}</span>
          <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${badgeConfig.bg}`}>
            <Icon className="w-3.5 h-3.5" />
            <span>{video.score_badge}</span>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
          {video.recommendation}
        </p>

        <div className="grid grid-cols-3 gap-1.5 p-2 bg-slate-900/60 rounded-xl text-[10px] text-slate-300 font-mono mb-3 border border-slate-800/40">
          <div className="truncate">🎣 {video.hook}</div>
          <div className="truncate">📦 {video.body}</div>
          <div className="truncate">🎯 {video.cta}</div>
        </div>
      </div>

      <div className="flex items-center gap-2 pt-2 border-t border-slate-800/60">
        {video.file_url && (
          <>
            <button
              onClick={() => onSelectPreview(video.file_url)}
              className="flex-1 py-1.5 px-3 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all"
            >
              <Play className="w-3.5 h-3.5" /> Ver Vídeo
            </button>
            <a
              href={`http://127.0.0.1:8000${video.file_url}`}
              download
              className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition-all"
              title="Baixar MP4"
            >
              <Download className="w-4 h-4" />
            </a>
          </>
        )}
      </div>
    </div>
  );
};
