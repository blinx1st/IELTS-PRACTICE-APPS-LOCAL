import test from 'node:test';
import assert from 'node:assert/strict';
import {highlightSelection,normalizeAnnotations,annotatedSegments} from '../../frontend/annotations.ts';

const text='abcdefghijklmnopqrst';
const range=(start,end,anchor='p1')=>({anchor,start,end,text:text.slice(start,end)});
const levels=items=>items.filter(a=>a.kind==='highlight').map(a=>[a.start,a.end,a.color]);

test('chosen colour replaces only the intersection, without escalation',()=>{
 let items=highlightSelection([], [range(0,8)],'green');
 items=highlightSelection(items,[range(4,12)],'blue');
 assert.deepEqual(levels(items),[[0,4,'green'],[4,12,'blue']]);
 items=highlightSelection(items,[range(6,10)],'red');
 assert.deepEqual(levels(items),[[0,4,'green'],[4,6,'blue'],[6,10,'red'],[10,12,'blue']]);
 assert.deepEqual(normalizeAnnotations(JSON.parse(JSON.stringify(items))),items);
});

test('repeated full highlight merges to one range and never gains a note',()=>{
  let items=[];
  for(let i=0;i<30;i++)items=highlightSelection(items,[range(0,8)]);
  assert.deepEqual(levels(items),[[0,8,'yellow']]);
  assert.equal(items.length,1);
  assert.equal(items[0].note,undefined);
});

test('clear splits only selected text and does not remove overlapping notes',()=>{
  const note={...range(3,10),id:'note1',kind:'note',note:'Remember this'};
  let items=highlightSelection([note],[range(0,12)]);
  items=highlightSelection(items,[range(5,9)],'clear');
  assert.deepEqual(levels(items),[[0,5,'yellow'],[9,12,'yellow']]);
  assert.deepEqual(items.find(a=>a.kind==='note'),note);
  const parts=annotatedSegments('p1',text,items);
  assert.equal(parts.map(p=>p.text).join(''),text);
  assert.equal(parts.find(p=>p.start===5).color,undefined);
  assert.equal(parts.find(p=>p.start===5).note.note,'Remember this');
});

test('legacy highlights overlap correctly and legacy notes stay independent',()=>{
  const old=[{...range(0,8),id:'a',note:''},{...range(4,12),id:'b',note:''},{...range(6,10),id:'c',note:'Old note'}];
  const items=normalizeAnnotations(old);
  assert.deepEqual(levels(items),[[0,4,'yellow'],[4,8,'orange'],[8,12,'yellow']]);
  assert.equal(items.at(-1).kind,'note');
  assert.deepEqual(normalizeAnnotations(items),items);
  assert.deepEqual(normalizeAnnotations(JSON.parse(JSON.stringify(items))),items);
});

test('multi-paragraph selection and clearing do not mix anchors',()=>{
  let items=highlightSelection([],[range(0,5,'p1'),range(0,5,'p2')]);
  items=highlightSelection(items,[range(0,5,'p1')]);
  assert.deepEqual(items.map(a=>[a.anchor,a.color]),[['p1','yellow'],['p2','yellow']]);
  items=highlightSelection(items,[range(1,4,'p1')],'clear');
  assert.deepEqual(items.filter(a=>a.anchor==='p2').map(a=>a.color),['yellow']);
});

test('invalid and out-of-text annotations cannot corrupt rendered text',()=>{
  const items=normalizeAnnotations([{...range(0,3),start:-1,id:'bad'},{...range(0,3),end:0,id:'empty'},{...range(0,3),id:'valid',note:''}]);
  assert.deepEqual(levels(items),[[0,3,'yellow']]);
  assert.equal(annotatedSegments('p1','ab',items).map(p=>p.text).join(''),'ab');
});

test('all five colors survive serialization and legacy levels retain their original colors',()=>{
 for(const color of ['yellow','orange','red','green','blue']){
  const items=highlightSelection([],[range(0,5)],color);
  assert.equal(normalizeAnnotations(JSON.parse(JSON.stringify(items)))[0].color,color);
 }
 assert.deepEqual(normalizeAnnotations([1,2,3].map((level,i)=>({...range(i*3,i*3+3),id:String(i),kind:'highlight',level}))).map(a=>a.color),['yellow','orange','red']);
});
test('historic paragraph annotations cross inline blanks through stable source offsets',()=>{
 const note={...range(2,12),id:'n',kind:'note',note:'Keep'};
 const items=highlightSelection([note],[range(0,15)],'blue');
 const pieces=annotatedSegments('p1',text.slice(8,15),items,8);
 assert.equal(pieces.map(p=>p.text).join(''),text.slice(8,15));
 assert.equal(pieces[0].color,'blue');assert.equal(pieces[0].note.id,'n');
});
