import {useEffect,useRef,type ReactNode} from 'react';
import {X} from 'lucide-react';

export function Modal({title,children,onClose,wide=false}:{title:string;children:ReactNode;onClose:()=>void;wide?:boolean}){
  const box=useRef<HTMLDivElement>(null),close=useRef(onClose);close.current=onClose;
  useEffect(()=>{
    const old=document.activeElement as HTMLElement|null;
    const key=(e:KeyboardEvent)=>{
      if(e.key==='Escape'){e.stopPropagation();close.current();}
      if(e.key==='Tab'){
        const controls=Array.from(box.current?.querySelectorAll<HTMLElement>('button,input,select,textarea,a[href],[tabindex="0"]')||[]).filter(el=>!el.hasAttribute('disabled')&&el.getClientRects().length>0);
        const first=controls[0],last=controls.at(-1);
        if(e.shiftKey&&(document.activeElement===first||document.activeElement===box.current)){e.preventDefault();last?.focus();}
        if(!e.shiftKey&&(document.activeElement===last||document.activeElement===box.current)){e.preventDefault();first?.focus();}
      }
    };
    box.current?.focus();document.addEventListener('keydown',key);
    return()=>{document.removeEventListener('keydown',key);if(old?.isConnected)old.focus();};
  },[]);
  return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}><div ref={box} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title} className={'modal '+(wide?'wide':'')}><div className="modal-heading"><h2>{title}</h2><button className="icon-button" aria-label="Đóng" onClick={onClose}><X size={20}/></button></div>{children}</div></div>;
}
