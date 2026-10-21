"""Preparation-only local ASR evidence for audio boundaries; never called by the app."""
from pathlib import Path
import json,sys,re
ROOT=Path(__file__).resolve().parents[1];LIB=ROOT/'library';PREP=LIB/'preparation/listening'

def main():
    from faster_whisper import WhisperModel
    import av,numpy as np
    def decode_audio(path,sampling_rate=16000):
        converter=av.AudioResampler(format='s16',layout='mono',rate=sampling_rate);chunks=[]
        with av.open(path) as source:
            for frame in source.decode(audio=0):
                for out in converter.resample(frame):chunks.append(out.to_ndarray().flatten())
            for out in converter.resample(None):chunks.append(out.to_ndarray().flatten())
        return np.concatenate(chunks).astype(np.float32)/32768
    model=WhisperModel('tiny.en',device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True,download_root=str(PREP/'models'))
    for path in sorted((LIB/'listening/tests').glob('*.json')):
        t=json.loads(path.read_text(encoding='utf8'))
        for part in t['parts']:
            n=part['number'];out=PREP/f'cam{t["book"]}'/f'timeline-t{t["test"]}-p{n}.json'
            if t['book']<17 and n!=4:continue
            if out.exists():continue
            a=part['audio'];samples=decode_audio(str(LIB/'audio'/Path(a['url']).name),sampling_rate=16000)
            duration=len(samples)/16000
            ranges=[(0,min(120,duration))] if n==1 else []
            effective_end=part['audio'].get('end',duration) if t['book']<17 else duration
            ranges.append((max(0,effective_end-120),effective_end))
            if (t['book'],t['test'],n)==(19,1,1):ranges.append((115,175))
            records=[]
            for start,end in ranges:
                segments,_=model.transcribe(samples[int(start*16000):int(end*16000)],language='en',beam_size=3,condition_on_previous_text=False,word_timestamps=True)
                records.extend({'start':s.start+start,'end':s.end+start,'text':s.text,'words':[{'word':w.word,'start':w.start+start,'end':w.end+start} for w in s.words or []]} for s in segments)
            out.write_text(json.dumps({'audioSha256':a['sha256'],'duration':duration,'model':'faster-whisper tiny.en int8','segments':records},ensure_ascii=False,indent=2),encoding='utf8')
            print(t['book'],t['test'],n,'complete',flush=True)

if __name__=='__main__':main()
