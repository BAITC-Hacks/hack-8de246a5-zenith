import { ArrowUpRight, Lightbulb } from 'lucide-react';
export default function InsightCard({title,text,index,tip=false}:{title:string;text:string;index:number;tip?:boolean}) {
 return <article className={'insight-card '+(tip?'tip':'')}><div className="insight-number">{tip?<Lightbulb size={17}/>:String(index+1).padStart(2,'0')}<ArrowUpRight size={16}/></div><h3>{title}</h3><p>{text}</p></article>;
}
