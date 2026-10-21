import {Flag} from 'lucide-react';
import {useState} from 'react';
import { Annotated } from './Annotated';
import type { LayoutProps } from './QuestionLayouts';
import { AnswerField, LayoutFeedback } from './AnswerField';
import { BookBlocks } from './BookBlocks';

export function ExtendedLayout(props:LayoutProps){
  const [zoom,setZoom]=useState(100);
  const {group:g,attempt:a,editable,onAnswer,onFocus,onAnnotation,onFlag}=props;
  const layout=g.layout;
  const tokens=layout?.kind==='flow'?layout.blocks.flatMap(b=>b.content):[];
  const counts:Record<number,number>={};tokens.forEach(t=>{if(typeof t!=='string')counts[t.number]=Math.max(counts[t.number]||0,(t.part||0)+1);});
  const blank=(n:number,part=0)=><AnswerField number={n} part={part} count={counts[n]||1} props={props}/>;
  const feedback=<LayoutFeedback props={props}/>;
  if(layout?.kind==='flow'){
    const options=g.type==='matching'&&g.options?.length?<div className="flow-options" aria-label="List of options">{g.options.map(o=><div key={o.value}><b>{o.value}</b><Annotated id={g.id+'-option-'+o.value} text={o.label} annotations={a.annotations} onEdit={onAnnotation}/></div>)}</div>:null;
    // Legacy blocks keep their original identifiers as well as their old list markers.
    const blocks=layout.blocks.map((b,i)=>({...b,anchors:b.anchors||b.content.map((_,ti)=>`${g.id}-flow-${i}-${ti}`),marker:b.marker||(b.tag==='li'?'bullet' as const:undefined)}));
    return <div className={'listening-flow completion-flow document-flow '+(layout.variant||'notes')}>
      {layout.optionsPosition!=='after'&&options}<div className={'book-document frame-'+(layout.frame||'box')}><BookBlocks blocks={blocks} props={props} counts={counts} anchor={g.id+'-flow'}/></div>{layout.optionsPosition==='after'&&options}{feedback}
    </div>;
  }
  if(layout?.kind==='diagram')return <><button className="text-button diagram-zoom" onClick={()=>setZoom(zoom===100?150:100)}>Zoom diagram · {zoom}%</button><div className="diagram-scroll"><div className="listening-diagram" style={{width:zoom+'%',maxWidth:'none'}}><img src={layout.image.url} alt={'Diagram for '+g.heading}/>{layout.labels.map(l=><div className="diagram-answer" key={l.number} data-question={l.number} onFocus={()=>onFocus(l.number)} style={{left:l.x*100+'%',top:l.y*100+'%',width:(l.width||.18)*100+'%'}}>{g.options?.length?<label><span>{l.number}</span><select aria-label={'Answer '+l.number} disabled={!editable} value={a.answers[l.number]||''} onChange={e=>onAnswer(l.number,e.target.value)}><option value="">—</option>{g.options.map(o=><option value={o.value} key={o.value}>{o.value}</option>)}</select><button className={'flag-button '+(a.flags.includes(l.number)?'flagged':'')} aria-label={'Mark question '+l.number+' for review'} aria-pressed={a.flags.includes(l.number)} disabled={!editable} onClick={()=>onFlag(l.number)}><Flag size={14}/></button></label>:blank(l.number)}</div>)}</div></div>{g.options?.length&&<div className="diagram-options">{g.options.map(o=><span key={o.value}><b>{o.value}</b> {o.label}</span>)}</div>}{feedback}</>;
  return null;
}
