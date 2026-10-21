import {test,before,after} from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {filterQuestions,adjacentQuestion} from '../../frontend/navigation.ts';

let server,nav,support,demo;
before(async()=>{
  server=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom',optimizeDeps:{noDiscovery:true,include:[],entries:[]}});
  nav=await server.ssrLoadModule('/ExamNavigation.tsx');support=await server.ssrLoadModule('/ExamSupport.tsx');demo=await server.ssrLoadModule('/Familiarisation.tsx');
});
after(async()=>{await server?.close();});
const noop=()=>{},render=(c,p)=>renderToStaticMarkup(createElement(c,p));

test('review and unanswered navigation preserve original numbering, blanks and both answered and unanswered flags',()=>{
  const numbers=[11,12,13,14],answers={11:' A ',12:'   ',14:'word'},flags=[11,13,40];
  assert.deepEqual(filterQuestions(numbers,answers,flags,'unanswered'),[12,13]);
  assert.deepEqual(filterQuestions(numbers,answers,flags,'review'),[11,13]);
  assert.deepEqual(filterQuestions(numbers,answers,flags,'all'),numbers);
  assert.equal(adjacentQuestion([12,13],11,1),12);
  assert.equal(adjacentQuestion([12,13],14,-1),13);
  assert.equal(adjacentQuestion([12,13],13,1),undefined);
  assert.equal(adjacentQuestion([],11,-1),undefined);
});

test('40-question footer exposes current question, progress, part boundaries and flags without grading colours',()=>{
  const units=[1,2,3,4].map(number=>({number,groups:[{questions:Array.from({length:10},(_,i)=>({number:(number-1)*10+i+1}))}]}));
  const html=render(nav.ExamNavigation,{units,answers:{1:'answer'},flags:[1,12],current:12,activePart:2,onJump:noop,onPart:noop});
  assert.equal((html.match(/aria-label="Question \d+,/g)||[]).length,40);
  assert.match(html,/aria-current="step"[^>]*aria-label="Question 12, unanswered, marked for review"/);
  assert.match(html,/Go to Part 4/);assert.match(html,/Filter questions/);
  assert.equal(html.includes('nav-number correct'),false);
});

test('display preferences recover invalid saved values and constrain font size and page colours',()=>{
  assert.deepEqual(support.normalizePreferences(null),{fontSize:17,contrast:'white'});
  assert.deepEqual(support.normalizePreferences({fontSize:50,contrast:'black'}),{fontSize:24,contrast:'white'});
  assert.deepEqual(support.normalizePreferences({fontSize:14.7,contrast:'soft'}),{fontSize:15,contrast:'soft'});
  assert.equal(support.normalizePreferences({fontSize:NaN}).fontSize,17);
});

test('familiarisation renders the same answer table and navigation with untimed, score-free instructions',()=>{
  const html=render(demo.Familiarisation,{onBack:noop});
  assert.match(html,/NO SCORE/);assert.match(html,/Untimed/);
  assert.match(html,/Answer 1/);assert.match(html,/Answer 2/);
  assert.match(html,/Filter questions/);assert.match(html,/For review/);
  assert.match(html,/Part 2/);assert.equal(html.includes('60:00'),false);
});
