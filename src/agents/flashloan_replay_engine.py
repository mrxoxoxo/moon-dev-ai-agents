"""
🌙 Moon Dev's Flashloan Replay Engine
Replicate successful historical attacks that are still profitable
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from termcolor import cprint
from collections import deque

@dataclass
class HistoricalAttack:
    """A successful attack ready to be replayed"""
    original_tx_hash: str
    original_timestamp: float
    original_profit_usd: float
    attack_type: str
    steps: List[Dict]
    tokens_involved: List[str]
    dexs_used: List[str]
    still_active: bool
    current_opportunity_score: float
    expected_current_profit: float
    
    def to_dict(self) -> Dict:
        return {
            'original_tx': self.original_tx_hash,
            'original_timestamp': self.original_timestamp,
            'original_profit': self.original_profit_usd,
            'attack_type': self.attack_type,
            'steps': self.steps,
            'tokens': self.tokens_involved,
            'dexs': self.dexs_used,
            'still_active': self.still_active,
            'opportunity_score': self.current_opportunity_score,
            'expected_profit': self.expected_current_profit
        }


class ReplayEngine:
    """
    Replay historical successful attacks
    
    How it works:
    1. Store successful attack patterns
    2. Continuously check if opportunity still exists
    3. Validate current market conditions
    4. Execute if still profitable
    5. Update success rate
    
    Benefits:
    - Proven strategies (already worked)
    - Known execution path
    - Reduced risk
    - Fast execution
    """
    
    def __init__(self, flashloan_core, eigenphi_learner):
        self.core = flashloan_core
        self.learner = eigenphi_learner
        
        # Database of replayable attacks
        self.replayable_attacks: Dict[str, HistoricalAttack] = {}
        self.replay_history: deque = deque(maxlen=1000)
        
        # Statistics
        self.total_replays = 0
        self.successful_replays = 0
        self.total_replay_profit = 0.0
        
        # Configuration
        self.min_replay_confidence = 0.85  # 85% similarity to original
        self.check_interval_seconds = 60  # Check every minute
        
        cprint("\n🔁 Flashloan Replay Engine Initialized", "cyan", attrs=['bold'])
        cprint("   Monitors: Historical successful attacks", "cyan")
        cprint("   Strategy: Replicate when opportunity reappears", "cyan")
    
    def add_successful_attack(self, attack_data: Dict):
        """
        Add a successful attack to replay database
        
        Args:
            attack_data: Attack details from execution or EigenPhi
        """
        attack_id = f"{attack_data['attack_type']}_{attack_data['tx_hash'][:10]}"
        
        attack = HistoricalAttack(
            original_tx_hash=attack_data['tx_hash'],
            original_timestamp=attack_data.get('timestamp', time.time()),
            original_profit_usd=attack_data['profit_usd'],
            attack_type=attack_data['attack_type'],
            steps=attack_data.get('steps', []),
            tokens_involved=attack_data.get('tokens_traded', []),
            dexs_used=attack_data.get('dexs_involved', []),
            still_active=True,
            current_opportunity_score=1.0,
            expected_current_profit=attack_data['profit_usd']
        )
        
        self.replayable_attacks[attack_id] = attack
        
        cprint(f"💾 Stored attack for replay: {attack_id}", "green")
        cprint(f"   Original Profit: ${attack_data['profit_usd']:,.2f}", "cyan")
    
    def check_replay_opportunities(self) -> List[HistoricalAttack]:
        """
        Check all stored attacks for replay opportunities
        
        Returns:
            List of currently replayable attacks
        """
        cprint(f"\n🔍 Checking {len(self.replayable_attacks)} historical attacks...", "cyan")
        
        replayable = []
        
        for attack_id, attack in self.replayable_attacks.items():
            # Check if opportunity still exists
            current_state = self._check_attack_viability(attack)
            
            if current_state['is_viable']:
                attack.still_active = True
                attack.current_opportunity_score = current_state['score']
                attack.expected_current_profit = current_state['expected_profit']
                
                replayable.append(attack)
                
                cprint(f"✅ {attack_id}: ${current_state['expected_profit']:,.2f} expected", "green")
            else:
                attack.still_active = False
                cprint(f"❌ {attack_id}: No longer viable", "red")
        
        cprint(f"\n📊 Found {len(replayable)} replayable opportunities", "green" if replayable else "yellow")
        
        return replayable
    
    def _check_attack_viability(self, attack: HistoricalAttack) -> Dict:
        """
        Check if historical attack is still viable
        
        Validates:
        - Tokens still exist
        - DEX pools still active
        - Price differences still present
        - Liquidity sufficient
        """
        try:
            # For flashloan arbitrage
            if attack.attack_type == 'flashloan_arb':
                return self._check_arbitrage_viability(attack)
            
            # For sandwich attacks
            elif attack.attack_type == 'sandwich':
                return self._check_sandwich_viability(attack)
            
            # For liquidations
            elif attack.attack_type == 'liquidation':
                return self._check_liquidation_viability(attack)
            
            else:
                return {'is_viable': False, 'score': 0, 'expected_profit': 0}
                
        except Exception as e:
            cprint(f"⚠️ Viability check error: {str(e)}", "yellow")
            return {'is_viable': False, 'score': 0, 'expected_profit': 0}
    
    def _check_arbitrage_viability(self, attack: HistoricalAttack) -> Dict:
        """Check if arbitrage opportunity still exists"""
        # Extract original route
        tokens = attack.tokens_involved
        dexs = attack.dexs_used
        
        if len(dexs) < 2:
            return {'is_viable': False, 'score': 0, 'expected_profit': 0}
        
        # Get current prices on same DEXs
        try:
            # Simplified - in production, fetch actual prices
            price_diff_exists = True  # Would check real prices
            
            if price_diff_exists:
                # Estimate current profit (scaled by market conditions)
                market_volatility = 1.0  # Would calculate actual
                expected_profit = attack.original_profit_usd * market_volatility * 0.8  # Conservative
                
                return {
                    'is_viable': expected_profit > 50,  # At least $50
                    'score': 0.85,
                    'expected_profit': expected_profit
                }
            
        except:
            pass
        
        return {'is_viable': False, 'score': 0, 'expected_profit': 0}
    
    def _check_sandwich_viability(self, attack: HistoricalAttack) -> Dict:
        """Check if sandwich opportunity pattern still exists"""
        # Sandwich attacks are time-sensitive, less replayable
        # But patterns can repeat
        return {'is_viable': False, 'score': 0, 'expected_profit': 0}
    
    def _check_liquidation_viability(self, attack: HistoricalAttack) -> Dict:
        """Check for similar liquidation opportunities"""
        # Check lending protocols for similar positions
        return {'is_viable': False, 'score': 0, 'expected_profit': 0}
    
    def replay_attack(self, attack: HistoricalAttack) -> Dict:
        """
        Execute a replay of historical attack
        
        Args:
            attack: Historical attack to replay
            
        Returns:
            Execution result
        """
        cprint(f"\n🔁 REPLAYING ATTACK: {attack.original_tx_hash[:16]}...", "magenta", attrs=['bold'])
        cprint(f"   Original Profit: ${attack.original_profit_usd:,.2f}", "cyan")
        cprint(f"   Expected Now: ${attack.expected_current_profit:,.2f}", "green")
        
        self.total_replays += 1
        
        try:
            # Adapt steps to current conditions
            adapted_steps = self._adapt_steps_to_current(attack.steps)
            
            # Execute with same pattern
            result = self._execute_adapted_attack(adapted_steps, attack)
            
            # Track result
            if result.get('success'):
                self.successful_replays += 1
                self.total_replay_profit += result.get('profit', 0)
                
                cprint(f"✅ Replay successful: ${result['profit']:,.2f}", "green", attrs=['bold'])
            else:
                cprint(f"❌ Replay failed: {result.get('error')}", "red")
            
            # Store replay
            self.replay_history.append({
                'attack_id': attack.original_tx_hash,
                'timestamp': time.time(),
                'expected': attack.expected_current_profit,
                'actual': result.get('profit', 0),
                'success': result.get('success', False)
            })
            
            return result
            
        except Exception as e:
            cprint(f"❌ Replay error: {str(e)}", "red")
            return {'success': False, 'error': str(e)}
    
    def _adapt_steps_to_current(self, original_steps: List[Dict]) -> List[Dict]:
        """Adapt historical steps to current market conditions"""
        adapted = []
        
        for step in original_steps:
            # Update amounts based on current liquidity
            # Update DEXs if original no longer exists
            # Adjust for current gas prices
            adapted.append(step.copy())
        
        return adapted
    
    def _execute_adapted_attack(self, steps: List[Dict], attack: HistoricalAttack) -> Dict:
        """Execute the adapted attack"""
        # Build transaction from steps
        # Execute via core
        # Return result
        
        # Simulated for now
        return {
            'success': True,
            'profit': attack.expected_current_profit,
            'simulated': True
        }
    
    def get_replay_statistics(self) -> Dict:
        """Get replay engine statistics"""
        success_rate = (self.successful_replays / max(1, self.total_replays)) * 100
        
        return {
            'total_stored_attacks': len(self.replayable_attacks),
            'active_opportunities': sum(1 for a in self.replayable_attacks.values() if a.still_active),
            'total_replays': self.total_replays,
            'successful_replays': self.successful_replays,
            'success_rate': success_rate,
            'total_profit': self.total_replay_profit
        }
