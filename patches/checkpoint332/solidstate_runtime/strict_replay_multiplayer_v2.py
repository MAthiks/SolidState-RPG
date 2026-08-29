from copy import deepcopy
from .strict_replay_save_resume_v1 import StrictReplaySaveResumeContinuityV1
from .multiplayer_certification_v2 import MultiplayerRuntimeContractV2
from .strict_recovery_journal import StrictRecoveryJournal

class MultiplayerStrictReplayRecertificationV2:
    """Actor-bound Strict Replay for 1-4 player sessions.

    The deterministic reducer remains the certified V1 reducer. V2 binds every event
    to the player and currently-owned investigator and includes that actor trace in the
    continuity fingerprint. No reroll occurs during replay.
    """
    @classmethod
    def append_player_action(cls, engine, player_id, character_id, action_id, roll, delta=0,
                             event_id=None, session_id='MULTIPLAYER_SESSION'):
        state, before_commit = engine.db.state()
        session = state.get('interface_session') or {}
        players = session.get('players') or []
        party = MultiplayerRuntimeContractV2.validate_party(engine, players, require_interface=True)
        if party.get('status') != 'PASS':
            return {'status':'FAIL_CLOSED','code':'MULTIPLAYER_PARTY_INVALID','detail':party}
        if party['bindings'].get(player_id) != character_id:
            return {'status':'FAIL_CLOSED','code':'ACTOR_CONTROL_MISMATCH','previous_commit':before_commit,'new_commit':before_commit}
        if not isinstance(roll, int) or isinstance(roll, bool) or not 1 <= roll <= 100:
            return {'status':'FAIL_CLOSED','code':'ROLL_INVALID','previous_commit':before_commit,'new_commit':before_commit}
        payload={'roll':roll,'delta':int(delta),'player_id':player_id,'character_id':character_id}
        return StrictReplaySaveResumeContinuityV1.append_action(
            engine, session_id, action_id, payload, event_id or f'{session_id}:{before_commit+1}:{player_id}'
        )

    @classmethod
    def actor_trace(cls, engine):
        state,_=engine.db.state(); journal=state.get(StrictReplaySaveResumeContinuityV1.JOURNAL_KEY,[])
        out=[]
        for row in journal:
            ev=row.get('event',{}); p=ev.get('payload',{})
            out.append({'event_id':ev.get('event_id'),'action_id':ev.get('action_id'),
                        'player_id':p.get('player_id'),'character_id':p.get('character_id'),
                        'roll':p.get('roll'),'event_hash':row.get('event_hash')})
        return out

    @classmethod
    def verify_engine(cls, engine, expected_actor_trace=None):
        base=StrictReplaySaveResumeContinuityV1.verify_engine(engine)
        if base.get('status')!='REPLAY_MATCH': return base
        state,_=engine.db.state(); session=state.get('interface_session') or {}; players=session.get('players') or []
        party=MultiplayerRuntimeContractV2.validate_party(engine,players,require_interface=True)
        if party.get('status')!='PASS': return {'status':'FAIL_CLOSED','reason':'MULTIPLAYER_PARTY_INVALID','detail':party}
        journal=state.get(StrictReplaySaveResumeContinuityV1.JOURNAL_KEY,[])
        jv=StrictRecoveryJournal.verify(journal)
        if not jv.get('valid'): return {'status':'FAIL_CLOSED','reason':'STRICT_JOURNAL_INVALID','detail':jv}
        trace=[]
        for i,row in enumerate(journal):
            ev=row['event']; payload=ev.get('payload')
            if not isinstance(payload,dict):return {'status':'FAIL_CLOSED','reason':'ACTOR_PAYLOAD_INVALID','index':i}
            pid=payload.get('player_id'); cid=payload.get('character_id')
            if pid not in players:return {'status':'FAIL_CLOSED','reason':'ACTOR_PLAYER_NOT_IN_SESSION','index':i}
            if party['bindings'].get(pid)!=cid:return {'status':'FAIL_CLOSED','reason':'ACTOR_CONTROL_MISMATCH','index':i}
            if not isinstance(payload.get('roll'),int) or isinstance(payload.get('roll'),bool) or not 1<=payload['roll']<=100:
                return {'status':'FAIL_CLOSED','reason':'ROLL_INVALID','index':i}
            trace.append({'event_id':ev['event_id'],'action_id':ev['action_id'],'player_id':pid,
                          'character_id':cid,'roll':payload['roll'],'event_hash':row['event_hash']})
        if expected_actor_trace is not None and trace!=expected_actor_trace:
            return {'status':'REPLAY_DIVERGENCE','reason':'ACTOR_TRACE_MISMATCH','actual':trace,'expected':expected_actor_trace}
        return {'status':'REPLAY_MATCH','events':len(trace),'actor_trace':trace,'state':base.get('state')}

    @classmethod
    def continuity_fingerprint(cls,engine):
        fp=StrictReplaySaveResumeContinuityV1.continuity_fingerprint(engine)
        fp['actor_trace']=cls.actor_trace(engine)
        return fp

    @staticmethod
    def compare(a,b):
        keys=('commit_sequence','canonical_digest','strict_state_digest','journal_hashes','rolls','actions','commit_trace','actor_trace')
        diff={k:{'continuous':a.get(k),'resumed':b.get(k)} for k in keys if a.get(k)!=b.get(k)}
        return {'status':'REPLAY_MATCH' if not diff else 'REPLAY_DIVERGENCE','diff':diff}
