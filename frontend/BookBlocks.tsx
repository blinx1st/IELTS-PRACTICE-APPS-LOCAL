import type { CSSProperties } from 'react';
import { Annotated } from './Annotated';
import { AnswerField } from './AnswerField';
import type { LayoutProps } from './QuestionLayouts';
import type { TextBlock } from './types';

export function BookBlocks({blocks,props,counts,anchor}:{blocks:TextBlock[];props:LayoutProps;counts:Record<number,number>;anchor:string}){
  return <>{blocks.map((b,bi)=>{
    const Tag=b.role==='title'?'h3':b.role==='section'?'h4':b.tag==='h3'?'h3':'p';
    const text=(s:string,i:number,start=0)=><Annotated key={i} id={b.anchors?.[i]||`${anchor}-${bi}-${i}`} offset={(b.offsets?.[i]||0)+start} text={s} annotations={props.attempt.annotations} onEdit={props.onAnnotation}/>;
    const contents=b.content.map((t,i)=>typeof t==='string'?text(b.labelEnd&&i===0?t.slice(b.labelEnd):t,i,b.labelEnd&&i===0?b.labelEnd:0):<AnswerField key={i} number={t.number} part={t.part} count={counts[t.number]||1} props={props}/>);
    return <Tag key={bi} className={'book-block '+(b.role||'body')+(b.marker?' has-marker':'')+(b.labelEnd?' paired-label':'')} style={{'--block-depth':b.depth||0,textAlign:b.align} as CSSProperties}>
      {b.marker&&<span className="book-marker" aria-hidden="true">{b.marker==='dash'?'–':b.marker==='circle'?'◦':'•'}</span>}
      {b.labelEnd&&typeof b.content[0]==='string'?<><span className="book-form-label">{text(b.content[0].slice(0,b.labelEnd),0)}</span><span className="book-form-value">{contents}</span></>:contents}
    </Tag>;
  })}</>;
}
