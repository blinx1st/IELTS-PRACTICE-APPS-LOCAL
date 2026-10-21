import type { Annotation, HighlightColor, TextRange } from './types';

type OldAnnotation = Omit<Annotation,'kind'> & {kind?:'highlight'|'note'};
const valid = (a:TextRange) => !!a&&typeof a.anchor==='string'&&Number.isInteger(a.start)&&Number.isInteger(a.end)&&a.start>=0&&a.end>a.start&&typeof a.text==='string';
const kindOf = (a:OldAnnotation) => a.kind||(a.note?'note':'highlight');
export const highlightColors: {value:HighlightColor;label:string}[] = [{value:'yellow',label:'Yellow'},{value:'orange',label:'Orange'},{value:'red',label:'Red'},{value:'green',label:'Green'},{value:'blue',label:'Blue'}];
const isColor=(c:unknown):c is HighlightColor=>highlightColors.some(x=>x.value===c);

function collectSegments(highlights:OldAnnotation[],ranges:TextRange[],paint?:HighlightColor|'clear') {
  const anchors=[...new Set([...highlights,...ranges].map(a=>a.anchor))].sort();
  const output:Annotation[]=[];
  for(const anchor of anchors){
    const old=highlights.filter(a=>a.anchor===anchor),selected=ranges.filter(a=>a.anchor===anchor);
    const points=[...new Set([...old,...selected].flatMap(a=>[a.start,a.end]))].sort((a,b)=>a-b);
    for(let i=0;i<points.length-1;i++){
      const start=points[i],end=points[i+1];
      const active=old.filter(a=>a.start<=start&&a.end>=end);
      const selection=selected.find(a=>a.start<=start&&a.end>=end);
      const colored=active.filter(a=>isColor(a.color));
      const legacyLevel=Math.min(3,active.reduce((s,a)=>s+(a.level||1),0));
      let color=colored.at(-1)?.color || (legacyLevel?(['yellow','orange','red'][legacyLevel-1] as HighlightColor):undefined);
      if(selection&&paint)color=paint==='clear'?undefined:paint;
      if(!color)continue;
      const source=selection||active[0];
      const text=source.text.slice(start-source.start,end-source.start);
      const previous=output.at(-1);
      if(previous?.anchor===anchor&&previous.end===start&&previous.color===color){
        previous.end=end;previous.text+=text;previous.id=`${anchor}:highlight:${previous.start}:${end}:${color}`;
      }else output.push({id:`${anchor}:highlight:${start}:${end}:${color}`,kind:'highlight',anchor,start,end,text,color});
    }
  }
  return output;
}

export function normalizeAnnotations(items:OldAnnotation[]=[]):Annotation[]{
  const all=items.filter(valid);
  const notes=all.filter(a=>kindOf(a)==='note').map(a=>({...a,kind:'note' as const,note:a.note||''}));
  return [...collectSegments(all.filter(a=>kindOf(a)==='highlight'),[]),...notes];
}

export function highlightSelection(items:Annotation[],ranges:TextRange[],color:HighlightColor|'clear'='yellow'):Annotation[]{
  const normalized=normalizeAnnotations(items);
  return [...collectSegments(normalized.filter(a=>a.kind==='highlight'),ranges.filter(valid),color),...normalized.filter(a=>a.kind==='note')];
}

export function annotatedSegments(anchor:string,text:string,items:Annotation[],offset=0){
  const applicable=normalizeAnnotations(items.filter(a=>a.anchor===anchor&&a.start<offset+text.length&&a.end>offset&&valid(a)));
  const points=[...new Set([0,text.length,...applicable.flatMap(a=>[Math.max(0,a.start-offset),Math.min(text.length,a.end-offset)])])].sort((a,b)=>a-b);
  return points.slice(0,-1).map((start,i)=>{
    const end=points[i+1],active=applicable.filter(a=>a.start<=start+offset&&a.end>=end+offset);
    return {start,text:text.slice(start,end),color:active.find(a=>a.kind==='highlight')?.color,note:active.find(a=>a.kind==='note')};
  });
}
