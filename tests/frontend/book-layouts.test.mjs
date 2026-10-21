import {test,before,after} from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import {createServer} from 'vite';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
let server,table,flow,field,groups=[];
const noop=()=>{},render=(c,p)=>renderToStaticMarkup(createElement(c,p));
const props=group=>({group,attempt:{answers:{},answerParts:{},annotations:[],flags:[]},editable:true,results:{},onAnswer:noop,onAnswerPart:noop,onFlag:noop,onFocus:noop,onAnnotation:noop});
before(async()=>{
 server=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom',optimizeDeps:{noDiscovery:true,include:[],entries:[]}});
 ({InteractiveTable:table}=await server.ssrLoadModule('/QuestionLayouts.tsx'));
 ({ExtendedLayout:flow}=await server.ssrLoadModule('/ListeningLayouts.tsx'));
 field=await server.ssrLoadModule('/AnswerField.tsx');
 for(const directory of ['library/tests','library/listening/tests'])for(const file of await readdir(directory)){
  const t=JSON.parse(await readFile(directory+'/'+file,'utf8'));groups.push(...(t.parts||t.passages).flatMap(p=>p.groups));
 }
});
after(async()=>{await server?.close();});

test('18 tables use reviewed ratios and all 146 text groups retain inline answer order',()=>{
 let tables=0,flows=0;
 for(const g of groups){
  if(!['table','flow'].includes(g.layout?.kind))continue;
  const isTable=g.layout.kind==='table', html=render(isTable?table:flow,props(g));
  const numbers=[...html.matchAll(/<(?:input|select)[^>]+aria-label="Answer (\d+)/g)].map(m=>+m[1]);
  assert.deepEqual([...new Set(numbers)],g.questions.map(q=>q.number),g.id);
  assert.ok(!html.includes('<img'),g.id);
  if(isTable){tables++;for(const width of g.layout.columnWidths)assert.ok(html.includes(`width:${width}%`));}
  else flows++;
 }
 assert.equal(tables,18);assert.equal(flows,146);
});

test('word limits and per-blank overrides give stable sizes independent of typing',()=>{
 assert.deepEqual([1,2,3].map(field.answerWidth),[12,16,20]);
 const g=groups.find(g=>g.id==='cam15-t4-p1-g2'),p=props(g);
 let html=render(table,p);assert.match(html,/--answer-width:10ch/);
 p.attempt.answerParts[7]=['leaves','bark'];p.attempt.answers[7]='leaves bark';
 const filled=render(table,p);
 assert.equal((html.match(/--answer-width:10ch/g)||[]).length,2);
 assert.equal((filled.match(/--answer-width:10ch/g)||[]).length,2);
 assert.equal((filled.match(/Mark question 7 for review/g)||[]).length,1);
 assert.equal((filled.match(/class="answer-number">7/g)||[]).length,1);
});

test('Stonehenge preserves heading hierarchy and independent nested source markers',()=>{
 const g=groups.find(g=>g.id==='cam18-t2-p1-g1');const html=render(flow,props(g));
 assert.match(html,/<h3[^>]*title[^>]*>/);assert.match(html,/<h4[^>]*section[^>]*>/);
 assert.match(html,/--block-depth:1/);assert.match(html,/--block-depth:2/);
 assert.ok(html.indexOf('Answer 2')<html.indexOf('may have been arranged'));
 assert.equal((html.match(/class="book-marker"/g)||[]).length,13);
});

test('historic highlight and note still attach after an original block is split',()=>{
 const g=groups.find(g=>g.id==='cam20-t2-p1-g1'),p=props(g);
 // This original layout used one body anchor for its initial text token.
 const block=g.layout.blocks.find(b=>b.content.some(t=>typeof t==='string'&&t.includes('Appearance')));
 const i=block.content.findIndex(t=>typeof t==='string'&&t.includes('Appearance'));
 const start=block.offsets[i]+block.content[i].indexOf('Appearance');
 p.attempt.annotations=[{id:'h',kind:'highlight',color:'blue',anchor:block.anchors[i],start,end:start+10,text:'Appearance'},
 {id:'n',kind:'note',note:'Keep this note',anchor:block.anchors[i],start,end:start+10,text:'Appearance'}];
 const html=render(flow,p);
 assert.match(html,/highlight-color-blue/);assert.match(html,/title="Keep this note"/);
 assert.equal((html.match(/Appearance/g)||[]).length,1);
});

test('word-bank letters stay inline, banks follow the summary and grading stays hidden until supplied',()=>{
 const g=groups.find(g=>g.id==='cam18-t2-p2-g3'),p=props(g);p.attempt.answers[24]='C';
 let html=render(flow,p);
 assert.match(html,/<option value="C" selected="">C\. /);
 assert.ok(html.lastIndexOf('Answer 26')<html.indexOf('List of options'));
 assert.equal(html.includes('answer-feedback correct'),false);
 p.editable=false;p.results[24]={status:'correct',accepted:['C']};html=render(flow,p);
 assert.match(html,/answer-feedback correct/);assert.equal((html.match(/<select[^>]*disabled/g)||[]).length,3);
});
