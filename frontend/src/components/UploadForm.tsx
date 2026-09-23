import { useRef, useState } from 'react';
import { UploadCloud, X, FileSpreadsheet, Download } from 'lucide-react';
import { api } from '../api';
type Result = {imported:number;skipped:number;warnings:string[]};
export default function UploadForm({close,done}:{close:()=>void;done:(message:string)=>Promise<void>}) {
  const input = useRef<HTMLInputElement>(null);
  const [busy,setBusy] = useState(false), [error,setError] = useState(''), [file,setFile] = useState<File|null>(null);
  async function upload(demo=false) {
    if(!demo && !file) return;
    if(file && !demo && file.size > 2*1024*1024) {setError('Максимальный размер файла — 2 МБ.');return;}
    setBusy(true);setError('');
    try {
      const body = new FormData(); if(file) body.append('file',file);
      const result = await api<Result>(demo?'/demo':'/upload',{method:'POST',...(demo?{}:{body})});
      await done(`Добавлено: ${result.imported}. Уже загружено: ${result.skipped}. ${result.warnings.join(' ')}`);
      close();
    } catch(e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  return <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="upload-title"><button className="icon-button modal-close" onClick={close} disabled={busy} aria-label="Закрыть"><X size={20}/></button><div className="eyebrow">ВАШИ ФИНАНСЫ, НА ОДНОМ ЭКРАНЕ</div><h2 id="upload-title">Добавьте транзакции</h2><p className="muted">Загрузите выписку, а мы разложим расходы по категориям.</p><button className="dropzone" disabled={busy} onClick={()=>input.current?.click()} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();if(!busy) setFile(e.dataTransfer.files[0]??null);}}><UploadCloud size={34}/><strong>{file?file.name:'Перетащите CSV или выберите файл'}</strong><span>UTF-8 или Windows-1251 · до 2 МБ · до 1 000 строк</span></button><input ref={input} type="file" accept=".csv" className="sr-only" onChange={e=>setFile(e.target.files?.[0]??null)}/><div className="format"><FileSpreadsheet size={18}/><div><strong>дата, описание, сумма, тип</strong><p>2026-09-01, Кофейня, 1500, расход</p><small>Тип необязателен: без него минус — расход, плюс — доход. Валюта всего файла должна быть одной.</small></div></div>{error&&<div className="error" role="alert">{error}</div>}<button className="primary full" disabled={busy||!file} onClick={()=>upload()}>{busy?'Обрабатываем транзакции…':'Загрузить и проанализировать'}</button><div className="demo-choice"><span>Пока нет выписки?</span><button className="text-button" disabled={busy} onClick={()=>upload(true)}>Попробовать 80 демо-транзакций →</button></div><a className="download" href="/api/demo.csv"><Download size={14}/>Скачать пример CSV</a></section></div>;
}
