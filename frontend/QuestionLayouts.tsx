import type { Annotation, Attempt, Group, ResultRow } from './types';
import { Annotated } from './Annotated';
import { Flag, X } from 'lucide-react';

export type LayoutProps={group:Group;attempt:Attempt;editable:boolean;results:Record<number,ResultRow>;onAnswer:(n:number,v:string)=>void;onAnswerPart:(n:number,part:number,count:number,v:string)=>void;onFlag:(n:number)=>void;onFocus:(n:number)=>void;onAnnotation:(a:Annotation)=>void};

export function answerPartsFor(a:Pick<Attempt,'answers'|'answerParts'>,number:number,count:number){
  const stored=a.answerParts?.[number];
  if(stored)return Array.from({length:count},(_,i)=>stored[i]||'');
  const words=(a.answers[number]||'').trim().split(/\s+/);
  return Array.from({length:count},(_,i)=>i===count-1?words.slice(i).join(' '):words[i]||'');
}

const norm=(s:string)=>s.normalize('NFKC').trim().toUpperCase();
function FlagButton({n,props}:{n:number;props:LayoutProps}){
  return <button type="button" className={'flag-button '+(props.attempt.flags.includes(n)?'flagged':'')} aria-label={'Mark question '+n+' for review'} aria-pressed={props.attempt.flags.includes(n)} title="Mark for review" disabled={!props.editable} onClick={()=>props.onFlag(n)}><Flag size={14}/></button>;
}

export function InteractiveTable(props:LayoutProps){
  const {group:g,attempt:a,editable,onAnswer,onAnswerPart,onFocus,onAnnotation,results}=props;
  if(g.layout?.kind!=='table')return null;
  const {rows,caption}=g.layout;
  const counts:Record<number,number>={};
  rows.forEach(r=>r.cells.forEach(c=>c.content.forEach(item=>{if(typeof item!=='string')counts[item.number]=Math.max(counts[item.number]||0,(item.part||0)+1);})));
  const columns=Math.max(...rows.map(r=>r.cells.reduce((sum,c)=>sum+(c.colSpan||1),0)));
  const widths=columns===2?[32,68]:columns===3?[19,31,50]:Array(columns).fill(100/columns);
  return <div className="table-scroll" tabIndex={0} aria-label={'Answer table for '+g.heading}><table className="completion-table">
    {caption&&<caption>{caption}</caption>}<colgroup>{widths.map((w,i)=><col key={i} style={{width:w+'%'}}/>)}</colgroup>
    <tbody>{rows.map((row,ri)=><tr key={ri}>{row.cells.map((cell,ci)=>{
      const Cell=cell.header?'th':'td';
      return <Cell key={ci} rowSpan={cell.rowSpan} colSpan={cell.colSpan}>{cell.content.map((item,ti)=>{
        if(typeof item==='string')return <Annotated key={ti} id={`${g.id}-cell-${ri}-${ci}-${ti}`} text={item} annotations={a.annotations} onEdit={onAnnotation}/>;
        const n=item.number,part=item.part||0,count=counts[n],first=part===0,row=results[n],id=`answer-${n}${count>1?'-part-'+part:''}`;
        const value=count>1?answerPartsFor(a,n,count)[part]:a.answers[n]||'';
        return <span key={ti} className={'table-answer '+(row?.status||'')} data-question={n} onFocus={()=>onFocus(n)}><span className="table-blank">{first&&<label htmlFor={id}>{n}</label>}<input id={id} aria-label={`Answer ${n}${count>1?', part '+(part+1):''}`} value={value} disabled={!editable} maxLength={1000} autoComplete="off" spellCheck={false} onChange={e=>count>1?onAnswerPart(n,part,count,e.target.value):onAnswer(n,e.target.value)}/>{first&&<FlagButton n={n} props={props}/>}</span>{first&&row&&<span className="table-feedback">{row.status==='correct'?'Đúng':row.status==='blank'?'Bỏ trống':'Sai'} · {row.accepted.join(' / ')}</span>}</span>;
      })}</Cell>;
    })}</tr>)}</tbody>
  </table></div>;
}

export function MatchingMatrix(props:LayoutProps){
  const {group:g,attempt:a,editable,results,onAnswer,onFocus,onAnnotation}=props;
  if(g.layout?.kind!=='matrix')return null;
  const {rows,matchingKind}=g.layout,options=g.options||[];
  return <>
    {matchingKind==='headings'&&<div className="heading-list"><strong>List of headings</strong>{options.map(o=><div key={o.value}><b>{o.value}</b><Annotated id={g.id+'-heading-'+o.value} text={o.label} annotations={a.annotations} onEdit={onAnnotation}/></div>)}</div>}
    <div className="matrix-scroll" tabIndex={0} aria-label={'Answer grid for '+g.heading}><table className="matching-matrix" style={{minWidth:(matchingKind==='headings'?170:250)+options.length*34}}>
      <thead><tr><th scope="col">Question</th>{options.map(o=><th scope="col" key={o.value}>{o.value}</th>)}</tr></thead>
      <tbody>{rows.map(q=>{
        const result=results[q.number],value=a.answers[q.number]||'';
        return <tr key={q.number} data-question={q.number} onFocus={()=>onFocus(q.number)}><th scope="row"><div className="matrix-prompt"><span className="question-index">{q.number}</span><span><Annotated id={g.id+'-q'+q.number} text={q.text} annotations={a.annotations} onEdit={onAnnotation}/>{result&&<small className={'matrix-feedback '+result.status}>{result.status==='correct'?'Đúng':result.status==='blank'?'Bỏ trống':'Sai'} · Đáp án: {result.accepted.join(' / ')}</small>}</span><span className="matrix-actions"><FlagButton n={q.number} props={props}/>{editable&&value&&<button className="clear-matrix" aria-label={'Clear answer '+q.number} title="Clear answer" onClick={()=>onAnswer(q.number,'')}><X size={12}/></button>}</span></div></th>{options.map(o=>{
          const selected=value===o.value,correct=!!result&&result.accepted.some(x=>norm(x)===norm(o.value));
          const style=correct?'correct-option':result&&selected?'incorrect-option':selected?'selected-option':'';
          return <td key={o.value} className={style}><label><input type="radio" name={g.id+'-q'+q.number} aria-label={`Question ${q.number}, ${o.value}`} value={o.value} checked={selected} disabled={!editable} onChange={()=>onAnswer(q.number,o.value)}/></label></td>;
        })}</tr>;
      })}</tbody>
    </table></div>
  </>;
}
