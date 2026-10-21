import {useEffect,useRef,useState} from 'react';
import {Play,Pause,RotateCcw,Volume2,FileText,Headphones} from 'lucide-react';
import {post} from './api';
import type {Attempt,PlayerState,TestCard} from './types';
import {Modal} from './Dialog';
import {StartOrientation} from './ExamSupport';

export function ListeningStartModal({test,onClose,onStart,onFamiliarise}:{test:TestCard;onClose:()=>void;onStart:(a:Attempt)=>void;onFamiliarise?:()=>void}){
  const [mode,setMode]=useState('exam'),[part,setPart]=useState(1),[busy,setBusy]=useState(false),[error,setError]=useState('');
  return <Modal title={`Cambridge ${test.book} · Test ${test.test}`} onClose={onClose} wide><div className="listening-start"><p className="muted">Chọn cách luyện Listening hôm nay. Audio chỉ chạy sau bước kiểm tra âm thanh.</p>{onFamiliarise&&<StartOrientation onOpen={onFamiliarise}/>}<div className="mode-options">{[{id:'exam',name:'Thi sát thật',text:'40 câu · nghe một lần · 1×'},{id:'full',name:'Luyện cả đề',text:'40 câu · audio tự do'},{id:'part',name:'Luyện từng Part',text:'10 câu · audio tự do'}].map(m=><button key={m.id} className={'mode '+(mode===m.id?'selected':'')} aria-pressed={mode===m.id} onClick={()=>setMode(m.id)}><Headphones/><strong>{m.name}</strong><small>{m.text}</small></button>)}</div>{mode==='part'&&<label className="practice-select">Chọn Part<select value={part} onChange={e=>setPart(+e.target.value)}>{test.passages.map(p=><option key={p.number} value={p.number}>Part {p.number} · {p.title}</option>)}</select></label>}<div className="info-box">{mode==='exam'?'Không tua hoặc dừng thủ công. Sau 4 Parts có 2 phút kiểm tra đáp án. Nếu có sự cố, app giữ vị trí và ghi nhận bài bị gián đoạn.':'Không giới hạn thời gian. Có Pause, chỉnh tốc độ 0,5–2×, tua và lặp đoạn A–B. Transcript mở sau khi chấm.'}</div>{error&&<p role="alert">{error}</p>}<div className="modal-actions"><button className="button secondary" disabled={busy} onClick={onClose}>Quay lại</button><button className="button" disabled={busy} onClick={()=>{setBusy(true);void post<Attempt>('/attempts',{testId:test.id,skill:'listening',mode:mode==='exam'?'exam':'practice',part:mode==='part'?part:null}).then(onStart).catch(e=>{setError(e.message);setBusy(false);});}}>{busy?'Đang mở…':'Mở bài Listening'}</button></div></div></Modal>;
}

