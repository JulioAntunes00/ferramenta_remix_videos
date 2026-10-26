import React, { useRef, useState } from 'react';
import { UploadCloud, CheckCircle2, Film, ArrowDownCircle } from 'lucide-react';

export const UploadCard = ({
  title,
  category,
  subtitle,
  icon: Icon,
  badgeColor,
  files,
  onUpload,
  disabled
}) => {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(category, e.target.files[0]);
      e.target.value = '';
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !isFull) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled || isFull) return;

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.includes('video') || file.name.endsWith('.mp4') || file.name.endsWith('.mov')) {
        onUpload(category, file);
      } else {
        alert('Por favor, arraste apenas arquivos de vídeo (MP4 ou MOV).');
      }
    }
  };

  const isFull = files.length >= 4;

  return (
    <div 
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`bg-[#131b2e] border transition-all duration-200 rounded-2xl p-5 flex flex-col justify-between shadow-xl relative ${
        isDragging 
          ? 'border-indigo-500 bg-indigo-950/20 ring-2 ring-indigo-500/30 scale-[1.01]' 
          : 'border-slate-800 hover:border-slate-700'
      }`}
    >
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div className={`p-2 rounded-xl ${badgeColor} bg-opacity-20 flex items-center justify-center`}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-100 text-base">{title}</h3>
              <p className="text-xs text-slate-400">{subtitle}</p>
            </div>
          </div>
          <span className="text-xs font-bold px-2.5 py-1 bg-slate-800 text-slate-300 rounded-full border border-slate-700">
            {files.length}/4
          </span>
        </div>

        {/* Área Interativa com Drag and Drop */}
        <div className="space-y-2 mt-4 min-h-[140px]">
          {files.length === 0 ? (
            <div
              onClick={() => !disabled && !isFull && fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center h-[140px] group ${
                isDragging 
                  ? 'border-indigo-400 bg-indigo-500/10' 
                  : 'border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/20'
              }`}
            >
              {isDragging ? (
                <>
                  <ArrowDownCircle className="w-8 h-8 text-indigo-400 animate-bounce mb-2" />
                  <p className="text-xs font-bold text-indigo-300">Solte o clipe aqui!</p>
                </>
              ) : (
                <>
                  <UploadCloud className="w-8 h-8 text-slate-500 group-hover:text-indigo-400 transition-colors mb-2" />
                  <p className="text-xs font-medium text-slate-300">Arraste e solte ou clique aqui</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">MP4 ou MOV (máx 4 vídeos)</p>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {files.map((file, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2.5 bg-slate-900/80 border border-slate-800/80 rounded-xl text-xs"
                >
                  <div className="flex items-center gap-2 overflow-hidden pr-2">
                    <Film className="w-4 h-4 text-indigo-400 shrink-0" />
                    <div className="flex flex-col truncate">
                      <span className="truncate text-slate-300 font-medium">{file.name}</span>
                      {file.is_horizontal && (
                        <span className="text-[10px] text-amber-400 font-semibold flex items-center gap-1">
                          📐 Horizontal (Fundo Desfocado Ativo)
                        </span>
                      )}
                    </div>
                  </div>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                </div>
              ))}
              
              {!isFull && (
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => fileInputRef.current?.click()}
                  className={`w-full py-2.5 border border-dashed rounded-xl text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
                    isDragging 
                      ? 'border-indigo-400 bg-indigo-500/10 text-indigo-300' 
                      : 'border-slate-800 hover:border-slate-700 hover:bg-slate-800/30 text-slate-400'
                  }`}
                >
                  <UploadCloud className="w-3.5 h-3.5" /> 
                  {isDragging ? 'Solte para adicionar' : 'Arraste ou clique para adicionar mais um'}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="video/mp4,video/quicktime"
        className="hidden"
        onChange={handleFileChange}
        disabled={disabled || isFull}
      />
    </div>
  );
};
