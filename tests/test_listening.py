import copy
import hashlib
import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient
import backend.app as server
from backend.scoring import band_for, grade


@pytest.fixture
def listening(tmp_path, monkeypatch):
    lib=tmp_path/'library'
    for folder in ['listening/tests','listening/keys','listening/transcripts','audio','assets']:
        (lib/folder).mkdir(parents=True,exist_ok=True)
    audio=b'ID3'+bytes(range(128))*10
    sha=hashlib.sha256(audio).hexdigest();name=sha+'.mp3'
    (lib/'audio'/name).write_bytes(audio)
    test={'id':'cam20-listening-test1','skill':'listening','book':20,'test':1,'title':'Listening fixture','version':'1','verification':{'status':'verified'},'parts':[]}
    for i in range(1,5):
        test['parts'].append({'id':f'p{i}','number':i,'title':f'Part {i}','paragraphs':[],
            'groups':[{'id':f'g{i}','type':'completion','instructions':'ONE WORD ONLY','body':'','wordLimit':1,
                       'questions':[{'number':n,'text':'Fill'} for n in range(i*10-9,i*10+1)]}],
            'audio':{'url':'/library-audio/'+name,'sha256':sha,'duration':5,'start':0,'end':5,'verification':{'status':'verified'}}})
    key={'answers':{str(n):['answer'] for n in range(1,41)},'multi':[]}
    for path,value in [('tests',test),('keys',key),('transcripts',{'parts':{'1':'Private transcript','2':'Two','3':'Three','4':'Four'}})]:
        (lib/'listening'/path/(test['id']+'.json')).write_text(json.dumps(value),encoding='utf-8')
    monkeypatch.setattr(server,'DB',tmp_path/'history.sqlite3');monkeypatch.setattr(server,'LIBRARY',lib)
    moment=[1_790_000_000.0];monkeypatch.setattr(server.time,'time',lambda:moment[0])
    return TestClient(server.app),test,key,lib,moment


def begin(c,**extra):
    r=c.post('/api/attempts',json={'testId':'cam20-listening-test1','skill':'listening',**extra})
    assert r.status_code==200,r.text
    return r.json()


def player(c,a,action,**extra):
    return c.post('/api/attempts/'+a['id']+'/player',json={'action':action,'clientId':'tab-one-123',**extra})


def test_skill_library_and_private_transcript(listening):
    c,t,k,lib,clock=listening
    assert c.get('/api/library').json()['readyCount']==0
    assert c.get('/api/library?skill=listening').json()['readyCount']==1
    a=begin(c)
    assert len(a['numbers'])==40 and a['deadline'] is None and a['duration']==140
    assert 'keySnapshot' not in a and 'transcriptSnapshot' not in a
    assert 'Private transcript' not in json.dumps(a)
    assert c.get('/api/attempts/'+a['id']+'/transcript').status_code==409
    c.post('/api/attempts/'+a['id']+'/submit')
    assert c.get('/api/attempts/'+a['id']+'/transcript').status_code==409
    c.post('/api/attempts/'+a['id']+'/grade')
    assert c.get('/api/attempts/'+a['id']+'/transcript').json()['parts']['1']=='Private transcript'


def test_practice_all_or_part_and_no_reading_pause_route(listening):
    c,*_=listening
    assert len(begin(c,mode='practice')['numbers'])==40
    a=begin(c,mode='practice',part=3)
    assert a['numbers']==list(range(21,31)) and a['player']['part']==3
    assert c.post('/api/attempts/'+a['id']+'/pause').status_code==409
    assert c.post('/api/attempts',json={'testId':a['testId'],'skill':'listening','part':5}).status_code==422
    assert c.post('/api/attempts',json={'testId':a['testId']}).status_code==422


def test_independent_checkpoint_revision_and_lease(listening):
    c,t,k,lib,clock=listening
    a=begin(c)
    a=player(c,a,'play',position=0).json();clock[0]+=2
    a=player(c,a,'checkpoint',position=2).json()
    assert a['revision']==0 and a['player']['elapsed']==2
    r=c.patch('/api/attempts/'+a['id'],json={'revision':0,'answers':{'1':'answer'},'currentPassage':2})
    assert r.status_code==200 and r.json()['revision']==1
    assert c.post('/api/attempts/'+a['id']+'/player',json={'clientId':'tab-two-123','action':'claim'}).status_code==409
    clock[0]+=9
    restored=c.get('/api/attempts/'+a['id']).json()
    assert not restored['player']['running'] and restored['player']['position']==2
    assert restored['player']['interrupted'] and restored['player']['interruptions']==1
    assert restored['answers']=={'1':'answer'}


