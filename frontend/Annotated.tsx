import type { Annotation } from './types';
import { annotatedSegments } from './annotations';

export function Annotated({id,text,annotations,onEdit,offset=0}:{id:string;text:string;annotations:Annotation[];onEdit:(a:Annotation)=>void;offset?:number}){
  return <span data-text-id={id} data-text-start={offset}>{annotatedSegments(id,text,annotations,offset).map(part=>{
    const content=part.note?<span className="note-anchor" title={part.note.note||'Note'} onClick={e=>{e.stopPropagation();onEdit(part.note!);}}>{part.text}</span>:part.text;
    return part.color?<mark key={part.start} className={'highlight-color-'+part.color}>{content}</mark>:<span key={part.start}>{content}</span>;
  })}</span>;
}
