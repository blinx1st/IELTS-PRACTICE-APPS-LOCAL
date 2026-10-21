import {Eraser,StickyNote} from 'lucide-react';
import {highlightColors} from './annotations';
import type {HighlightColor} from './types';

export function SelectionTools({x,y,onAction}:{x:number;y:number;onAction:(action:HighlightColor|'note'|'clear')=>void}) {
  return <div className="selection-menu color-selection-menu" role="toolbar" aria-label="Selected text tools"
    style={{left:Math.max(8,Math.min(window.innerWidth-390,x)),top:Math.max(8,Math.min(window.innerHeight-100,y))}}
    onMouseDown={e=>e.preventDefault()}>
    <div className="highlight-palette" role="group" aria-label="Highlight color">
      {highlightColors.map(c=><button key={c.value} className={'highlight-swatch highlight-color-'+c.value}
        title={c.label} aria-label={'Highlight '+c.label.toLowerCase()} onClick={()=>onAction(c.value)}><span className="sr-only">{c.label}</span></button>)}
    </div>
    <button onClick={()=>onAction('note')}><StickyNote size={15}/>Note</button>
    <button onClick={()=>onAction('clear')}><Eraser size={15}/>Clear highlight</button>
  </div>;
}
