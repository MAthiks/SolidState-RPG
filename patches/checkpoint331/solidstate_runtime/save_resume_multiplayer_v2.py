import json, hashlib, hmac
from copy import deepcopy
from .save_resume_v1 import SaveResumeSelectedScenarioAndFullInterfaceV1

class MultiplayerSaveResumeRecertificationV2(SaveResumeSelectedScenarioAndFullInterfaceV1):
    SCHEMA='SOLIDSTATE_MULTIPLAYER_SAVE_RESUME_V2'
    CHECKPOINT_FLOOR=330
    AUTHORITY_ID='MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2'

    def _validate_session(self,state,tables):
        err=super()._validate_session(state,tables)
        if err:return err
        s=state['interface_session']; players=s['players']; cmap=s['control_map']
        chars={r['character_id']:r for r in tables['characters']}
        party={r['player_id']:r['character_id'] for r in tables['party']}
        if set(party)!=set(players):return 'PARTY_PLAYER_SET_MISMATCH'
        if party!=cmap:return 'PARTY_INTERFACE_CONTROL_MAP_MISMATCH'
        if state.get('party')!=party:return 'CANONICAL_SQL_PARTY_MISMATCH'
        canonical_chars=state.get('characters',{})
        mech_rows={}
        for r in tables['mechanical_values']: mech_rows.setdefault(r['entity_id'],{})[r['key']]=r['value']
        wound_rows={r['entity_id']:r for r in tables['wounds_state']}
        registry={r['object_id']:r for r in tables['mechanical_registry']}
        inventory={}
        for r in tables['inventory']: inventory.setdefault(r['owner_id'],{})[r['object_id']]=r['quantity']
        know_rows={}
        for r in tables['knowledge_partitions']:
            if r['visibility'] not in ('PLAYER','KEEPER'):return 'KNOWLEDGE_VISIBILITY_INVALID'
            know_rows.setdefault(r['character_id'],{})[r['knowledge_id']]={'visibility':r['visibility'],'source_authority':r['source_authority']}
        can_mech=state.get('mechanical_values',{}); can_wounds=state.get('wounds',{}); can_registry=state.get('mechanical_registry',{}); can_knowledge=state.get('knowledge',{})
        for p in players:
            cid=cmap[p]
            try: sql_char=json.loads(chars[cid]['state_json'])
            except Exception:return 'CHARACTER_STATE_INVALID'
            if canonical_chars.get(cid)!=sql_char:return 'CHARACTER_CANONICAL_SQL_MISMATCH'
            if chars[cid]['owner_id']!=p:return 'CONTROL_OWNERSHIP_INVALID'
            vals=mech_rows.get(cid,{})
            for key in ('HP','SAN','MP','Luck'):
                if key not in vals:return 'PLAYER_MECHANICAL_VALUE_MISSING'
                if can_mech.get(cid,{}).get(key)!=vals[key]:return 'MECHANICAL_CANONICAL_SQL_MISMATCH'
            wr=wound_rows.get(cid); cw=can_wounds.get(cid)
            if not wr or not isinstance(cw,dict):return 'PLAYER_WOUND_STATE_MISSING'
            for sqlk,cank in (('max_hp','max_hp'),('current_hp','current_hp'),('major_wound','major_wound'),('dying','dying')):
                sv=wr[sqlk]
                if sqlk in ('major_wound','dying'):sv=bool(sv)
                if cw.get(cank)!=sv:return 'WOUND_CANONICAL_SQL_MISMATCH'
            if wr['current_hp']!=vals['HP']:return 'HP_WOUND_MECHANIC_MISMATCH'
            for oid,qty in inventory.get(cid,{}).items():
                if qty<=0:return 'PLAYER_INVENTORY_QUANTITY_INVALID'
                rr=registry.get(oid)
                if not rr or rr['owner_id']!=cid:return 'INVENTORY_REGISTRY_OWNER_MISMATCH'
                cr=can_registry.get(oid)
                if not isinstance(cr,dict) or cr.get('owner_id')!=cid:return 'REGISTRY_CANONICAL_SQL_MISMATCH'
            for oid,rr in registry.items():
                if rr['owner_id']==cid and inventory.get(cid,{}).get(oid,0)<=0:return 'REGISTRY_ITEM_MISSING_FROM_INVENTORY'
            ck=can_knowledge.get(cid,{})
            if ck!=know_rows.get(cid,{}):return 'KNOWLEDGE_CANONICAL_SQL_MISMATCH'
        return None

    def _verify_bundle(self,b):
        if not isinstance(b,dict) or set(b)!={'payload','auth'}: return 'BUNDLE_SHAPE_INVALID'
        p=b['payload']; a=b['auth']
        if not isinstance(p,dict) or not isinstance(a,dict): return 'BUNDLE_SHAPE_INVALID'
        if p.get('schema')!=self.SCHEMA or p.get('checkpoint_floor')!=self.CHECKPOINT_FLOOR or p.get('authority_id')!=self.AUTHORITY_ID:return 'AUTHORITY_FLOOR_INVALID'
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
        if sorted(seqs)!=list(range(1,commit+1)):return 'COMMIT_LEDGER_NOT_CONTIGUOUS'
        return None

    def save(self,save_id):
        out=super().save(save_id)
        if out.get('status')=='SAVED': out['code']='MULTIPLAYER_SAVE_RESUME_V2_SAVED'
        return out

    def restore(self,bundle):
        out=super().restore(bundle)
        if out.get('status')=='RESTORED':out['code']='MULTIPLAYER_SAVE_RESUME_V2_READY'
        return out
