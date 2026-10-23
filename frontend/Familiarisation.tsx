import {useEffect,useRef,useState,type CSSProperties,type MouseEvent} from 'react';
import {ArrowLeft,ArrowRight,BookOpen,Check,CheckCircle2,Clock3,Flag,Headphones,HelpCircle,Highlighter,Maximize2,RotateCcw,Settings2,StickyNote,Volume2} from 'lucide-react';
import {Modal} from './Dialog';
import {Annotated} from './Annotated';
import {highlightSelection} from './annotations';
import {SelectionTools} from './SelectionTools';
import {ListeningMatching} from './ListeningMatching';
import {ListeningColumnsPicker,useListeningColumns,useQuestionPaneWidth,canSplitQuestions} from './ListeningColumns';
import {InteractiveTable,MatchingMatrix,type LayoutProps} from './QuestionLayouts';
import {ExamNavigation} from './ExamNavigation';
import {DisplaySettings,ExamHelp,FAMILIARISATION_KEY,useExamPreferences} from './ExamSupport';
import type {Annotation,Attempt,Group,Skill,TextRange,Test,HighlightColor} from './types';

const table:Group={id:'demo-table',type:'completion',wordLimit:1,heading:'Question 1',instructions:'Complete the table below. Choose ONE WORD ONLY from the text.',body:'',questions:[{number:1,text:''}],layout:{kind:'table',columnWidths:[35,65],minWidthCh:36,rows:[{cells:[{header:true,content:['Place']},{header:true,content:['Available to borrow']}]},{cells:[{content:['The community library']},{content:['Books and ',{number:1}]}]}]}};
const matrix:Group={id:'demo-match',type:'matching',heading:'Question 3',instructions:'Choose the correct letter, A or B.',body:'',questions:[{number:3,text:'A place for studying quietly'}],options:[{value:'A',label:'The garden'},{value:'B',label:'The reading room'}],layout:{kind:'matrix',matchingKind:'paragraphs',rows:[{number:3,text:'A place for studying quietly'}]}};
const listeningMatch:Group={id:'demo-listening-match',type:'matching',heading:'Questions 3–6',instructions:'Choose the correct letter, A or B.',body:'',questions:[{number:3,text:'A place for studying quietly'},{number:4,text:'A place for meeting friends'},{number:5,text:'A place for reading books'},{number:6,text:'A place for talking outside'}],options:[{value:'A',label:'The garden'},{value:'B',label:'The reading room'}]};
const text='The community library opens at nine every morning. Visitors can borrow books and magazines. A quiet reading room is available upstairs. The garden is a space for meeting friends and talking.';
const demo:Test={id:'interface-demo',book:0,test:0,title:'Get familiar with your test screen',version:'1',verification:{status:'demo'},passages:[{id:'demo-p1',number:1,title:'A visit to the community library',paragraphs:[{id:'demo-text',text}],groups:[table,{id:'demo-statement',type:'tfng',heading:'Question 2',instructions:'Choose TRUE, FALSE or NOT GIVEN.',body:'',questions:[{number:2,text:'The library opens at nine.'}]}]},{id:'demo-p2',number:2,title:'Finding your way around',paragraphs:[{id:'demo-text-2',text:'The reading room is for quiet study. People can meet and talk in the garden.'}],groups:[matrix]}]};

