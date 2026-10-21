import {useState,type KeyboardEvent} from 'react';
import {ArrowRight,BookOpen,CheckCircle2,Clock3,Flag,Headphones,Highlighter,Keyboard,Settings2} from 'lucide-react';
import type {Skill} from './types';

export const PREFERENCES_KEY='reading-room:exam-preferences:v1';
export const FAMILIARISATION_KEY='reading-room:familiarisation:v1';
export type ExamPreferences={fontSize:number;contrast:'white'|'soft'|'high'};
export const defaultPreferences:ExamPreferences={fontSize:17,contrast:'white'};
export function onTabKeyDown(e:KeyboardEvent<HTMLElement>){
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
  const tabs=Array.from(e.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]'));
  const index=tabs.indexOf(document.activeElement as HTMLButtonElement);if(index<0)return;
  e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?tabs.length-1:(index+(e.key==='ArrowRight'?1:tabs.length-1))%tabs.length;
  tabs[next]?.focus();tabs[next]?.click();
}
export function normalizePreferences(value:unknown):ExamPreferences{
  const v=value&&typeof value==='object'?value as Partial<ExamPreferences>:{};
  return {fontSize:typeof v.fontSize==='number'&&Number.isFinite(v.fontSize)?Math.min(24,Math.max(14,Math.round(v.fontSize))):17,contrast:['white','soft','high'].includes(v.contrast||'')?v.contrast!: 'white'};
}
export function useExamPreferences(){
  const [preferences,set]=useState<ExamPreferences>(()=>{try{return normalizePreferences(JSON.parse(localStorage.getItem(PREFERENCES_KEY)||'null'));}catch{return defaultPreferences;}});
  const update=(patch:Partial<ExamPreferences>)=>set(current=>{const next=normalizePreferences({...current,...patch});try{localStorage.setItem(PREFERENCES_KEY,JSON.stringify(next));}catch{/* Preferences remain usable when browser storage is unavailable. */}return next;});
  return {preferences,update};
}
export function DisplaySettings({value,onChange}:{value:ExamPreferences;onChange:(v:Partial<ExamPreferences>)=>void}){
  return <div className="display-settings"><p>Adjust your reading comfort. Your choices also apply to the next test.</p><fieldset><legend>Text size</legend><div className="text-size-picker"><button aria-label="Decrease text size" disabled={value.fontSize<=14} onClick={()=>onChange({fontSize:value.fontSize-1})}>A−</button><output aria-live="polite">{value.fontSize} px</output><button aria-label="Increase text size" disabled={value.fontSize>=24} onClick={()=>onChange({fontSize:value.fontSize+1})}>A+</button></div></fieldset><fieldset><legend>Page appearance</legend><div className="contrast-options">{([{id:'white',label:'White'},{id:'soft',label:'Soft background'},{id:'high',label:'High contrast'}] as const).map(o=><button key={o.id} className={'contrast-sample '+o.id} aria-pressed={value.contrast===o.id} onClick={()=>onChange({contrast:o.id})}><span>Aa</span>{o.label}{value.contrast===o.id&&<CheckCircle2 size={16}/>}</button>)}</div></fieldset><div className={'display-preview theme-'+value.contrast} style={{fontSize:value.fontSize}}>Read at a comfortable size. The answer fields remain in the same place.</div></div>;
}
export function StartOrientation({onOpen}:{onOpen:()=>void}){
  return <button className="start-orientation" onClick={onOpen}><Keyboard size={20}/><span><strong>Chưa quen thao tác trên máy?</strong><small>Thử điền đáp án, cắm cờ và chuyển câu trước khi bắt đầu.</small></span><ArrowRight size={18}/></button>;
}
export function ExamHelp({skill='reading',practice=false}:{skill?:Skill;practice?:boolean}){
  const [tab,setTab]=useState('navigation');
  const sections=[{id:'navigation',label:'Navigation',icon:Keyboard},{id:'answers',label:'Answers',icon:CheckCircle2},{id:'tools',label:'Tools',icon:Highlighter},{id:'time',label:'Timing & audio',icon:Clock3}];
  return <div className="exam-help"><p className="help-timer-notice"><Clock3 size={16}/>Opening Help or Display settings does not pause your test.</p><div className="help-tabs" role="tablist" aria-label="Help topics" onKeyDown={onTabKeyDown}>{sections.map(s=><button role="tab" aria-selected={tab===s.id} key={s.id} onClick={()=>setTab(s.id)}><s.icon size={16}/>{s.label}</button>)}</div><section role="tabpanel" aria-label={sections.find(s=>s.id===tab)?.label}>
    {tab==='navigation'&&<><h3>Đi đến câu cần làm</h3><p>Bấm số ở thanh dưới để chuyển tới ô trả lời. Số nền xanh đã có đáp án; viền đậm là câu hiện tại. Cờ màu vàng là câu bạn muốn xem lại, không có nghĩa là trả lời sai.</p><p>Chọn <b>Unanswered</b> hoặc <b>For review</b> để tìm các câu cần kiểm tra. Chọn <b>All questions</b> để hiện lại toàn bộ.</p><div className="help-key-row"><kbd>Alt</kbd> + <kbd>← / →</kbd><span>Câu trước / sau</span></div><div className="help-key-row"><kbd>Tab</kbd><span>Đến ô hoặc nút tiếp theo</span></div><div className="help-key-row"><kbd>↑ / ↓</kbd><span>Chọn trong dropdown hoặc nhóm radio</span></div></>}
    {tab==='answers'&&<><h3>Trả lời ngay trong đề</h3><p>Gõ vào chỗ trống trong câu hoặc bảng. Đọc đúng giới hạn từ; không cần gõ lại số câu. Với hai ô thuộc một câu, điền riêng từng ô.</p><p>Bấm radio để chọn một đáp án, checkbox cho nhóm chọn nhiều. Dùng <b>Clear answer</b>, dấu × hoặc lựa chọn trống để xóa.</p><p><b>Finish test</b> mở bước kiểm tra trước khi nộp. Sau nộp, bài được khóa. Chỉ khi bấm <b>Chấm bài</b>, đáp án đúng và điểm mới xuất hiện.</p></>}
    {tab==='tools'&&<><h3>Đọc và ghi nhớ</h3><p>Bôi chọn chữ rồi chọn <b>Highlight</b>: vàng ở lần đầu, phần chồng nhau chuyển cam rồi đỏ. <b>Clear highlight</b> xóa màu trong vùng chọn.</p><p><b>Note</b> tạo ghi chú riêng. Bấm chữ gạch chân để mở lại; nút <b>Notes</b> liệt kê ghi chú. Xóa highlight không xóa note.</p><p><Settings2 size={16}/> <b>Display</b> đổi cỡ chữ và độ tương phản. Reading có thanh kéo giữa hai cột; cũng có thể focus thanh rồi dùng phím ←/→. <b>Source</b> là ảnh PDF để đối chiếu khi học.</p></>}
    {tab==='time'&&<><h3>{skill==='listening'?'Listening: audio và thời gian':'Reading: đồng hồ làm bài'}</h3>{skill==='listening'?<><p><Headphones size={16}/> Khi thi sát thật, audio 1× phát liên tiếp bốn Parts. Chuyển trang câu hỏi không đổi track đang phát. Không có tua hoặc Pause thủ công; cuối bài có 2 phút kiểm tra.</p><p>Luyện tập có Play/Pause, tốc độ, tua ±5 giây và lặp A–B. Đổi Part sẽ dừng track cũ. Khi gặp sự cố, app dừng ở checkpoint và chờ Resume.</p></>:<><p><BookOpen size={16}/> Thi 60 phút không Pause. Đóng tab hoặc dừng dịch vụ không đặt lại đồng hồ. Hết giờ tự nộp.</p><p>Luyện không hạn giờ đếm thời gian đã làm và có Pause. Khi Pause, nội dung được che. Bấm Resume để tiếp tục.</p></>}<p>Chế độ hiện tại: <b>{practice?'luyện tập':'thi thử'}</b>. <b>Saved on this device</b> xác nhận bài đã lưu trên máy; nếu thấy bản nháp trình duyệt, giữ tab và mở lại dịch vụ local.</p></>}
  </section></div>;
}
