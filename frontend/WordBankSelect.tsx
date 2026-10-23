import {useEffect,useId,useRef,useState,type CSSProperties,type KeyboardEvent} from 'react';
import {createPortal} from 'react-dom';
import type {Option} from './types';

/** Keep the native value/control for forms; draw the popup in the page so it
 * behaves consistently across Windows browsers and independently scrolling panes. */
export function WordBankSelect({id,label,value,disabled,options,onChange}:{id:string;label:string;value:string;disabled:boolean;options:Option[];onChange:(value:string)=>void}){
  const listId=useId(),control=useRef<HTMLSelectElement>(null),popup=useRef<HTMLDivElement>(null);
  const [position,setPosition]=useState<CSSProperties|null>(null),[active,setActive]=useState(0);
  const choices=[{value:'',label:'Select an answer'},...options.map(o=>({...o,label:o.value+'. '+o.label}))];
  const opened=!!position&&!disabled;
  const open=()=>{
    if(disabled||!control.current)return;
    const r=control.current.getBoundingClientRect(),width=Math.min(window.innerWidth-16,Math.max(250,r.width,Math.min(440,...choices.map(o=>o.label.length*8+36))));
    const height=Math.min(280,choices.length*38+12),below=window.innerHeight-r.bottom-12;
    setPosition({position:'fixed',left:Math.max(8,Math.min(r.left,window.innerWidth-width-8)),width,maxHeight:Math.min(height,Math.max(below,r.top-8)),fontSize:getComputedStyle(control.current).fontSize,fontFamily:getComputedStyle(control.current).fontFamily,
      ...(below>=height||below>r.top?{top:r.bottom+5}:{bottom:window.innerHeight-r.top+5})});
    setActive(Math.max(0,choices.findIndex(o=>o.value===value)));
    control.current.focus({preventScroll:true});
  };
  const choose=(index:number)=>{onChange(choices[index].value);setPosition(null);control.current?.focus({preventScroll:true});};
  useEffect(()=>{
    if(!opened)return;
    const outside=(e:PointerEvent)=>{if(!control.current?.contains(e.target as Node)&&!popup.current?.contains(e.target as Node))setPosition(null);};
    const move=(e:Event)=>{if(!popup.current?.contains(e.target as Node))setPosition(null);};
    document.addEventListener('pointerdown',outside,true);document.addEventListener('scroll',move,true);window.addEventListener('resize',move);
    return()=>{document.removeEventListener('pointerdown',outside,true);document.removeEventListener('scroll',move,true);window.removeEventListener('resize',move);};
  },[opened]);
  useEffect(()=>{if(opened)popup.current?.querySelector('[data-active="true"]')?.scrollIntoView({block:'nearest'});},[active,opened]);
  useEffect(()=>{if(disabled)setPosition(null);},[disabled]);
  const key=(e:KeyboardEvent<HTMLSelectElement>)=>{
    if(e.key==='Tab'){setPosition(null);return;}
    if(e.key==='Escape'){e.preventDefault();setPosition(null);return;}
    if(['ArrowDown','ArrowUp','Enter',' ','Home','End'].includes(e.key)){
      e.preventDefault();
      if(!opened){open();return;}
      if(e.key==='Enter'||e.key===' ')choose(active);
      else setActive(e.key==='Home'?0:e.key==='End'?choices.length-1:Math.max(0,Math.min(choices.length-1,active+(e.key==='ArrowDown'?1:-1))));
    }else if(opened&&e.key.length===1){
      e.preventDefault();const index=choices.findIndex(o=>o.value.toLowerCase()===e.key.toLowerCase());if(index>=0)setActive(index);
    }
  };
  return <><select ref={control} id={id} aria-label={label} value={value} disabled={disabled}
    aria-expanded={opened} aria-controls={opened?listId:undefined} aria-activedescendant={opened?listId+'-'+active:undefined}
    onPointerDown={e=>{e.preventDefault();opened?setPosition(null):open();}}
    onMouseDown={e=>e.preventDefault()} onKeyDown={key} onChange={e=>{onChange(e.target.value);setPosition(null);}}>
    {choices.map(o=><option value={o.value} key={o.value}>{o.label}</option>)}
  </select>{opened&&createPortal(<div ref={popup} id={listId} role="listbox" aria-label={'Choices for '+label.toLowerCase()} className="word-bank-popup" style={position!}>
    {choices.map((o,i)=><button type="button" role="option" tabIndex={-1} id={listId+'-'+i} key={o.value} aria-selected={o.value===value} data-active={i===active} onPointerDown={e=>e.preventDefault()} onClick={()=>choose(i)}>{o.label}</button>)}
  </div>,document.body)}</>;
}
