from dataclasses import dataclass, field
from typing import List, Dict

READY='READY'; PENDING='PENDING'
NORMAL='NORMAL_LIBRE'; ASSISTED='FACILE_ASSISTE'

@dataclass
class CharacterDraft:
    source_accessible: bool=True
    occupation_resolved: bool=True
    occupation_total_ok: bool=True
    credit_in_range: bool=True
    required_skills_present: bool=True
    personal_total_ok: bool=True
    backstory_ok: bool=True
    finances_ok: bool=True
    equipment_ok: bool=True
    interrupted: bool=False
    tx_version: int=0

    @property
    def status(self):
        checks=(self.source_accessible,self.occupation_resolved,self.occupation_total_ok,
                self.credit_in_range,self.required_skills_present,self.personal_total_ok,
                self.backstory_ok,self.finances_ok,self.equipment_ok,not self.interrupted)
        return READY if all(checks) else PENDING

@dataclass
class StartupState:
    engine_rules_validated: bool=False
    scenario_accessible: bool=False
    player_count: int|None=None
    slots: List[CharacterDraft]=field(default_factory=list)
    assistance: List[str]=field(default_factory=list)
    party_state_initialized: bool=False
    character_states_initialized: bool=False
    partitions_active: bool=False
    initial_save_ready: bool=False
    preflight_critical_ok: bool=False
    diagnostic_mode: bool=False
    ironman_mode: bool=True
    committed_rolls: Dict[str,int]=field(default_factory=dict)
    autosave_revision: int=0
    knowledge: List[set]=field(default_factory=list)

    def configure_players(self,count:int):
        if count not in (1,2,3,4): raise ValueError('player_count must be 1..4')
        self.player_count=count
        self.slots=[CharacterDraft() for _ in range(count)]
        self.assistance=[NORMAL for _ in range(count)]
        self.knowledge=[set() for _ in range(count)]
        self.party_state_initialized=True
        self.character_states_initialized=True

    def set_assistance(self,idx:int,mode:str):
        if mode not in (NORMAL,ASSISTED): raise ValueError('invalid assistance mode')
        self.assistance[idx]=mode

    def can_start_scenario(self)->bool:
        return bool(
            self.engine_rules_validated and self.scenario_accessible
            and self.player_count in (1,2,3,4)
            and len(self.slots)==self.player_count
            and len(self.assistance)==self.player_count
            and all(m in (NORMAL,ASSISTED) for m in self.assistance)
            and all(s.status==READY for s in self.slots)
            and self.party_state_initialized and self.character_states_initialized
            and self.partitions_active and self.initial_save_ready
            and self.preflight_critical_ok and not self.diagnostic_mode
        )

    def commit_roll(self,roll_id:str,value:int):
        if roll_id in self.committed_rolls: raise RuntimeError('committed roll immutable')
        self.committed_rolls[roll_id]=value; self.autosave_revision+=1

    def observe(self,player:int,clue:str): self.knowledge[player].add(clue)
    def transmit(self,src:int,dst:int,clue:str):
        if clue not in self.knowledge[src]: raise RuntimeError('source player does not know clue')
        self.knowledge[dst].add(clue)

def continue_status(save_exists:bool)->str:
    return 'CONTINUE_READY' if save_exists else 'NO_SAVE_CLEAN'

def interface_rule(mode:str):
    if mode==NORMAL: return {'prompt':'OPEN','suggestions':0,'free_action':True,'help_control':True}
    if mode==ASSISTED: return {'prompt':'OPEN','suggestions':3,'free_action':True,'help_control':True,'source':'PLAYER_KNOWLEDGE_ONLY'}
    raise ValueError(mode)
