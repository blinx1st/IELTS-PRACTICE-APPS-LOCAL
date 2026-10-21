import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError, post } from './api';
import type { Attempt } from './types';
import { normalizeAnnotations } from './annotations';

type Draft = Pick<Attempt,'answers'|'answerParts'|'flags'|'annotations'|'currentPassage'>;
const fields = (a:Attempt):Draft => ({answers:a.answers,answerParts:a.answerParts||{},flags:a.flags,annotations:normalizeAnnotations(a.annotations),currentPassage:a.currentPassage});
const normalizeAttempt=(a:Attempt):Attempt=>({...a,...fields(a),test:a.test?{...a.test,passages:a.test.parts||a.test.passages}:a.test});
export function useAttempt(id:string) {
  const [attempt,setAttempt] = useState<Attempt|null>(null);
  const [saveState,setSaveState] = useState('saved');
  const [error,setError] = useState('');
  const current = useRef<Attempt|null>(null);
  const generation = useRef(0), saved = useRef(0);
  const inflight = useRef<Promise<void>|null>(null);
  const blocked = useRef(false);
  const mounted = useRef(true);
  const draftKey = 'reading-room:draft:' + id;
  const apply = useCallback((a:Attempt) => {current.current=a;if(mounted.current)setAttempt(a);},[]);
  const persist = useCallback((a:Attempt) => {
    try {localStorage.setItem(draftKey,JSON.stringify({...fields(a),revision:a.revision}));}
    catch {setError('Bộ nhớ trình duyệt đã đầy. Hãy giữ app mở cho đến khi trạng thái Saved xuất hiện.');}
  },[draftKey]);
  useEffect(() => {
    mounted.current=true; blocked.current=false; generation.current=0;saved.current=0;setAttempt(null);setError('');
    api<Attempt>('/attempts/'+id).then(normalizeAttempt).then(a=>{
      if(!mounted.current)return;
      try {
        const raw = JSON.parse(localStorage.getItem(draftKey)||'null');
        const local = raw?{...fields(raw),revision:raw.revision}:null;
        if(local && ['active','paused'].includes(a.status)) {
          if(JSON.stringify(fields(a))===JSON.stringify(fields(local as Attempt))) localStorage.removeItem(draftKey);
          else if(local.revision===a.revision && a.status==='active') {
            a={...a,...fields(local as Attempt)};
            generation.current=1;setSaveState('pending');
          } else {blocked.current=true;setError('Có bản nháp khác với dữ liệu trên máy. Đã giữ bản nháp để tránh ghi đè; hãy xuất bản nháp trước khi mở lại.');setSaveState('conflict');}
        }
      } catch {setError('Không đọc được bản nháp trình duyệt; dữ liệu đã lưu trên máy vẫn được giữ nguyên.');}
      apply(a);
    }).catch(e=>setError(e.message));
    return()=>{mounted.current=false;};
  },[id,draftKey,apply]);

  const flush = useCallback(async ():Promise<void> => {
    if(blocked.current)throw new Error('Bài đang có xung đột dữ liệu. Hãy mở lại trước khi tiếp tục.');
    if(inflight.current)return inflight.current;
    const task = (async()=>{
      while(saved.current < generation.current) {
        const a=current.current;
        if(!a || !['active','paused'].includes(a.status))return;
        const g=generation.current;
        setSaveState('saving');
        try {
          const response = normalizeAttempt(await api<Attempt>('/attempts/'+id,{method:'PATCH',body:JSON.stringify({...fields(a),revision:a.revision})}));
          const latest=current.current!;
          const next = g===generation.current ? response : {...response,...fields(latest)};
          if((latest.player?.sequence||0)>(response.player?.sequence||0))next.player=latest.player;
          saved.current=g;apply(next);setError('');
          if(g===generation.current) {localStorage.removeItem(draftKey);setSaveState('saved');}
          else persist(next);
        } catch(e) {
          if(e instanceof ApiError && e.status===409){blocked.current=true;setSaveState('conflict');}
          else setSaveState('offline');
          setError((e as Error).message); throw e;
        }
      }
    })();
    inflight.current=task;
    try {await task;}finally{inflight.current=null;}
  },[id,draftKey,apply,persist]);

  const edit = useCallback((patch:Partial<Draft>|((current:Attempt)=>Partial<Draft>))=>{
    const a=current.current;
    if(!a || a.status!=='active' || blocked.current)return;
    const next={...a,...(typeof patch==='function'?patch(a):patch)}; generation.current++;apply(next);persist(next);setSaveState('pending');
  },[apply,persist]);
  useEffect(()=>{
    if(saveState!=='pending')return;
    const timeout=setTimeout(()=>{void flush().catch(()=>{});},400);
    return()=>clearTimeout(timeout);
  },[attempt,saveState,flush]);
  useEffect(()=>{
    const retry=setInterval(()=>{if(saved.current<generation.current&&!blocked.current)void flush().catch(()=>{});},5000);
    return()=>clearInterval(retry);
  },[flush]);
  const action = useCallback(async(name:string)=>{
    await flush();
    const a=normalizeAttempt(await post<Attempt>('/attempts/'+id+'/'+name));
    apply(a);setSaveState('saved');setError('');localStorage.removeItem(draftKey);
    return a;
  },[id,flush,apply,draftKey]);
  const checkExpiry = useCallback(async()=>{
    const a=normalizeAttempt(await api<Attempt>('/attempts/'+id));
    if(a.status==='submitted'||a.status==='graded'){
      saved.current=generation.current;blocked.current=false;apply(a);setSaveState('saved');
      setError('Time is up. Your last saved answers have been submitted.');
    }
  },[id,apply]);
  const receivePlayback=useCallback((remote:Attempt)=>{
    const c=current.current;if(!c)return;
    if(['submitted','graded'].includes(remote.status)){
      saved.current=generation.current;apply(normalizeAttempt(remote));
      localStorage.removeItem(draftKey);setSaveState('saved');
    }else apply({...c,player:remote.player,status:remote.status,mode:remote.mode,part:remote.part,convertedFromExam:remote.convertedFromExam,serverNow:remote.serverNow});
  },[apply,draftKey]);
  return {attempt,saveState,error,setError,edit,action,checkExpiry,flush,receivePlayback};
}
