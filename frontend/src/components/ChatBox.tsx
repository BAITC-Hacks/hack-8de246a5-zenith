import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { api } from '../api';
export default function ChatBox({month}:{month:string}) {
 const [message,setMessage]=useState(''),[reply,setReply]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 async function send(e:React.FormEvent) {e.preventDefault();if(!message.trim())return;setBusy(true);setError('');try{const r=await api<{reply:string}>('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({month,message})});setReply(r.reply);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 return <section className="panel chat-panel" id="assistant"><div className="section-heading"><div><h2><Sparkles size={19}/> Спросите ассистента</h2><p>Ответы с учётом выбранного месяца</p></div><span className="pill">Claude Sonnet 4.6</span></div><form onSubmit={send}><input aria-label="Вопрос ассистенту" value={message} onChange={e=>setMessage(e.target.value)} maxLength={1000} placeholder="На чём я могу сэкономить в этом месяце?"/><button className="primary" disabled={busy||!message.trim()} aria-label="Отправить вопрос">{busy?'…':<Send size={18}/>}</button></form>{error&&<p className="error" role="alert">{error}</p>}{reply&&<p className="chat-reply" aria-live="polite">{reply}</p>}<small className="muted">Для чата нужен API-ключ. Ассистент видит суммы по категориям и топ-5 расходов.</small></section>;
}
