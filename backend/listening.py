"""Offline listening sessions. Player checkpoints never increment answer revisions."""
import math
import time
from fastapi import HTTPException

RATES = (.5, .75, 1, 1.25, 1.5, 1.75, 2)
LEASE_SECONDS = 8


def units(test):
    return test.get('parts', test.get('passages', []))


def initial_player(test, part=None):
    first = next(p for p in units(test) if part is None or p['number'] == part)
    return dict(part=first['number'], position=first['audio'].get('start', 0), rate=1,
                phase='ready', running=False, reviewRemaining=120, elapsed=0,
                interrupted=False, interruptions=0, sequence=0, leaseOwner=None,
                leaseUntil=0, lastCheckpointAt=None, loopA=None, loopB=None)


def interrupt(a):
    p = a['player']
    if p['running']:
        p.update(running=False, interrupted=True, interruptions=p.get('interruptions', 0) + 1)
    p.update(leaseOwner=None, leaseUntil=0)


def stale(a, now=None):
    p = a.get('player')
    if (p and p['running'] and a['status'] in ('active', 'paused')
            and (now or time.time()) > p.get('leaseUntil', 0)):
        interrupt(a)
        return True
    return False


def duration(test):
    return sum(p['audio'].get('end', p['audio']['duration']) - p['audio'].get('start', 0) for p in units(test)) + 120


def control(a, body, now=None):
    now = now or time.time()
    if a.get('skill', 'reading') != 'listening':
        raise HTTPException(409, 'This is not a Listening session.')
    if a['status'] not in ('active', 'paused'):
        raise HTTPException(409, 'This attempt has been submitted. Use the review player.')
    p = a['player']
    stale(a, now)
    if p.get('leaseOwner') not in (None, body.clientId) and p.get('leaseUntil', 0) > now:
        raise HTTPException(409, 'Audio is controlled in another tab. Close that tab and retry in 8 seconds.')
    p.update(leaseOwner=body.clientId, leaseUntil=now + LEASE_SECONDS)
    action = body.action
    strict = a['mode'] == 'exam'
    selected = [u for u in units(a['testSnapshot']) if a.get('part') is None or u['number'] == a['part']]
    unit = next(u for u in selected if u['number'] == p['part'])
    audio = unit['audio']; lo = audio.get('start', 0); hi = audio.get('end', audio['duration'])
    previous_running = p['running']
    delta = max(0, min(8, now - (p.get('lastCheckpointAt') or now)))
    if previous_running and action != 'claim':
        p['elapsed'] += delta
    if action == 'claim' and previous_running:
        interrupt(a)
        p.update(leaseOwner=body.clientId, leaseUntil=now + LEASE_SECONDS)
        previous_running = False
    if action == 'practice':
        a.update(mode='practice', convertedFromExam=True, part=None, examTiming='untimed')
        strict = False
        if p['phase'] == 'check': p.update(phase='audio', running=False)
    if body.position is not None:
        pos = body.position
        if not math.isfinite(pos) or not lo - .1 <= pos <= hi + .5:
            raise HTTPException(422, 'Audio position is outside this Part.')
        if strict and action not in ('claim', 'interrupt', 'release'):
            if pos < p['position'] - .15 or pos > p['position'] + delta + 3:
                raise HTTPException(422, 'Seeking is disabled during the simulation.')
        if action not in ('claim',):
            p['position'] = max(lo, min(hi, pos))
    if body.rate is not None:
        if body.rate not in RATES or (strict and body.rate != 1):
            raise HTTPException(422, 'Playback speed is not allowed in this mode.')
        p['rate'] = body.rate
    if not strict:
        for key in ('loopA', 'loopB'):
            value = getattr(body, key)
            if value is not None and (not math.isfinite(value) or not lo <= value <= hi):
                raise HTTPException(422, 'Loop points must be inside this Part.')
        if body.clearLoop:
            p.update(loopA=None, loopB=None)
        if body.loopA is not None: p['loopA'] = body.loopA
        if body.loopB is not None: p['loopB'] = body.loopB
        if p.get('loopA') is not None and p.get('loopB') is not None and p['loopB'] <= p['loopA'] + .25:
            raise HTTPException(422, 'Point B must be after point A.')
    if action == 'play':
        p.update(running=True, phase='audio' if p['phase'] == 'ready' else p['phase'])
        a['status'] = 'active'
    elif action == 'pause':
        if strict: raise HTTPException(409, 'Pause is disabled in the simulation.')
        p['running'] = False; a['status'] = 'paused'
    elif action in ('interrupt', 'release'):
        interrupt(a)
    elif action == 'seek':
        if strict: raise HTTPException(409, 'Seeking is disabled in the simulation.')
        if body.part is not None and body.part != p['part']:
            unit = next((u for u in selected if u['number'] == body.part), None)
            if unit is None: raise HTTPException(422, 'Invalid Part.')
            p.update(part=body.part, position=unit['audio'].get('start', 0), loopA=None, loopB=None)
        p.update(running=False, phase='audio')
    elif action == 'next':
        if p['phase'] != 'audio': raise HTTPException(409, 'The audio phase has already ended.')
        if p['position'] < hi - .8:
            raise HTTPException(409, 'This Part has not ended yet.')
        index = selected.index(unit)
        if strict and index + 1 < len(selected):
            nxt = selected[index + 1]
            p.update(part=nxt['number'], position=nxt['audio'].get('start', 0), phase='audio', running=True)
        elif strict:
            p.update(phase='check', running=True, reviewRemaining=120)
        else:
            p['running'] = False
    if p['phase'] == 'check' and previous_running and action != 'next':
        p['reviewRemaining'] = max(0, p['reviewRemaining'] - delta)
        if p['reviewRemaining'] == 0:
            p.update(phase='finished', running=False)
            a.update(status='submitted', submittedAt=now, autoSubmitted=True, revision=a['revision'] + 1)
    p.update(lastCheckpointAt=now, sequence=p.get('sequence', 0) + 1)
    return a