def test_reload_claim_pauses_without_reset(listening):
    c,t,k,lib,clock=listening
    a=begin(c);player(c,a,'play');clock[0]+=2
    a=player(c,a,'checkpoint',position=2).json()
    a=player(c,a,'claim').json()
    assert a['player']['position']==2 and a['player']['interrupted'] and not a['player']['running']


def test_missing_audio_disables_test_and_loop_restart_preserves_new_a(listening):
    c,t,k,lib,clock=listening
    a=begin(c,mode='practice')
    player(c,a,'checkpoint',loopA=1,loopB=3)
    r=player(c,a,'checkpoint',clearLoop=True,loopA=4).json()
    assert r['player']['loopA']==4 and r['player']['loopB'] is None
    next((lib/'audio').iterdir()).unlink()
    assert c.get('/api/library?skill=listening').json()['readyCount']==0


def test_practice_conversion_during_final_check_exits_check_phase(listening):
    c,t,k,lib,clock=listening
    a=begin(c)
    for part in range(4):
        player(c,a,'play');clock[0]+=5
        a=player(c,a,'next',position=5).json()
    assert a['player']['phase']=='check'
    assert player(c,a,'next',position=5).status_code==409
    a=player(c,a,'practice').json()
    assert a['player']['phase']=='audio' and not a['player']['running']
    clock[0]+=121
    assert player(c,a,'checkpoint').json()['status']=='active'


def test_strict_controls_and_one_way_practice(listening):
    c,t,k,lib,clock=listening
    a=begin(c);player(c,a,'play')
    assert player(c,a,'pause').status_code==409
    assert player(c,a,'seek',position=4).status_code==422
    assert player(c,a,'checkpoint',rate=1.5).status_code==422
    a=player(c,a,'practice').json()
    assert a['mode']=='practice' and a['convertedFromExam']
    a=player(c,a,'checkpoint',rate=2,position=4,loopA=1,loopB=3).json()
    assert a['player']['rate']==2 and a['player']['loopA']==1
    a=player(c,a,'pause').json();assert a['status']=='paused'
    a=player(c,a,'play').json();assert a['status']=='active'
    a=player(c,a,'seek',part=2).json();assert a['player']['part']==2 and a['player']['position']==0


def test_four_parts_checking_and_autosubmit(listening):
    c,t,k,lib,clock=listening
    a=begin(c);player(c,a,'play')
    for i in range(1,5):
        clock[0]+=5;a=player(c,a,'next',position=5).json()
        if i<4: assert a['player']['part']==i+1 and a['player']['running']
    assert a['player']['phase']=='check' and a['player']['reviewRemaining']==120
    for _ in range(60):
        clock[0]+=2;a=player(c,a,'checkpoint',position=5).json()
    assert a['status']=='submitted' and a['autoSubmitted'] and a['player']['phase']=='finished'
    assert player(c,a,'play').status_code==409


def test_audio_range_and_streamed_archive(listening):
    c,t,k,lib,clock=listening
    url=t['parts'][0]['audio']['url']
    r=c.get(url,headers={'Range':'bytes=0-9'})
    assert r.status_code==206 and len(r.content)==10
    a=begin(c,mode='practice',part=1)
    player(c,a,'play');clock[0]+=2;player(c,a,'checkpoint',position=2)
    data=c.get('/api/backup');assert data.status_code==200
    with zipfile.ZipFile(io.BytesIO(data.content)) as z:
        manifest=json.loads(z.read('reading-room-backup.json'))
        assert manifest['version']==2 and any(n.startswith('audio/') for n in z.namelist())
    with server.connect() as db: db.execute('DELETE FROM attempts')
    r=c.post('/api/restore',files={'file':('backup.zip',data.content,'application/zip')})
    assert r.status_code==200 and r.json()['restored']==1
    restored=c.get('/api/attempts/'+a['id']).json()
    assert restored['player']['position']==2 and not restored['player']['running']
    assert restored['revision']==0


def test_listening_band_thresholds():
    for score,band in [(15,4.5),(16,5),(18,5.5),(23,6),(26,6.5),(30,7),(32,7.5),(35,8),(37,8.5),(39,9),(40,9)]:
        assert band_for(score,'listening')==band
    assert band_for(15)==5 and band_for(32)==7
