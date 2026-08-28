import json, hashlib, hmac
from copy import deepcopy

class SaveResumeSelectedScenarioAndFullInterfaceV1:
    SCHEMA='SOLIDSTATE_SAVE_RESUME_V1'
    CHECKPOINT_FLOOR=326
    AUTHORITY_ID='MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION_V1'
    TABLES=(
      'commits','characters','party','mechanical_registry','inventory','mechanical_values',
      'ammunition_state','wounds_state','treatment_state','scenarios','knowledge_partitions',
      'scenario_state','scenario_events','discovered_clues','journey_state','session_events',
      'roll_ledger','playloop_turns','action_log','world_facts'
    )
    def __init__(self,engine,scenario_selection,secret):
        self.e=engine; self.selection=scenario_selection
        if isinstance(secret,str): secret=secret.encode('utf-8')
        if not isinstance(secret,(bytes,bytearray)) or len(secret)<32: raise ValueError('SAVE_SECRET_MIN_32_BYTES')
        self.secret=bytes(secret)
    @staticmethod
    def _canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    def _mac(self,payload): return hmac.new(self.secret,self._canon(payload).encode(),hashlib.sha256).hexdigest()
    def _schema_fp(self):
        data=[]
        for t in self.TABLES:
            cols=[dict(r) for r in self.e.db.conn.execute(f'PRAGMA table_info({t})').fetchall()]
            data.append([t,[(c['name'],c['type'],c['notnull'],c['pk']) for c in cols]])
        return hashlib.sha256(self._canon(data).encode()).hexdigest()
    def _rows(self,t):
        rows=[dict(r) for r in self.e.db.conn.execute(f'SELECT * FROM {t}').fetchall()]
        return sorted(rows,key=self._canon)
    def _validate_session(self,state,tables):
        s=state.get('interface_session')
        if not isinstance(s,dict) or s.get('phase')!='SESSION_READY': return 'SESSION_NOT_READY'
        players=s.get('players'); cmap=s.get('control_map')
        if not isinstance(players,list) or not 1<=len(players)<=4 or len(set(players))!=len(players): return 'PLAYER_SET_INVALID'
        if not isinstance(cmap,dict) or set(cmap)!=set(players) or len(set(cmap.values()))!=len(players): return 'CONTROL_MAP_INVALID'
        chars={r['character_id']:r for r in tables['characters']}
        party={r['player_id']:r['character_id'] for r in tables['party']}
        if any(party.get(p)!=cmap[p] for p in players): return 'PARTY_CONTROL_MAP_MISMATCH'
        canonical_party=state.get('party',{})
        if any(canonical_party.get(p)!=cmap[p] for p in players): return 'CANONICAL_CONTROL_MAP_MISMATCH'
        for p in players:
            cid=cmap[p]
            if cid not in chars or chars[cid]['owner_id']!=p: return 'CONTROL_OWNERSHIP_INVALID'
        selected=self.selection.select(s.get('scenario_key'))
        if selected.get('status')!='SELECTED' or selected.get('selection',{}).get('certification_status')!='PASS_REAL': return 'SCENARIO_NOT_PASS_REAL'
        return None
    def save(self,save_id):
        state,commit=self.e.db.state(); tables={t:self._rows(t) for t in self.TABLES}
        err=self._validate_session(state,tables)
        if err:return {'status':'BLOCKED','code':err}
        payload={'schema':self.SCHEMA,'checkpoint_floor':self.CHECKPOINT_FLOOR,'authority_id':self.AUTHORITY_ID,
                 'save_id':save_id,'commit_sequence':commit,'schema_fingerprint':self._schema_fp(),
                 'canonical_state':deepcopy(state),'tables':tables,
                 'runtime_context':{'active_scenario_id':self.e.scenario.active_scenario_id}}
        raw=self._canon(payload).encode(); dig=hashlib.sha256(raw).hexdigest()
        return {'status':'SAVED','bundle':{'payload':payload,'auth':{'algorithm':'HMAC-SHA256','payload_sha256':dig,'hmac_sha256':self._mac(payload)}}}
    def _verify_bundle(self,b):
        if not isinstance(b,dict) or set(b)!={'payload','auth'}: return 'BUNDLE_SHAPE_INVALID'
        p=b['payload']; a=b['auth']
        if not isinstance(p,dict) or not isinstance(a,dict): return 'BUNDLE_SHAPE_INVALID'
        if p.get('schema')!=self.SCHEMA or p.get('checkpoint_floor')!=326 or p.get('authority_id')!=self.AUTHORITY_ID:return 'AUTHORITY_FLOOR_INVALID'
        if a.get('algorithm')!='HMAC-SHA256':return 'AUTH_ALGORITHM_INVALID'
        raw=self._canon(p).encode()
        if hashlib.sha256(raw).hexdigest()!=a.get('payload_sha256'):return 'PAYLOAD_HASH_MISMATCH'
        if not hmac.compare_digest(self._mac(p),str(a.get('hmac_sha256',''))):return 'SAVE_AUTHENTICATION_FAILED'
        if p.get('schema_fingerprint')!=self._schema_fp():return 'DB_SCHEMA_MISMATCH'
        if set(p.get('tables',{}))!=set(self.TABLES):return 'TABLE_SET_INVALID'
        commit=p.get('commit_sequence')
        if not isinstance(commit,int) or commit<0:return 'COMMIT_SEQUENCE_INVALID'
        seqs=[r.get('commit_sequence') for r in p['tables']['commits']]
        if not seqs or max(seqs)!=commit:return 'COMMIT_LEDGER_MISMATCH'
        return None
    def _pristine(self):
        state,commit=self.e.db.state()
        if commit!=0 or state!={'scenario_started':False}: return False
        for t in self.TABLES:
            if self.e.db.conn.execute(f'SELECT COUNT(*) n FROM {t}').fetchone()['n']!=0:return False
        return True
    def restore(self,bundle):
        err=self._verify_bundle(bundle)
        if err:return {'status':'FAIL_CLOSED','code':err}
        p=bundle['payload']; err=self._validate_session(p['canonical_state'],p['tables'])
        if err:return {'status':'FAIL_CLOSED','code':err}
        if not self._pristine():return {'status':'FAIL_CLOSED','code':'TARGET_NOT_PRISTINE'}
        conn=self.e.db.conn
        try:
            conn.execute('PRAGMA foreign_keys=OFF'); conn.execute('BEGIN IMMEDIATE')
            self.e.db.set_state(deepcopy(p['canonical_state']),int(p['commit_sequence']))
            for t in self.TABLES:
                actual=[r['name'] for r in conn.execute(f'PRAGMA table_info({t})').fetchall()]
                for row in p['tables'][t]:
                    if set(row)!=set(actual): raise ValueError('ROW_SCHEMA_MISMATCH')
                    qs=','.join('?' for _ in actual); cols=','.join(actual)
                    conn.execute(f'INSERT INTO {t}({cols}) VALUES({qs})',[row[c] for c in actual])
            fk=conn.execute('PRAGMA foreign_key_check').fetchall()
            if fk: raise ValueError('FOREIGN_KEY_INVALID')
            conn.commit(); conn.execute('PRAGMA foreign_keys=ON')
        except Exception:
            conn.rollback(); conn.execute('PRAGMA foreign_keys=ON')
            return {'status':'FAIL_CLOSED','code':'RESTORE_TRANSACTION_REJECTED'}
        self.e.scenario.active_scenario_id=p.get('runtime_context',{}).get('active_scenario_id')
        s=p['canonical_state']['interface_session']
        return {'status':'RESTORED','code':'SAVE_RESUME_V1_READY','commit':p['commit_sequence'],
                'session':{'scenario_key':s['scenario_key'],'scenario_title':s['scenario_title'],
                           'certification_status':s['certification_status'],'players':list(s['players']),
                           'control_map':deepcopy(s['control_map']),'phase':s['phase']}}
