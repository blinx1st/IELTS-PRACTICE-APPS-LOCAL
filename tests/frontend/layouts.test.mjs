import {test,before,after} from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import {createServer} from 'vite';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';

let server,ui,Annotated,groups=[];
before(async()=>{
  server=await createServer({server:{middlewareMode:true,hmr:false},appType:'custom',optimizeDeps:{noDiscovery:true,include:[],entries:[]}});
  ui=await server.ssrLoadModule('/QuestionLayouts.tsx');
  ({Annotated}=await server.ssrLoadModule('/Annotated.tsx'));
  for(const file of await readdir('library/tests')){
    const t=JSON.parse(await readFile('library/tests/'+file,'utf8'));
    groups.push(...t.passages.flatMap(p=>p.groups).filter(g=>g.layout));
  }
});
after(async()=>{await server?.close();});
const noop=()=>{};
const props=group=>({group,attempt:{answers:{},answerParts:{},annotations:[],flags:[]},editable:true,results:{},onAnswer:noop,onAnswerPart:noop,onFlag:noop,onFocus:noop,onAnnotation:noop});
const render=(component,p)=>renderToStaticMarkup(createElement(component,p));

test('all six verified tables render 36 in-cell inputs covering exactly 35 questions',()=>{
  const tables=groups.filter(g=>g.layout.kind==='table');
  assert.equal(tables.length,6);
  let total=0,questions=0;
  for(const group of tables){
    const html=render(ui.InteractiveTable,props(group));
    const labels=[...html.matchAll(/<input[^>]+aria-label="Answer (\d+)(?:, part (\d+))?"/g)];
    assert.deepEqual([...new Set(labels.map(m=>+m[1]))].sort((a,b)=>a-b),group.questions.map(q=>q.number));
    assert.equal(/<img/.test(html),false);
    assert.ok(html.includes('<table'));
    assert.ok(/rowspan="5"/i.test(html)||group.id!=='cam13-t3-p1-g1');
    total+=labels.length;questions+=group.questions.length;
  }
  assert.equal(total,36);assert.equal(questions,35);
});

test('two-part table answer preserves an empty first field, and displays old combined answers',()=>{
  const group=groups.find(g=>g.id==='cam15-t4-p1-g2');
  const p=props(group);p.attempt.answers[7]='bark';p.attempt.answerParts[7]=['','bark'];
  let html=render(ui.InteractiveTable,p);
  assert.match(html,/id="answer-7-part-0"[^>]*value=""/);
  assert.match(html,/id="answer-7-part-1"[^>]*value="bark"/);
  assert.deepEqual(ui.answerPartsFor({answers:{7:'leaves bark'},answerParts:{}},7,2),['leaves','bark']);
  p.editable=false;html=render(ui.InteractiveTable,p);
  assert.equal((html.match(/<input[^>]*disabled=""/g)||[]).length,4);
});

test('all 34 matrices expose the complete correct choices, with no result before grading',()=>{
  const matrices=groups.filter(g=>g.layout.kind==='matrix');
  assert.equal(matrices.length,34);
  assert.equal(matrices.filter(g=>g.layout.matchingKind==='headings').length,5);
  for(const group of matrices){
    const p=props(group),n=group.questions[0].number;p.attempt.answers[n]=group.options[0].value;
    const html=render(ui.MatchingMatrix,p);
    assert.equal((html.match(/type="radio"/g)||[]).length,group.questions.length*group.options.length,group.id);
    assert.equal((html.match(/checked=""/g)||[]).length,1);
    assert.equal(html.includes('correct-option'),false);
    assert.equal(html.includes('incorrect-option'),false);
    assert.equal(html.includes('Clear answer '+n),true);
    if(group.layout.matchingKind==='headings')for(const option of group.options)assert.ok(html.includes(option.label.replaceAll('&','&amp;')));
  }
});

test('graded matrix shows correct column and incorrect selection, with all controls locked',()=>{
  const group=groups.find(g=>g.layout.kind==='matrix'),p=props(group),n=group.questions[0].number;
  p.attempt.answers[n]=group.options[0].value;p.editable=false;
  p.results[n]={number:n,status:'incorrect',accepted:[group.options[1].value]};
  const html=render(ui.MatchingMatrix,p);
  assert.match(html,/class="correct-option"/);assert.match(html,/class="incorrect-option"/);
  assert.equal((html.match(/<input[^>]*disabled=""/g)||[]).length,group.questions.length*group.options.length);
  assert.equal(html.includes('Clear answer'),false);
});

test('highlight and note use independent markup over the same text',()=>{
  const html=render(Annotated,{id:'p1',text:'example',annotations:[{id:'h',kind:'highlight',level:2,anchor:'p1',start:0,end:7,text:'example'},{id:'n',kind:'note',note:'note',anchor:'p1',start:0,end:7,text:'example'}],onEdit:noop});
  assert.match(html,/highlight-level-2/);assert.match(html,/note-anchor/);
  assert.equal((html.match(/example/g)||[]).length,1);
});
