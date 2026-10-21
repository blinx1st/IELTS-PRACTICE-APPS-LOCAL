import {useState} from 'react';
import {ArrowLeft,ArrowRight,Flag} from 'lucide-react';
import type {Passage,ResultRow} from './types';
import {adjacentQuestion,filterQuestions,type QuestionFilter} from './navigation';

type Props={units:Pick<Passage,'number'|'groups'>[];answers:Record<string,string>;flags:number[];current:number;activePart:number;results?:Record<number,ResultRow>;onJump:(n:number)=>void;onPart:(n:number)=>void};
export function ExamNavigation({units,answers,flags,current,activePart,results={},onJump,onPart}:Props){
  const [filter,setFilter]=useState<QuestionFilter>('all');
  const numbers=units.flatMap(p=>p.groups.flatMap(g=>g.questions.map(q=>q.number)));
  const visible=filterQuestions(numbers,answers,flags,filter),done=numbers.filter(n=>answers[n]?.trim()).length;
  const previous=adjacentQuestion(visible,current,-1),next=adjacentQuestion(visible,current,1);
  const marked=flags.filter(n=>numbers.includes(n)).length;
  return <footer className="exam-footer exam-navigation" aria-label="Question navigation">
    <div className="nav-overview"><div className="answer-progress"><strong>{done}<span> / {numbers.length}</span></strong><span>answered</span><div className="answer-progress-track" aria-hidden="true"><i style={{width:100*done/Math.max(1,numbers.length)+'%'}}/></div></div>
      <div className="question-filters" role="group" aria-label="Filter questions">{([{id:'all',label:'All questions',count:numbers.length},{id:'unanswered',label:'Unanswered',count:numbers.length-done},{id:'review',label:'For review',count:marked}] as const).map(f=><button key={f.id} aria-pressed={filter===f.id} className={filter===f.id?'selected':''} onClick={()=>setFilter(f.id)}>{f.id==='review'&&<Flag size={12}/>} {f.label} <b>{f.count}</b></button>)}</div>
      <div className="question-stepper"><span>Question <b>{current}</b></span><button className="icon-button" aria-label="Previous question" title="Previous question · Alt + Left" disabled={previous===undefined} onClick={()=>previous!==undefined&&onJump(previous)}><ArrowLeft size={17}/></button><button className="icon-button" aria-label="Next question" title="Next question · Alt + Right" disabled={next===undefined} onClick={()=>next!==undefined&&onJump(next)}><ArrowRight size={17}/></button></div>
    </div>
    <nav className="question-nav" aria-label="Parts and questions" style={{gridTemplateColumns:`repeat(${units.length},minmax(0,1fr))`}}>{units.map(part=>{
      const all=part.groups.flatMap(g=>g.questions.map(q=>q.number)),shown=all.filter(n=>visible.includes(n));
      return <div className={'nav-passage '+(part.number===activePart?'active-part':'')} key={part.number}><button className="nav-part-button" aria-current={part.number===activePart?'true':undefined} aria-label={'Go to Part '+part.number} onClick={()=>onPart(part.number)}><b>Part {part.number}</b><span>{all.filter(n=>answers[n]?.trim()).length}/{all.length}</span></button><div className="nav-numbers">{shown.map(n=><button key={n} aria-current={current===n?'step':undefined} aria-label={`Question ${n}, ${answers[n]?.trim()?'answered':'unanswered'}${flags.includes(n)?', marked for review':''}`} className={['nav-number',answers[n]?.trim()?'answered':'',current===n?'focused':'',results[n]?.status||''].join(' ')} onClick={()=>onJump(n)}>{n}{flags.includes(n)&&<i aria-hidden="true"/>}</button>)}{!shown.length&&<span className="nav-empty">—</span>}</div></div>;
    })}</nav>
    {visible.length===0&&<p className="nav-filter-empty" role="status">{filter==='review'?'No questions marked for review.':'All questions have an answer.'} <button onClick={()=>setFilter('all')}>Show all questions</button></p>}
  </footer>;
}
