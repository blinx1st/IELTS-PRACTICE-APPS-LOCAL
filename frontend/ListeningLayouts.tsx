import {useState} from 'react';
import { Annotated } from './Annotated';
import { answerPartsFor, type LayoutProps } from './QuestionLayouts';
import type { TableCell } from './types';

export function ExtendedLayout(props:LayoutProps){
  const [zoom,setZoom]=useState(100);
  const {group:g,attempt:a,editable,onAnswer,onAnswerPart,onFocus,onAnnotation,results,onFlag}=props;
  const layout=g.layout;
  const tokens=layout?.kind==='flow'?layout.blocks.flatMap(b=>b.content):[];
  const counts:Record<number,number>={};tokens.forEach(t=>{if(typeof t!=='string')counts[t.number]=Math.max(counts[t.number]||0,(t.part||0)+1);});
  const blank=(n:number,part=0)=>{
    const count=counts[n]||1,row=results[n];
    return <span className={'inline-blank '+(row?.status||'')} data-question={n} onFocus={()=>onFocus(n)}><label htmlFor={`answer-${n}-${part}`}>{n}</label><input id={`answer-${n}-${part}`} aria-label={`Answer ${n}${count>1?', part '+(part+1):''}`} value={count>1?answerPartsFor(a,n,count)[part]:a.answers[n]||''} disabled={!editable} spellCheck={false} autoComplete="off" maxLength={1000} onChange={e=>count>1?onAnswerPart(n,part,count,e.target.value):onAnswer(n,e.target.value)}/>{part===0&&<button className={'flag-button '+(a.flags.includes(n)?'flagged':'')} title="Mark for review" aria-label={'Mark question '+n+' for review'} aria-pressed={a.flags.includes(n)} disabled={!editable} onClick={()=>onFlag(n)}>⚑</button>}</span>;
  };
  const content=(items:TableCell['content'],anchor:string)=>items.map((t,i)=>typeof t==='string'?<Annotated key={i} id={`${anchor}-${i}`} text={t} annotations={a.annotations} onEdit={onAnnotation}/>:<span key={i}>{blank(t.number,t.part)}</span>);
  const feedback=<div className="flow-feedback">{g.questions.map(q=>results[q.number]&&<div key={q.number} className={'answer-feedback '+results[q.number].status}>{q.number} · {results[q.number].status==='correct'?'Đúng':results[q.number].status==='blank'?'Bỏ trống':'Sai'} · {results[q.number].accepted.join(' / ')}</div>)}</div>;
  if(layout?.kind==='flow')return <div className="listening-flow">{layout.blocks.map((b,i)=>{const Tag=b.tag==='h3'?'h3':'p';return <Tag className={b.tag==='li'?'flow-bullet':''} key={i}>{content(b.content,`${g.id}-flow-${i}`)}</Tag>;})}{feedback}</div>;
  if(layout?.kind==='diagram')return <><button className="text-button diagram-zoom" onClick={()=>setZoom(zoom===100?150:100)}>Zoom diagram · {zoom}%</button><div className="diagram-scroll"><div className="listening-diagram" style={{width:zoom+'%',maxWidth:'none'}}><img src={layout.image.url} alt={'Diagram for '+g.heading}/>{layout.labels.map(l=><div className="diagram-answer" key={l.number} data-question={l.number} onFocus={()=>onFocus(l.number)} style={{left:l.x*100+'%',top:l.y*100+'%',width:(l.width||.18)*100+'%'}}>{g.options?.length?<label><span>{l.number}</span><select aria-label={'Answer '+l.number} disabled={!editable} value={a.answers[l.number]||''} onChange={e=>onAnswer(l.number,e.target.value)}><option value="">—</option>{g.options.map(o=><option value={o.value} key={o.value}>{o.value}</option>)}</select><button className={'flag-button '+(a.flags.includes(l.number)?'flagged':'')} aria-label={'Mark question '+l.number+' for review'} aria-pressed={a.flags.includes(l.number)} disabled={!editable} onClick={()=>onFlag(l.number)}>⚑</button></label>:blank(l.number)}</div>)}</div></div>{g.options?.length&&<div className="diagram-options">{g.options.map(o=><span key={o.value}><b>{o.value}</b> {o.label}</span>)}</div>}{feedback}</>;
  return null;
}
