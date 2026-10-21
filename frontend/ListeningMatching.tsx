import {Annotated} from './Annotated';
import {QuestionColumns} from './ListeningColumns';
import {Flag} from 'lucide-react';
import type {LayoutProps} from './QuestionLayouts';

export function ListeningMatching(props:LayoutProps&{twoColumns?:boolean}) {
  const {group:g,attempt:a,editable,results,onAnswer,onFocus,onFlag,onAnnotation,twoColumns=false}=props;
  const options=<div className="listening-option-list"><strong>List of options</strong>{g.options?.map(o=><p key={o.value}><b>{o.value}</b><Annotated id={g.id+'-option-'+o.value} text={o.label} annotations={a.annotations} onEdit={onAnnotation}/></p>)}</div>;
  const rows=<QuestionColumns items={g.questions} split={twoColumns} render={q=><div key={q.number} data-question={q.number} onFocus={()=>onFocus(q.number)} className={'matching-answer-row '+(results[q.number]?.status||'')}>
    <span className="question-index">{q.number}</span><Annotated id={g.id+'-q'+q.number} text={q.text} annotations={a.annotations} onEdit={onAnnotation}/>
    <select aria-label={'Answer '+q.number} value={a.answers[q.number]||''} disabled={!editable} onChange={e=>onAnswer(q.number,e.target.value)}><option value="">—</option>{g.options?.map(o=><option key={o.value} value={o.value}>{o.value}</option>)}</select>
    <button aria-label={'Mark question '+q.number+' for review'} aria-pressed={a.flags.includes(q.number)} className={'flag-button '+(a.flags.includes(q.number)?'flagged':'')} disabled={!editable} onClick={()=>onFlag(q.number)}><Flag size={14}/></button>
    {results[q.number]&&<small className={'answer-feedback '+results[q.number].status}>{results[q.number].status==='correct'?'Đúng':results[q.number].status==='blank'?'Bỏ trống':'Sai'} · {results[q.number].accepted.join(' / ')}</small>}
  </div>}/>;
  return twoColumns?<div className="listening-matching-split">{options}{rows}</div>:<div className="listening-matching">{rows}{options}</div>;
}
