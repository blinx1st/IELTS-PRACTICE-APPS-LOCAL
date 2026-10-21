import test from 'node:test';
import assert from 'node:assert/strict';
import {highlightSelection,normalizeAnnotations,annotatedSegments} from '../../frontend/annotations.ts';

const text='abcdefghijklmnopqrst';
const range=(start,end,anchor='p1')=>({anchor,start,end,text:text.slice(start,end)});
const levels=items=>items.filter(a=>a.kind==='highlight').map(a=>[a.start,a.end,a.level]);

test('overlap increases only the intersection, saturating at red',()=>{
  let items=highlightSelection([], [range(0,8)]);
  items=highlightSelection(items,[range(4,12)]);
  assert.deepEqual(levels(items),[[0,4,1],[4,8,2],[8,12,1]]);
  items=highlightSelection(items,[range(6,10)]);
  assert.deepEqual(levels(items),[[0,4,1],[4,6,2],[6,8,3],[8,10,2],[10,12,1]]);
  items=highlightSelection(items,[range(6,8)]);
  assert.deepEqual(levels(items),[[0,4,1],[4,6,2],[6,8,3],[8,10,2],[10,12,1]]);
});

test('repeated full highlight merges to one range and never gains a note',()=>{
  let items=[];
  for(let i=0;i<30;i++)items=highlightSelection(items,[range(0,8)]);
  assert.deepEqual(levels(items),[[0,8,3]]);
  assert.equal(items.length,1);
  assert.equal(items[0].note,undefined);
});

test('clear splits only selected text and does not remove overlapping notes',()=>{
  const note={...range(3,10),id:'note1',kind:'note',note:'Remember this'};
  let items=highlightSelection([note],[range(0,12)]);
  items=highlightSelection(items,[range(5,9)],true);
  assert.deepEqual(levels(items),[[0,5,1],[9,12,1]]);
  assert.deepEqual(items.find(a=>a.kind==='note'),note);
  const parts=annotatedSegments('p1',text,items);
  assert.equal(parts.map(p=>p.text).join(''),text);
  assert.equal(parts.find(p=>p.start===5).level,0);
  assert.equal(parts.find(p=>p.start===5).note.note,'Remember this');
});

test('legacy highlights overlap correctly and legacy notes stay independent',()=>{
  const old=[{...range(0,8),id:'a',note:''},{...range(4,12),id:'b',note:''},{...range(6,10),id:'c',note:'Old note'}];
  const items=normalizeAnnotations(old);
  assert.deepEqual(levels(items),[[0,4,1],[4,8,2],[8,12,1]]);
  assert.equal(items.at(-1).kind,'note');
  assert.deepEqual(normalizeAnnotations(items),items);
  assert.deepEqual(normalizeAnnotations(JSON.parse(JSON.stringify(items))),items);
});

test('multi-paragraph selection and clearing do not mix anchors',()=>{
  let items=highlightSelection([],[range(0,5,'p1'),range(0,5,'p2')]);
  items=highlightSelection(items,[range(0,5,'p1')]);
  assert.deepEqual(items.map(a=>[a.anchor,a.level]),[['p1',2],['p2',1]]);
  items=highlightSelection(items,[range(1,4,'p1')],true);
  assert.deepEqual(items.filter(a=>a.anchor==='p2').map(a=>a.level),[1]);
});

test('invalid and out-of-text annotations cannot corrupt rendered text',()=>{
  const items=normalizeAnnotations([{...range(0,3),start:-1,id:'bad'},{...range(0,3),end:0,id:'empty'},{...range(0,3),id:'valid',note:''}]);
  assert.deepEqual(levels(items),[[0,3,1]]);
  assert.equal(annotatedSegments('p1','ab',items).map(p=>p.text).join(''),'ab');
});