export const clockText=(s:number)=>{s=Math.max(0,Math.ceil(s));return (s>=3600?Math.floor(s/3600)+':':'')+String(Math.floor(s/60)%60).padStart(2,'0')+':'+String(s%60).padStart(2,'0');};
export function listeningRemaining(a:Attempt,position=a.player?.position||0){
  const p=a.player!;if(p.phase==='check')return p.reviewRemaining;if(p.phase==='finished')return 0;
  return 120+a.test.passages.filter(u=>u.number>=p.part).reduce((sum,u)=>sum+(u.audio!.end??u.audio!.duration)-(u.number===p.part?position:u.audio!.start||0),0);
}
type Props={attempt:Attempt;displayPart:number;receive:(a:Attempt)=>void;flush:()=>Promise<void>;error:(s:string)=>void;onClock:(s:number)=>void;onTranscript:()=>void;onPlayingPart:(part:number)=>void};
export function ListeningPlayer({attempt:a,displayPart,receive,flush,error,onClock,onTranscript,onPlayingPart}:Props){
  const media=useRef<HTMLAudioElement>(null),current=useRef(a),receiveRef=useRef(receive),clockRef=useRef(onClock),errorRef=useRef(error);
  current.current=a;receiveRef.current=receive;clockRef.current=onClock;errorRef.current=error;
  const [confirmPractice,setConfirmPractice]=useState(false);
  const [position,setPosition]=useState(a.player!.position),[volume,setVolume]=useState(.85),[busy,setBusy]=useState(false),[owned,setOwned]=useState(false),[localPaused,setLocalPaused]=useState(false);
  const readonly=['submitted','graded'].includes(a.status),strict=!readonly&&a.mode==='exam';
  const reviewPlayer=useRef({position:0,rate:1,loopA:null as number|null,loopB:null as number|null});
  const [reviewSettings,setReviewSettings]=useState(reviewPlayer.current);
  const activePart=readonly?displayPart:a.player!.part,unit=a.test.passages.find(u=>u.number===activePart)!;
  const asset=unit.audio!,start=asset.start||0,end=asset.end??asset.duration;
  const client=useRef(''),flight=useRef(false),transition=useRef(false),autoPlay=useRef(false),lastSave=useRef(Date.now()),mounted=useRef(true),restored=useRef(false),faulted=useRef(false);
  const draftKey='reading-room:player-draft:'+a.id;
  const buffering=useRef<ReturnType<typeof setTimeout>|null>(null);
  const clearBuffering=()=>{if(buffering.current){clearTimeout(buffering.current);buffering.current=null;}};
  if(!client.current)client.current=crypto.randomUUID();
  const pauseLocally=()=>{media.current?.pause();setLocalPaused(true);};
  const send=async(action:string,extra:Record<string,unknown>={})=>{
    const c=current.current;
    const payload={action,clientId:client.current,position:media.current&&media.current.readyState>=1?media.current.currentTime:undefined,...extra};
    try{
      if(faulted.current&&!['claim','interrupt','release'].includes(action)){
        await post<Attempt>('/attempts/'+c.id+'/player',{...payload,action:'interrupt'});faulted.current=false;
      }
      const response=await post<Attempt>('/attempts/'+c.id+'/player',payload);
      if(action==='interrupt')faulted.current=false;
      if(mounted.current){receiveRef.current(response);setOwned(true);lastSave.current=Date.now();localStorage.removeItem(draftKey);}
      return response;
    }catch(e){
      faulted.current=true;pauseLocally();localStorage.setItem(draftKey,JSON.stringify({...c.player,position:media.current?.currentTime??c.player!.position}));
      errorRef.current((e as Error).message+' Audio paused; your last position is kept in this browser.');throw e;
    }
  };
  const sendRef=useRef(send);sendRef.current=send;
  useEffect(()=>{
    mounted.current=true;
    if(!readonly)void sendRef.current('claim',{position:undefined}).then(()=>setLocalPaused(false)).catch(()=>setOwned(false));
    const heartbeat=setInterval(()=>{
      const c=current.current;if(['submitted','graded'].includes(c.status)||flight.current||transition.current)return;
      flight.current=true;
      void (async()=>{try{if(c.player!.phase==='check'&&c.player!.reviewRemaining<4)await flush();await sendRef.current('checkpoint');}catch{}finally{flight.current=false;}})();
    },2000);
    const release=()=>{
      const c=current.current;
      if(['submitted','graded'].includes(c.status))return;
      const payload={action:'release',clientId:client.current,position:media.current?.currentTime??c.player!.position};
      localStorage.setItem(draftKey,JSON.stringify({...c.player,position:payload.position}));
      void fetch('/api/attempts/'+c.id+'/player',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),keepalive:true}).catch(()=>{});
    };
    window.addEventListener('pagehide',release);
    return()=>{mounted.current=false;clearInterval(heartbeat);clearBuffering();media.current?.pause();release();window.removeEventListener('pagehide',release);};
  },[a.id]);
  useEffect(()=>{
    const tick=setInterval(()=>{
      const c=current.current,p=c.player!,m=media.current;
      const pos=m?.currentTime??p.position;if(m)setPosition(pos);
      const extra=p.running&&!localPaused?Math.min(2,(Date.now()-lastSave.current)/1000):0;
      clockRef.current(c.mode==='exam'?(p.phase==='check'?Math.max(0,p.reviewRemaining-extra):listeningRemaining(c,pos)):p.elapsed+extra);
      if(p.running&&!localPaused)localStorage.setItem(draftKey,JSON.stringify({...p,position:pos}));
    },250);
    return()=>clearInterval(tick);
  },[a.id,localPaused]);
  useEffect(()=>{
    if(!readonly&&a.mode==='practice'&&!a.part&&displayPart!==a.player!.part){
      media.current?.pause();void sendRef.current('seek',{part:displayPart,position:undefined}).catch(()=>{});
    }
  },[displayPart,a.mode,readonly]);
  useEffect(()=>{if(readonly){media.current?.pause();if(media.current)media.current.playbackRate=reviewPlayer.current.rate;autoPlay.current=false;}},[readonly]);
  const finishPart=async()=>{
    if(transition.current||readonly||!strict||current.current.player!.phase!=='audio')return;
    transition.current=true;media.current?.pause();
    try{await flush();const response=await send('next',{position:end});autoPlay.current=response.player!.phase==='audio';if(autoPlay.current)onPlayingPart(response.player!.part);}catch{}finally{transition.current=false;}
  };
  const loaded=()=>{
    clearBuffering();
    const m=media.current;if(!m)return;m.volume=volume;m.preservesPitch=true;
    if(readonly){reviewPlayer.current={...reviewPlayer.current,position:start,loopA:null,loopB:null};setReviewSettings({...reviewPlayer.current});}
    let target=readonly?start:current.current.player!.position;
    if(!readonly&&!restored.current){
      restored.current=true;try{const d=JSON.parse(localStorage.getItem(draftKey)||'null');if(d&&d.part===activePart)target=Math.min(end,Math.max(start,strict?Math.min(target+3,d.position):d.position));}catch{}
    }
    m.currentTime=Math.max(start,Math.min(end,target));m.playbackRate=readonly?reviewPlayer.current.rate:current.current.player!.rate;
    setPosition(m.currentTime);
    if(autoPlay.current){autoPlay.current=false;void m.play().catch(()=>{pauseLocally();void sendRef.current('interrupt').catch(()=>{});});}
  };
  const play=async()=>{
    const m=media.current;if(!m)return;setBusy(true);
    try{
      await flush();
      if(readonly){if(m.currentTime>=end-.1)m.currentTime=start;await m.play();setLocalPaused(false);return;}
      if(current.current.mode==='practice'&&m.currentTime>=end-.1)m.currentTime=start;
      if(current.current.player!.phase!=='check')await m.play();
      await send('play');setLocalPaused(false);
    }catch(e){pauseLocally();error((e as Error).message);}finally{setBusy(false);}
  };
  const pause=async()=>{
    setBusy(true);media.current?.pause();
    try{if(!readonly){await flush();await send('pause');}setLocalPaused(true);}catch{}finally{setBusy(false);}
  };
  const seek=async(pos:number)=>{const m=media.current;if(!m)return;m.currentTime=Math.max(start,Math.min(end,pos));setPosition(m.currentTime);if(!readonly)await send('checkpoint');};
  const settings=readonly?reviewSettings:a.player!;
  const update=async(values:Partial<PlayerState>&{clearLoop?:boolean})=>{
    if(values.rate&&media.current)media.current.playbackRate=values.rate;
    if(readonly){reviewPlayer.current={...reviewPlayer.current,...(values.clearLoop?{loopA:null,loopB:null}:{}),...values};setReviewSettings({...reviewPlayer.current});}
    else await send('checkpoint',values);
  };
  const audioError=()=>{if(!readonly&&current.current.player!.running){pauseLocally();void send('interrupt').catch(()=>{});error('Audio interrupted. Check the local service, then resume from the saved position.');}};
  const waiting=()=>{
    if(readonly||transition.current||autoPlay.current||buffering.current||!current.current.player!.running)return;
    buffering.current=setTimeout(()=>{buffering.current=null;if(media.current&&media.current.readyState<3)audioError();},3000);
  };
  const state=a.player!,running=state.running&&!localPaused;
  const playing=readonly?!!media.current&&!media.current.paused:running;
  return <div className="listening-player">
    <audio ref={media} src={asset.url} preload="auto" onLoadedMetadata={loaded} onError={audioError} onStalled={waiting} onWaiting={waiting} onPlaying={clearBuffering} onEnded={()=>{if(strict)void finishPart();else{setLocalPaused(true);if(!readonly)void send('pause',{position:end}).catch(()=>{});}}} onTimeUpdate={()=>{
      const m=media.current;if(!m)return;setPosition(m.currentTime);
      const s=readonly?reviewPlayer.current:current.current.player!;
      if(!strict&&s.loopA!=null&&s.loopB!=null&&m.currentTime>=s.loopB)m.currentTime=s.loopA;
      else if(strict&&m.currentTime>=end-.05)void finishPart();
      else if(!strict&&m.currentTime>=end){m.pause();setLocalPaused(true);if(!readonly)void send('pause',{position:end}).catch(()=>{});}
    }}/>
    <span className="audio-part"><Headphones size={18}/>Part {activePart}</span>
    {state.phase!=='ready'&&(!strict||!running)&&<button data-audio-resume className="button small" aria-label={playing&&!strict?'Pause audio':'Play audio'} disabled={busy||(!owned&&!readonly)} onClick={()=>void (playing&&!strict?pause():play())}>{playing&&!strict?<Pause size={15}/>:<Play size={15}/>} {playing&&!strict?'Pause':state.phase==='check'&&!readonly?'Resume checking':'Play / Resume'}</button>}
    <span className="audio-position">{state.phase==='check'&&!readonly?'Check your answers':`${clockText(position-start)} / ${clockText(end-start)}`}</span>
    {!strict&&<><button className="audio-skip" aria-label="Back 5 seconds" onClick={()=>void seek(position-5).catch(()=>{})}>−5s</button><input type="range" aria-label="Audio position" min={start} max={end} step="0.1" value={position} onChange={e=>void seek(+e.target.value).catch(()=>{})}/><button className="audio-skip" aria-label="Forward 5 seconds" onClick={()=>void seek(position+5).catch(()=>{})}>+5s</button><select aria-label="Playback speed" value={settings.rate} onChange={e=>void update({rate:+e.target.value}).catch(()=>{})}>{[.5,.75,1,1.25,1.5,1.75,2].map(r=><option key={r} value={r}>{r}×</option>)}</select></>}
    <label className="audio-volume"><Volume2 size={16}/><input type="range" aria-label="Volume" min="0" max="1" step="0.05" value={volume} onChange={e=>{setVolume(+e.target.value);if(media.current)media.current.volume=+e.target.value;}}/></label>
    {!strict&&<div className="audio-loop"><button className={settings.loopA!=null?'set':''} title="Set loop start" onClick={()=>void update({loopA:position,clearLoop:settings.loopB!=null&&position>=settings.loopB}).catch(()=>{})}>A</button><button className={settings.loopB!=null?'set':''} title="Set loop end" disabled={settings.loopA==null||position<=settings.loopA+.25} onClick={()=>void update({loopB:position}).catch(()=>{})}>B</button><button aria-label="Clear A–B loop" onClick={()=>void update({clearLoop:true}).catch(()=>{})}><RotateCcw size={13}/></button></div>}
    {strict&&<button className="text-button" disabled={busy} onClick={()=>setConfirmPractice(true)}>Switch to practice</button>}
    {confirmPractice&&<Modal title="Switch to practice?" onClose={()=>setConfirmPractice(false)}><p>Your answers and audio position will be kept. Practice allows pause, seeking and replay. This attempt will be recorded as practice.</p><div className="modal-actions"><button className="button secondary" onClick={()=>setConfirmPractice(false)}>Keep simulation</button><button className="button" onClick={()=>{setConfirmPractice(false);void send('practice').catch(()=>{});}}>Switch to practice</button></div></Modal>}
    {a.status==='graded'&&<button className="text-button" onClick={onTranscript}><FileText size={16}/>Transcript</button>}
    {state.interrupted&&<span className="interruption-label">Đã gián đoạn ({state.interruptions})</span>}
    {!owned&&!readonly&&<button className="text-button" onClick={()=>void send('claim',{position:undefined}).catch(()=>{})}>Retry audio connection</button>}
    {!readonly&&(state.phase==='ready'||(!running&&a.status!=='paused'))&&<div className="audio-ready"><Headphones size={24}/><strong>{state.phase==='ready'?'Check your headphones, then start.':'Your position is saved.'}</strong><span>{strict?'Listen once at normal speed. Four Parts, then two minutes to check your answers.':'You can pause, change speed and repeat audio while practising.'}</span>{state.phase==='ready'&&<button className="button secondary" onClick={()=>{const tone=new Audio('/audio-check.wav');tone.volume=volume;void tone.play().catch(e=>error(e.message));}}>Test sound</button>}<button data-audio-resume className="button" disabled={busy||!owned} onClick={()=>void play()}><Play size={16}/>{state.phase==='ready'?'Start listening':'Resume'}</button></div>}
  </div>;
}
