import {useEffect,useRef,useState,type ReactNode} from 'react';
import type {Group} from './types';

export type ListeningColumnsMode = 'auto'|'one'|'two';
const KEY='reading-room:listening-columns:v1';
export function useListeningColumns() {
  const [mode,setMode]=useState<ListeningColumnsMode>(()=>{try{const v=localStorage.getItem(KEY);return v==='one'||v==='two'?v:'auto';}catch{return 'auto';}});
  const set=(value:ListeningColumnsMode)=>{setMode(value);try{localStorage.setItem(KEY,value);}catch{/* Session preference still works. */}};
  return {mode,set};
}
export function ListeningColumnsPicker({mode,onChange}:{mode:ListeningColumnsMode;onChange:(v:ListeningColumnsMode)=>void}) {
  return <label className="listening-columns-picker">Layout <select aria-label="Listening question layout" value={mode} onChange={e=>onChange(e.target.value as ListeningColumnsMode)}>
    <option value="auto">Auto</option><option value="one">1 column</option><option value="two">2 columns</option>
  </select></label>;
}
export function splitQuestions<T>(items:T[]):T[][] {const middle=Math.ceil(items.length/2);return [items.slice(0,middle),items.slice(middle)];}
export function canSplitQuestions(group:Group,mode:ListeningColumnsMode) {
  const continuous=/flow[ -]?chart|complete (?:the |a )?(?:summary|notes|sentences|form)|label (?:the |a )?(?:map|plan|diagram)/i.test(group.instructions||'');
  return !group.layout&&!continuous&&['choice','matching'].includes(group.type)&&group.questions.length>=(mode==='two'?2:4)&&mode!=='one';
}
export function QuestionColumns<T>({items,split,render}:{items:T[];split:boolean;render:(item:T)=>ReactNode}) {
  return <div className={split?'question-columns':'question-single-column'}>{(split?splitQuestions(items):[items]).map((column,i)=><div className="question-column" key={i}>{column.map(render)}</div>)}</div>;
}
export function useQuestionPaneWidth() {
  const ref=useRef<HTMLDivElement>(null),[wide,setWide]=useState(false);
  useEffect(()=>{const pane=ref.current;if(!pane)return;const update=()=>setWide(pane.getBoundingClientRect().width>=1100);update();const observer=new ResizeObserver(update);observer.observe(pane);return()=>observer.disconnect();});
  return {ref,wide};
}
