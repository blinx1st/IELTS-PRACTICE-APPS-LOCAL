import type { CSSProperties } from 'react';
import { Flag } from 'lucide-react';
import type { Attempt } from './types';
import type { LayoutProps } from './QuestionLayouts';

export function answerPartsFor(a:Pick<Attempt,'answers'|'answerParts'>,number:number,count:number){
  const stored=a.answerParts?.[number];
  if(stored)return Array.from({length:count},(_,i)=>stored[i]||'');
  const words=(a.answers[number]||'').trim().split(/\s+/);
  return Array.from({length:count},(_,i)=>i===count-1?words.slice(i).join(' '):words[i]||'');
}

/** Fixed widths depend on the task, never on the answer being typed. */
export function answerWidth(wordLimit?:number){return wordLimit===1?12:wordLimit===2?16:wordLimit===3?20:16;}

export function LayoutFeedback({props}:{props:LayoutProps}){
  if(!props.group.questions.some(q=>props.results[q.number]))return null;
  return <div className="flow-feedback">{props.group.questions.map(q=>{
    const row=props.results[q.number];
    return row&&<div key={q.number} className={'answer-feedback '+row.status}>{q.number} · {row.status==='correct'?'Đúng':row.status==='blank'?'Bỏ trống':'Sai'} · {row.accepted.join(' / ')}</div>;
  })}</div>;
}

export function AnswerField({number:n,part=0,count=1,props}:{number:number;part?:number;count?:number;props:LayoutProps}){
  const {group:g,attempt:a,editable,results,onAnswer,onAnswerPart,onFlag,onFocus}=props;
  const layout=g.layout,override=layout&&'answerWidths' in layout?layout.answerWidths?.[n]:undefined;
  const options=g.type==='matching'?g.options:undefined;
  const width=override??(options?.length?Math.min(30,Math.max(18,...options.map(o=>o.value.length+o.label.length+3))):answerWidth(g.wordLimit));
  const id=`answer-${n}${count>1?'-part-'+part:''}`;
  const value=count>1?answerPartsFor(a,n,count)[part]:a.answers[n]||'';
  const label=`Answer ${n}${count>1?', part '+(part+1):''}`;
  return <span className={'answer-field inline-blank '+(results[n]?.status||'')} data-question={n} onFocus={()=>onFocus(n)} style={{'--answer-width':width+'ch'} as CSSProperties}>
    {part===0&&<label htmlFor={id} className="answer-number">{n}</label>}
    {options?.length?<select id={id} aria-label={label} value={value} disabled={!editable} onChange={e=>onAnswer(n,e.target.value)}><option value="">Select an answer</option>{options.map(o=><option value={o.value} key={o.value}>{o.value}. {o.label}</option>)}</select>:<input id={id} aria-label={label} value={value} disabled={!editable} spellCheck={false} autoComplete="off" maxLength={1000} onChange={e=>count>1?onAnswerPart(n,part,count,e.target.value):onAnswer(n,e.target.value)}/>}
    {part===0&&<button type="button" className={'flag-button '+(a.flags.includes(n)?'flagged':'')} title="Mark for review" aria-label={'Mark question '+n+' for review'} aria-pressed={a.flags.includes(n)} disabled={!editable} onClick={()=>onFlag(n)}><Flag size={14}/></button>}
  </span>;
}
