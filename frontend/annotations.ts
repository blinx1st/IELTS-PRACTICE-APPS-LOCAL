import type { Annotation, TextRange } from './types';

type OldAnnotation = Omit<Annotation,'kind'> & {kind?:'highlight'|'note'};
const valid = (a:TextRange) => !!a&&typeof a.anchor==='string'&&Number.isInteger(a.start)&&Number.isInteger(a.end)&&a.start>=0&&a.end>a.start&&typeof a.text==='string';
const kindOf = (a:OldAnnotation) => a.kind||(a.note?'note':'highlight');

function collectSegments(highlights:OldAnnotation[],ranges:TextRange[],action:'normalize'|'add'|'clear') {
  const anchors=[...new Set([...highlights,...ranges].map(a=>a.anchor))].sort();
  const output:Annotation[]=[];
  for(const anchor of anchors){
    const old=highlights.filter(a=>a.anchor===anchor),selected=ranges.filter(a=>a.anchor===anchor);
    const points=[...new Set([...old,...selected].flatMap(a=>[a.start,a.end]))].sort((a,b)=>a-b);
    for(let i=0;i<points.length-1;i++){
      const start=points[i],end=points[i+1];
      const active=old.filter(a=>a.start<=start&&a.end>=end);
      const selection=selected.find(a=>a.start<=start&&a.end>=end);
      let level=Math.min(3,active.reduce((s,a)=>s+(a.level||1),0));
      if(selection&&action!=='normalize')level=action==='clear'?0:Math.min(3,level+1);
      if(!level)continue;
      const source=selection||active[0];
      const text=source.text.slice(start-source.start,end-source.start);
      const previous=output.at(-1);
      if(previous?.anchor===anchor&&previous.end===start&&previous.level===level){
        previous.end=end;previous.text+=text;previous.id=`${anchor}:highlight:${previous.start}:${end}:${level}`;
      }else output.push({id:`${anchor}:highlight:${start}:${end}:${level}`,kind:'highlight',anchor,start,end,text,level:level as 1|2|3});
    }
  }
  return output;
}

export function normalizeAnnotations(items:OldAnnotation[]=[]):Annotation[]{
  const all=items.filter(valid);
  const notes=all.filter(a=>kindOf(a)==='note').map(a=>({...a,kind:'note' as const,note:a.note||''}));
  return [...collectSegments(all.filter(a=>kindOf(a)==='highlight'),[],'normalize'),...notes];
}

export function highlightSelection(items:Annotation[],ranges:TextRange[],clear=false):Annotation[]{
  const normalized=normalizeAnnotations(items);
  return [...collectSegments(normalized.filter(a=>a.kind==='highlight'),ranges.filter(valid),clear?'clear':'add'),...normalized.filter(a=>a.kind==='note')];
}

export function annotatedSegments(anchor:string,text:string,items:Annotation[]){
  const applicable=items.filter(a=>a.anchor===anchor&&a.end<=text.length&&valid(a));
  const points=[...new Set([0,text.length,...applicable.flatMap(a=>[a.start,a.end])])].sort((a,b)=>a-b);
  return points.slice(0,-1).map((start,i)=>{
    const end=points[i+1],active=applicable.filter(a=>a.start<=start&&a.end>=end);
    return {start,text:text.slice(start,end),level:active.find(a=>a.kind==='highlight')?.level||0,note:active.find(a=>a.kind==='note')};
  });
}