export function Familiarisation({onBack}:{onBack:()=>void}){
  const [skill,setSkill]=useState<Skill>('reading'),[part,setPart]=useState(1),[current,setCurrent]=useState(1),[answers,setAnswers]=useState<Record<string,string>>({}),[flags,setFlags]=useState<number[]>([]),[annotations,setAnnotations]=useState<Annotation[]>([]);
  const [dialog,setDialog]=useState<'help'|'display'|'note'|'notes'|'finish'|null>(null),[note,setNote]=useState<Annotation|null>(null),[noteText,setNoteText]=useState(''),[complete,setComplete]=useState(false);
  const [selection,setSelection]=useState<{x:number;y:number;ranges:TextRange[]}|null>(null),[split,setSplit]=useState(50);
  const {preferences,update}=useExamPreferences();
  const columns=useListeningColumns();
  const {ref:questionPane,wide:questionPaneWide}=useQuestionPaneWidth();
  const preview:Test=skill==='listening'?{...demo,passages:[demo.passages[0],{...demo.passages[1],groups:[listeningMatch]}]}:demo;
  const panels=useRef<HTMLDivElement>(null),audio=useRef<HTMLAudioElement>(null);
  const first=!!answers[1]?.trim(),second=!!answers[2],marked=flags.length>0,third=!!answers[3];
  const tasks=[{done:first,title:'Điền vào chỗ trống',detail:'Trong bảng câu 1, nhập magazines.'},{done:second,title:'Chọn đáp án',detail:'Câu 2: chọn TRUE trong danh sách.'},{done:marked,title:'Cắm cờ xem lại',detail:'Bấm cờ cạnh một câu; thử bộ lọc For review bên dưới.'},{done:third,title:'Điều hướng sang Part 2',detail:'Chọn All questions, bấm số 3 ở footer rồi chọn B trong bảng matching.'}];
  const done=tasks.filter(t=>t.done).length,step=tasks.find(t=>!t.done);
  const attempt:Attempt={id:'demo',testId:demo.id,title:demo.title,book:0,testNumber:0,mode:'practice',passage:null,numbers:skill==='listening'?[1,2,3,4,5,6]:[1,2,3],startedAt:0,updatedAt:0,deadline:null,duration:null,remaining:null,status:'active',revision:0,answers,answerParts:{},flags,annotations,currentPassage:part,test:preview,result:null,serverNow:0,skill};
  const flag=(n:number)=>setFlags(old=>old.includes(n)?old.filter(x=>x!==n):[...old,n]);
  const jump=(n:number)=>{setPart(n>=3?2:1);setCurrent(n);setTimeout(()=>{const target=panels.current?.querySelector<HTMLElement>(`[data-question="${n}"]`);target?.scrollIntoView({block:'center'});target?.querySelector<HTMLElement>('input,select')?.focus({preventScroll:true});},60);};
  useEffect(()=>{
    const key=(e:KeyboardEvent)=>{if(dialog||!e.altKey||!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();jump(Math.min(skill==='listening'?6:3,Math.max(1,current+(e.key==='ArrowRight'?1:-1))));};
    window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key);
  });
  const openNote=(a:Annotation)=>{setNote(a);setNoteText(a.note||'');setDialog('note');};
  const props=(group:Group):LayoutProps=>({group,attempt,editable:true,results:{},onAnswer:(n,v)=>setAnswers(old=>({...old,[n]:v})),onAnswerPart:()=>{},onFocus:setCurrent,onFlag:flag,onAnnotation:openNote});
  const select=(e:MouseEvent)=>{
    if((e.target as Element).closest('input,select,textarea,button,[role="combobox"],[role="listbox"]'))return;
    const s=window.getSelection();if(!s?.rangeCount||s.isCollapsed){setSelection(null);return;}
    const range=s.getRangeAt(0),ranges:TextRange[]=[];
    panels.current?.querySelectorAll<HTMLElement>('[data-text-id]').forEach(el=>{
      if(!range.intersectsNode(el)||!el.textContent)return;
      let start=0,end=el.textContent.length;const before=range.cloneRange();before.selectNodeContents(el);
      if(el.contains(range.startContainer)){before.setEnd(range.startContainer,range.startOffset);start=before.toString().length;}
      if(el.contains(range.endContainer)){const after=range.cloneRange();after.selectNodeContents(el);after.setEnd(range.endContainer,range.endOffset);end=after.toString().length;}
      if(end>start)ranges.push({anchor:el.dataset.textId!,start:start+Number(el.dataset.textStart||0),end:end+Number(el.dataset.textStart||0),text:el.textContent.slice(start,end)});
    });
    if(ranges.length){const r=range.getBoundingClientRect();setSelection({x:Math.max(8,Math.min(innerWidth-350,r.left)),y:Math.max(90,r.top-48),ranges});}
  };
  const annotate=(kind:HighlightColor|'clear'|'note')=>{
    if(!selection)return;
    if(kind==='note')openNote({...selection.ranges[0],id:crypto.randomUUID(),kind:'note',note:''});
    else setAnnotations(old=>highlightSelection(old,selection.ranges,kind));
    window.getSelection()?.removeAllRanges();setSelection(null);
  };
  const reset=()=>{setAnswers({});setFlags([]);setAnnotations([]);setPart(1);setCurrent(1);setComplete(false);};
  const finish=()=>{try{localStorage.setItem(FAMILIARISATION_KEY,'completed');}catch{}setComplete(true);setDialog(null);};
  return <div className={`exam-shell familiarisation-shell theme-${preferences.contrast} ${skill==='listening'?'listening-shell':''}`}>
    <header className="exam-header"><button className="icon-button" aria-label="Back to library" onClick={onBack}><ArrowLeft size={20}/></button><div className="exam-identity"><strong>Get familiar with your test screen</strong><span>INTERFACE PRACTICE · NO SCORE</span></div><span className="demo-untimed"><Clock3 size={17}/>Untimed</span><div className="exam-header-actions"><button className="button secondary small" onClick={reset}><RotateCcw size={15}/>Try again</button><button className="button small" onClick={()=>setDialog('finish')}>Finish practice<ArrowRight size={15}/></button></div></header>
    <div className={'familiarisation-coach '+(complete?'complete':'')}><div className="coach-heading"><span className="coach-icon">{complete?<CheckCircle2 size={22}/>:<BookOpen size={22}/>}</span><div><strong>{complete?'Bạn đã sẵn sàng làm bài.':step?.title||'Bạn đã thử đủ các thao tác chính.'}</strong><p>{complete?'Chọn đề Cambridge trong thư viện để bắt đầu.':step?.detail||'Thử bôi chọn chữ để Highlight hoặc Note, rồi bấm Finish practice.'}</p></div></div><div className="coach-progress" aria-label={`Đã thử ${done} trên 4 thao tác`}>{tasks.map((t,i)=><span key={t.title} title={t.title} className={t.done?'done':''}>{t.done?<Check size={14}/>:i+1}</span>)}</div>{complete&&<button className="button small" onClick={onBack}>Chọn đề Cambridge<ArrowRight size={15}/></button>}</div>
    <div className="demo-context"><span>Bài tập thao tác · Không lưu vào lịch sử</span><div role="group" aria-label="Preview skill"><button aria-pressed={skill==='reading'} onClick={()=>{setSkill('reading');setPart(1);setCurrent(1);}}>Reading</button><button aria-pressed={skill==='listening'} onClick={()=>{setSkill('listening');setPart(1);setCurrent(1);}}>Listening</button></div></div>
    {skill==='listening'&&<div className="listening-player demo-audio"><Headphones size={19}/><strong>Sound check</strong><audio ref={audio} src="/audio-check.wav"/><button className="button secondary small" onClick={()=>void audio.current?.play().catch(()=>{})}>Test sound</button><Volume2 size={16}/><input type="range" min="0" max="1" step="0.05" defaultValue="0.85" aria-label="Demo volume" onChange={e=>{if(audio.current)audio.current.volume=+e.target.value;}}/><span>Âm thử tai nghe. Khi làm đề Listening, audio thật nằm ở thanh này.</span></div>}
    <div className="exam-toolbar"><div className="passage-tabs">{preview.passages.map(p=><button key={p.number} className={p.number===part?'selected':''} aria-pressed={p.number===part} onClick={()=>jump(p.number===1?1:3)}>Part {p.number}<span>{p.groups.flatMap(g=>g.questions).filter(q=>answers[q.number]?.trim()).length}/{p.groups.flatMap(g=>g.questions).length}</span></button>)}</div><div className="reading-tools">{skill==='listening'&&<ListeningColumnsPicker mode={columns.mode} onChange={columns.set}/>}<button onClick={()=>setDialog('display')}><Settings2 size={16}/>Display</button><button onClick={()=>setDialog('help')}><HelpCircle size={16}/>Help</button><button onClick={()=>setDialog('notes')}><StickyNote size={16}/>Notes <small>{annotations.filter(a=>a.kind==='note').length||''}</small></button><button aria-label="Fullscreen" title="Fullscreen" onClick={()=>{if(document.fullscreenElement)void document.exitFullscreen();else void document.documentElement.requestFullscreen().catch(()=>{});}}><Maximize2 size={17}/></button></div></div>
    <div className="exam-panels" ref={panels} onMouseUp={select} style={{'--reading-size':preferences.fontSize+'px'} as CSSProperties}>
      {skill==='reading'&&<><section className="reading-pane" style={{width:split+'%'}} aria-label="Reading passage"><div className="pane-caption"><span>READING PASSAGE {part}</span><span>Sample text</span></div><h1>{preview.passages[part-1].title}</h1><div className="passage-text"><p><Annotated id={part===1?'demo-text':'demo-text-2'} text={preview.passages[part-1].paragraphs[0].text} annotations={annotations} onEdit={openNote}/></p></div><div className="demo-reading-tip"><Highlighter size={17}/>Bôi chọn một đoạn chữ để thử Highlight hoặc Note. Kéo thanh giữa để đổi độ rộng hai cột.</div></section><div className="splitter" role="separator" aria-label="Resize reading and question panes" aria-orientation="vertical" aria-valuemin={32} aria-valuemax={68} aria-valuenow={split} tabIndex={0} onKeyDown={e=>{if(e.key==='ArrowLeft'){e.preventDefault();setSplit(x=>Math.max(32,x-2));}if(e.key==='ArrowRight'){e.preventDefault();setSplit(x=>Math.min(68,x+2));}}} onPointerDown={e=>e.currentTarget.setPointerCapture(e.pointerId)} onPointerMove={e=>{if(e.buttons!==1)return;const r=panels.current?.getBoundingClientRect();if(r)setSplit(Math.round(Math.max(32,Math.min(68,100*(e.clientX-r.left)/r.width))));}}><i/><i/><i/></div></>}
      <section ref={questionPane} className="questions-pane" aria-label="Questions" style={{width:skill==='listening'?'100%':100-split+'%'}}>
        {skill==='listening'&&<p className="demo-reading-tip">Dùng đoạn mẫu này để thử thao tác điền: {preview.passages[part-1].paragraphs[0].text}</p>}
        {part===1?<><div className="group-heading"><h2>{table.heading}</h2></div><p className="group-instructions">{table.instructions}</p><InteractiveTable {...props(table)}/><div className="question-item" data-question={2} onFocus={()=>setCurrent(2)}><div className="question-label"><span className="question-index">2</span><span className="question-text">The library opens at nine.</span><button aria-label="Mark question 2 for review" aria-pressed={flags.includes(2)} className={'flag-button '+(flags.includes(2)?'flagged':'')} onClick={()=>flag(2)}><Flag size={17}/></button></div><p>Choose TRUE, FALSE or NOT GIVEN.</p><select aria-label="Answer 2" value={answers[2]||''} onChange={e=>setAnswers(old=>({...old,2:e.target.value}))}><option value="">Select an answer</option>{['TRUE','FALSE','NOT GIVEN'].map(v=><option key={v}>{v}</option>)}</select></div></>:<><h2>{skill==='listening'?listeningMatch.heading:matrix.heading}</h2><p>{matrix.instructions}</p>{skill==='reading'&&<div className="demo-options">A · The garden<br/>B · The reading room</div>}{skill==='listening'?<ListeningMatching {...props(listeningMatch)} twoColumns={questionPaneWide&&canSplitQuestions(listeningMatch,columns.mode)}/>:<MatchingMatrix {...props(matrix)}/>}</>}
      </section>
    </div>
    <ExamNavigation units={preview.passages} answers={answers} flags={flags} current={current} activePart={part} onJump={jump} onPart={n=>jump(n===1?1:3)}/>
    {selection&&<SelectionTools x={selection.x} y={selection.y} onAction={annotate}/>}
    {dialog==='help'&&<Modal title="Help · Interface practice" onClose={()=>setDialog(null)} wide><ExamHelp skill={skill} practice/></Modal>}
    {dialog==='display'&&<Modal title="Display settings" onClose={()=>setDialog(null)}><DisplaySettings value={preferences} onChange={update}/></Modal>}
    {dialog==='notes'&&<Modal title="Your notes" onClose={()=>setDialog(null)}>{annotations.some(a=>a.kind==='note')?annotations.filter(a=>a.kind==='note').map(a=><div className="annotation-card" key={a.id}><blockquote>{a.text}</blockquote><p>{a.note}</p><button className="text-button" onClick={()=>openNote(a)}>Edit note</button></div>):<p>Select text, then choose Note. Highlights do not appear in this list.</p>}</Modal>}
    {dialog==='note'&&note&&<Modal title="Note for selected text" onClose={()=>setDialog(null)}><blockquote>{note.text}</blockquote><label className="demo-note-label">Your note<textarea aria-label="Your note" rows={4} value={noteText} onChange={e=>setNoteText(e.target.value)}/></label><div className="modal-actions"><button className="button secondary" onClick={()=>{setAnnotations(old=>old.filter(a=>a.id!==note.id));setDialog(null);}}>Delete note</button><button className="button" onClick={()=>{setAnnotations(old=>[...old.filter(a=>a.id!==note.id),{...note,note:noteText}]);setDialog(null);}}>Save note</button></div></Modal>}
    {dialog==='finish'&&<Modal title="Hoàn thành làm quen giao diện" onClose={()=>setDialog(null)}><p>Đã thử <b>{done}/4</b> thao tác. Đây là bài làm quen, không chấm điểm và không tạo lượt làm trong lịch sử.</p><ol className="demo-checklist">{tasks.map(t=><li key={t.title}>{t.done?<CheckCircle2 size={18}/>:<span className="demo-check-empty"/>}{t.title}</li>)}</ol><div className="modal-actions"><button className="button secondary" onClick={()=>setDialog(null)}>Thử tiếp</button><button className="button" onClick={finish}>Tôi đã sẵn sàng<ArrowRight size={16}/></button></div></Modal>}
  </div>;
}
