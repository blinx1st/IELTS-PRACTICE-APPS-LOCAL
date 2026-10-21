import type { Annotation } from './types';
import { annotatedSegments } from './annotations';

export function Annotated({id,text,annotations,onEdit}:{id:string;text:string;annotations:Annotation[];onEdit:(a:Annotation)=>void}){
  return <span data-text-id={id}>{annotatedSegments(id,text,annotations).map(part=>{
    const content=part.note?<span className="note-anchor" title={part.note.note||'Note'} onClick={e=>{e.stopPropagation();onEdit(part.note!);}}>{part.text}</span>:part.text;
    return part.level?<mark key={part.start} className={'highlight-level-'+part.level}>{content}</mark>:<span key={part.start}>{content}</span>;
  })}</span>;
}
