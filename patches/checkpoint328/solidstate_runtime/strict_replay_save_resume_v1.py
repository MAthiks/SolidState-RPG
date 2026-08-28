from copy import deepcopy
from .strict_replay_event import StrictReplayEvent
from .strict_recovery_journal import StrictRecoveryJournal
from .strict_replay_verifier import StrictReplayVerifier
from .canonical_state_digest import CanonicalStateDigest

class StrictReplaySaveResumeContinuityV1:
    STATE_KEY='strict_replay_state'
    JOURNAL_KEY='strict_replay_journal'

    @staticmethod
    def initial_state():
        return {'revision':0,'score':0,'rolls':[],'actions':[]}

    @staticmethod
    def action_reducer(state, action_id, payload):
        if not isinstance(payload,dict): return {'committed':False,'reason':'PAYLOAD_INVALID'}
        if not isinstance(payload.get('roll'),int) or not 1 <= payload['roll'] <= 100:
            return {'committed':False,'reason':'ROLL_INVALID'}
        if not isinstance(payload.get('delta'),int): return {'committed':False,'reason':'DELTA_INVALID'}
        out=deepcopy(state)
        out['revision']=int(out.get('revision',-1))+1
        out['score']=int(out.get('score',0))+payload['delta']
        out.setdefault('rolls',[]).append(payload['roll'])
        out.setdefault('actions',[]).append(action_id)
        return {'committed':True,'state':out}

    @classmethod
    def strict_reducer(cls,state,event):
        out=cls.action_reducer(state,event.get('action_id'),deepcopy(event.get('payload',{})))
        if not out.get('committed'): return out
        if out['state'].get('revision') != event.get('resulting_revision'):
            return {'committed':False,'reason':'REVISION_CONTRACT'}
        return out

    @classmethod
    def append_action(cls,engine,session_id,action_id,payload,event_id):
        canonical, before_commit=engine.db.state()
        before=deepcopy(canonical.get(cls.STATE_KEY,cls.initial_state()))
        reduced=cls.action_reducer(before,action_id,payload)
        if not reduced.get('committed'):
            return {'status':'FAIL_CLOSED','code':reduced.get('reason')}
        after=reduced['state']
        built=StrictReplayEvent.build(session_id,action_id,before,after,payload=payload,
                                      provenance='SUPPLIED_DETERMINISTIC_REPLAY_TAPE',event_id=event_id)
        if built.get('status')!='READY': return {'status':'FAIL_CLOSED','code':built.get('code')}
        journal=deepcopy(canonical.get(cls.JOURNAL_KEY,[]))
        appended=StrictRecoveryJournal.append(journal,built['event'])
        if appended.get('status')!='APPENDED': return {'status':'FAIL_CLOSED','code':appended.get('code')}
        def mutate(s):
            s[cls.STATE_KEY]=deepcopy(after)
            s[cls.JOURNAL_KEY]=deepcopy(appended['journal'])
        tx=engine.transact(mutate,[cls.STATE_KEY,cls.JOURNAL_KEY])
        if tx.get('status')!='COMMIT': return {'status':'FAIL_CLOSED','code':'ENGINE_TRANSACTION_FAILED'}
        return {'status':'COMMIT','previous_commit':before_commit,'new_commit':tx['new_commit'],
                'event':deepcopy(built['event']),'event_hash':appended['journal'][-1]['event_hash']}

    @classmethod
    def verify_engine(cls,engine):
        canonical,commit=engine.db.state()
        state=canonical.get(cls.STATE_KEY)
        journal=canonical.get(cls.JOURNAL_KEY)
        if not isinstance(state,dict) or not isinstance(journal,list):
            return {'status':'FAIL_CLOSED','reason':'STRICT_STATE_OR_JOURNAL_MISSING'}
        return StrictReplayVerifier.verify(cls.initial_state(),journal,cls.strict_reducer,state)

    @classmethod
    def validate_bundle_strict(cls,bundle):
        try:
            canonical=bundle['payload']['canonical_state']
            state=canonical[cls.STATE_KEY]
            journal=canonical[cls.JOURNAL_KEY]
        except Exception:
            return {'status':'FAIL_CLOSED','reason':'STRICT_SAVE_STATE_MISSING'}
        result=StrictReplayVerifier.verify(cls.initial_state(),journal,cls.strict_reducer,state)
        if result.get('status')!='REPLAY_MATCH':
            return {'status':'FAIL_CLOSED','reason':'STRICT_SAVE_REPLAY_INVALID','detail':result}
        return {'status':'PASS','events':len(journal),'final_digest':CanonicalStateDigest.digest(state)}

    @classmethod
    def restore_verified(cls,save_manager,bundle):
        pre=cls.validate_bundle_strict(bundle)
        if pre.get('status')!='PASS': return pre
        restored=save_manager.restore(bundle)
        if restored.get('status')!='RESTORED': return restored
        post=cls.verify_engine(save_manager.e)
        if post.get('status')!='REPLAY_MATCH':
            return {'status':'FAIL_CLOSED','reason':'STRICT_POST_RESTORE_REPLAY_INVALID','detail':post}
        return {'status':'RESTORED_STRICT','commit':restored['commit'],'events':pre['events'],'session':restored['session']}

    @staticmethod
    def commit_semantic_trace(engine):
        rows=engine.db.conn.execute('SELECT commit_sequence,changed_paths_json,state_hash FROM commits ORDER BY commit_sequence').fetchall()
        return [dict(r) for r in rows]

    @classmethod
    def continuity_fingerprint(cls,engine):
        canonical,commit=engine.db.state()
        journal=canonical.get(cls.JOURNAL_KEY,[])
        return {
            'commit_sequence':commit,
            'canonical_digest':CanonicalStateDigest.digest(canonical),
            'strict_state_digest':CanonicalStateDigest.digest(canonical.get(cls.STATE_KEY,{})),
            'journal_hashes':[r.get('event_hash') for r in journal],
            'rolls':list(canonical.get(cls.STATE_KEY,{}).get('rolls',[])),
            'actions':list(canonical.get(cls.STATE_KEY,{}).get('actions',[])),
            'commit_trace':cls.commit_semantic_trace(engine),
        }

    @staticmethod
    def compare(a,b):
        keys=('commit_sequence','canonical_digest','strict_state_digest','journal_hashes','rolls','actions','commit_trace')
        diff={k:{'continuous':a.get(k),'resumed':b.get(k)} for k in keys if a.get(k)!=b.get(k)}
        return {'status':'REPLAY_MATCH' if not diff else 'REPLAY_DIVERGENCE','diff':diff}
