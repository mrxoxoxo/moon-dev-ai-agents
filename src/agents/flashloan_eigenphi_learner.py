"""
🌙 Moon Dev's EigenPhi Learning Engine
Learn from real flashloan attacks and optimize strategies
Built with love by Moon Dev 🚀

Analyzes successful flashloans from https://eigenphi.io/
"""

import os
import sys
import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from termcolor import cprint
from collections import deque, defaultdict
from datetime import datetime, timedelta
import numpy as np

@dataclass
class MEVAttack:
    """A successful MEV attack from EigenPhi (all types)"""
    tx_hash: str
    timestamp: float
    blockchain: str
    attacker: str
    profit_usd: float
    profit_token: str
    flashloan_amount: float  # 0 if no flashloan used
    flashloan_token: str
    protocols_used: List[str]
    attack_type: str  # flashloan_arb, sandwich, frontrun, backrun, liquidation, oracle_manipulation, protocol_exploit
    attack_category: str  # MEV, EXPLOIT, RUG_PULL
    dexs_involved: List[str]
    tokens_traded: List[str]
    victim_txs: List[str]  # For sandwich/frontrun
    steps: List[Dict]
    gas_cost_usd: float
    net_profit_usd: float
    roi_percent: float
    complexity_score: int  # Number of steps
    risk_level: float  # 0-1 (exploits are high risk)
    block_number: int
    position_in_block: int  # Important for MEV ordering
    
    def to_dict(self) -> Dict:
        return {
            'tx_hash': self.tx_hash,
            'timestamp': self.timestamp,
            'blockchain': self.blockchain,
            'attacker': self.attacker,
            'profit_usd': self.profit_usd,
            'profit_token': self.profit_token,
            'flashloan_amount': self.flashloan_amount,
            'flashloan_token': self.flashloan_token,
            'protocols_used': self.protocols_used,
            'attack_type': self.attack_type,
            'dexs_involved': self.dexs_involved,
            'tokens_traded': self.tokens_traded,
            'steps': self.steps,
            'gas_cost_usd': self.gas_cost_usd,
            'net_profit_usd': self.net_profit_usd,
            'roi_percent': self.roi_percent,
            'complexity_score': self.complexity_score
        }


@dataclass
class StrategyPattern:
    """Extracted strategy pattern from multiple attacks"""
    pattern_id: str
    attack_type: str
    frequency: int
    avg_profit_usd: float
    success_rate: float
    protocols: List[str]
    token_patterns: List[str]
    optimal_conditions: Dict
    steps_template: List[str]
    risk_level: float
    adaptable_to_solana: bool
    
    def to_dict(self) -> Dict:
        return {
            'pattern_id': self.pattern_id,
            'attack_type': self.attack_type,
            'frequency': self.frequency,
            'avg_profit_usd': self.avg_profit_usd,
            'success_rate': self.success_rate,
            'protocols': self.protocols,
            'token_patterns': self.token_patterns,
            'optimal_conditions': self.optimal_conditions,
            'steps_template': self.steps_template,
            'risk_level': self.risk_level,
            'adaptable_to_solana': self.adaptable_to_solana
        }


class EigenPhiLearner:
    """
    Learn from ALL MEV attacks and protocol exploits on EigenPhi
    
    Attack Types Analyzed:
    1. Flashloan arbitrage
    2. Sandwich attacks
    3. Front-running
    4. Back-running
    5. Liquidations
    6. Oracle manipulation
    7. Protocol exploits (0-days)
    8. JIT (Just-In-Time) liquidity
    9. NFT sniping
    10. Token launch exploits
    
    Features:
    - Real-time MEV attack monitoring
    - Pattern extraction from successful attacks
    - Adaptation to Solana ecosystem
    - Risk assessment and filtering
    - Continuous strategy optimization
    """
    
    def __init__(self):
        """Initialize EigenPhi learner"""
        # EigenPhi API endpoint (they have a public API)
        self.api_base = "https://api.eigenphi.io/api/v1"
        
        # Historical attack database by type
        self.attack_history: deque = deque(maxlen=1000)
        self.sandwich_attacks: deque = deque(maxlen=500)
        self.frontrun_attacks: deque = deque(maxlen=500)
        self.backrun_attacks: deque = deque(maxlen=500)
        self.liquidation_attacks: deque = deque(maxlen=500)
        self.exploit_attacks: deque = deque(maxlen=200)
        
        # Extracted patterns
        self.patterns: Dict[str, StrategyPattern] = {}
        
        # Learning statistics by attack type
        self.stats = {
            'flashloan_arb': {'count': 0, 'total_profit': 0},
            'sandwich': {'count': 0, 'total_profit': 0},
            'frontrun': {'count': 0, 'total_profit': 0},
            'backrun': {'count': 0, 'total_profit': 0},
            'liquidation': {'count': 0, 'total_profit': 0},
            'oracle_manipulation': {'count': 0, 'total_profit': 0},
            'protocol_exploit': {'count': 0, 'total_profit': 0},
            'jit_liquidity': {'count': 0, 'total_profit': 0},
            'nft_snipe': {'count': 0, 'total_profit': 0}
        }
        
        self.total_attacks_analyzed = 0
        self.total_profit_learned = 0.0
        self.patterns_discovered = 0
        
        # Protocol mapping: Ethereum -> Solana equivalents
        self.protocol_mapping = {
            # DEXs
            'uniswap_v2': 'raydium',
            'uniswap_v3': 'orca_whirlpool',
            'sushiswap': 'raydium',
            'curve': 'mercurial',
            'balancer': 'lifinity',
            '1inch': 'jupiter',
            'pancakeswap': 'raydium',
            
            # Lending
            'aave': 'solend',
            'compound': 'solend',
            'maker': 'kamino',
            
            # Bridges
            'wormhole': 'wormhole',
            'portal': 'portal'
        }
        
        # Token categories
        self.token_categories = {
            'stablecoin': ['USDC', 'USDT', 'DAI', 'BUSD', 'FRAX'],
            'wrapped_eth': ['WETH', 'wETH'],
            'wrapped_btc': ['WBTC', 'renBTC', 'tBTC'],
            'governance': ['COMP', 'AAVE', 'UNI', 'CRV'],
            'meme': ['DOGE', 'SHIB', 'PEPE']
        }
        
        cprint("\n🔬 EigenPhi MEV Learning Engine Initialized", "magenta", attrs=['bold'])
        cprint("   Data Source: https://eigenphi.io/", "cyan")
        cprint("   Learning Scope: ALL MEV attacks + exploits", "cyan")
        cprint("   Attack Types: Flashloan, Sandwich, Frontrun, Backrun, Liquidation, Exploits", "cyan")
        cprint("   Adaptation Target: Solana ecosystem", "cyan")
    
    def fetch_all_mev_attacks(self, hours: int = 24, min_profit: float = 100.0) -> List[MEVAttack]:
        """
        Fetch ALL types of MEV attacks from EigenPhi
        
        Args:
            hours: Look back period in hours
            min_profit: Minimum profit threshold in USD
            
        Returns:
            List of all MEV attacks (flashloan, sandwich, frontrun, etc.)
        """
        cprint(f"\n📡 Fetching ALL MEV attacks from EigenPhi (last {hours}h)...", "cyan", attrs=['bold'])
        cprint("   Types: Flashloan, Sandwich, Frontrun, Backrun, Liquidation, Exploits", "yellow")
        
        attacks = []
        
        try:
            # EigenPhi API endpoint for flashloans
            # Note: This is a simplified example - actual API may differ
            endpoint = f"{self.api_base}/flashloans"
            
            params = {
                'start_time': int((time.time() - hours * 3600) * 1000),
                'end_time': int(time.time() * 1000),
                'min_profit': min_profit,
                'limit': 100
            }
            
            # In production, you would make actual API call
            # response = requests.get(endpoint, params=params)
            
            # For now, simulate with example data
            # In production: Parse actual EigenPhi API responses
            attacks = self._simulate_all_mev_attacks(hours, min_profit)
            
            # Categorize and store
            for attack in attacks:
                self.attack_history.append(attack)
                self.total_attacks_analyzed += 1
                self.total_profit_learned += attack.profit_usd
                
                # Update stats
                if attack.attack_type in self.stats:
                    self.stats[attack.attack_type]['count'] += 1
                    self.stats[attack.attack_type]['total_profit'] += attack.profit_usd
                
                # Store in specialized queues
                if attack.attack_type == 'sandwich':
                    self.sandwich_attacks.append(attack)
                elif attack.attack_type in ['frontrun', 'backrun']:
                    self.frontrun_attacks.append(attack)
                elif attack.attack_type == 'liquidation':
                    self.liquidation_attacks.append(attack)
                elif attack.attack_category == 'EXPLOIT':
                    self.exploit_attacks.append(attack)
            
            # Print breakdown
            cprint(f"\n✅ Fetched {len(attacks)} MEV attacks:", "green")
            cprint(f"   Total Profit: ${sum(a.profit_usd for a in attacks):,.2f}", "green", attrs=['bold'])
            
            attack_counts = defaultdict(int)
            for a in attacks:
                attack_counts[a.attack_type] += 1
            
            for attack_type, count in sorted(attack_counts.items(), key=lambda x: x[1], reverse=True):
                profit = sum(a.profit_usd for a in attacks if a.attack_type == attack_type)
                cprint(f"   {attack_type}: {count} attacks (${profit:,.2f})", "cyan")
            
            return attacks
            
        except Exception as e:
            cprint(f"❌ Error fetching EigenPhi data: {str(e)}", "red")
            return []
    
    def _simulate_all_mev_attacks(self, hours: int, min_profit: float) -> List[MEVAttack]:
        """
        Simulate ALL types of MEV attacks from EigenPhi
        
        In production, this would parse actual EigenPhi API responses
        """
        attacks = []
        
        # Simulate 15-30 attacks across all types
        num_attacks = np.random.randint(15, 31)
        
        attack_type_distribution = {
            'flashloan_arb': 0.25,
            'sandwich': 0.30,
            'frontrun': 0.15,
            'backrun': 0.10,
            'liquidation': 0.10,
            'oracle_manipulation': 0.03,
            'protocol_exploit': 0.02,
            'jit_liquidity': 0.03,
            'nft_snipe': 0.02
        }
        
        for i in range(num_attacks):
            attack_type = np.random.choice(
                list(attack_type_distribution.keys()),
                p=list(attack_type_distribution.values())
            )
            
            # Determine attack category
            if attack_type in ['protocol_exploit', 'oracle_manipulation']:
                category = 'EXPLOIT'
            else:
                category = 'MEV'
            
            # Profit ranges by attack type
            profit_ranges = {
                'flashloan_arb': (min_profit, 5000),
                'sandwich': (50, 2000),
                'frontrun': (100, 1500),
                'backrun': (50, 800),
                'liquidation': (200, 10000),
                'oracle_manipulation': (5000, 100000),
                'protocol_exploit': (10000, 500000),
                'jit_liquidity': (100, 3000),
                'nft_snipe': (500, 50000)
            }
            
            profit_range = profit_ranges.get(attack_type, (min_profit, 5000))
            profit = np.random.uniform(*profit_range)
            gas = np.random.uniform(5, 150)
            
            # Generate victim transactions for sandwich/frontrun
            victim_txs = []
            if attack_type in ['sandwich', 'frontrun']:
                num_victims = np.random.randint(1, 4)
                victim_txs = [f"0x{''.join(np.random.choice(list('0123456789abcdef'), 64))}" for _ in range(num_victims)]
            
            attack = MEVAttack(
                tx_hash=f"0x{''.join(np.random.choice(list('0123456789abcdef'), 64))}",
                timestamp=time.time() - np.random.uniform(0, hours * 3600),
                blockchain=np.random.choice(['ethereum', 'bsc', 'arbitrum']),
                attacker=f"0x{''.join(np.random.choice(list('0123456789abcdef'), 40))}",
                profit_usd=profit,
                profit_token='USDC',
                flashloan_amount=np.random.uniform(10000, 1000000) if 'flashloan' in attack_type else 0,
                flashloan_token='USDC' if 'flashloan' in attack_type else '',
                protocols_used=np.random.choice([
                    ['aave', 'uniswap_v2', 'sushiswap'],
                    ['compound', 'uniswap_v3', 'curve'],
                    ['maker', 'balancer', '1inch']
                ]),
                attack_type=attack_type,
                attack_category=category,
                dexs_involved=np.random.choice([
                    ['uniswap_v2', 'sushiswap'],
                    ['uniswap_v3', 'curve'],
                    ['balancer', '1inch']
                ]),
                tokens_traded=['USDC', 'WETH', 'DAI'],
                victim_txs=victim_txs,
                steps=self._generate_attack_steps(attack_type),
                gas_cost_usd=gas,
                net_profit_usd=profit - gas,
                roi_percent=(profit - gas) / gas * 100 if gas > 0 else 0,
                complexity_score=np.random.randint(2, 10),
                risk_level=0.8 if category == 'EXPLOIT' else 0.3,
                block_number=np.random.randint(18000000, 18100000),
                position_in_block=np.random.randint(0, 300)
            )
            
            attacks.append(attack)
        
        return attacks
    
    def _generate_attack_steps(self, attack_type: str) -> List[Dict]:
        """Generate attack steps based on type"""
        if attack_type == 'flashloan_arb':
            return [
                {'action': 'flashloan', 'protocol': 'aave', 'amount': 100000},
                {'action': 'swap', 'dex': 'uniswap_v2', 'from': 'USDC', 'to': 'WETH'},
                {'action': 'swap', 'dex': 'sushiswap', 'from': 'WETH', 'to': 'USDC'},
                {'action': 'repay', 'protocol': 'aave', 'amount': 100030}
            ]
        
        elif attack_type == 'sandwich':
            return [
                {'action': 'frontrun', 'dex': 'uniswap_v2', 'victim_tx': '0xabc', 'buy_token': 'WETH'},
                {'action': 'victim_executes', 'victim_tx': '0xabc'},
                {'action': 'backrun', 'dex': 'uniswap_v2', 'sell_token': 'WETH', 'profit': True}
            ]
        
        elif attack_type == 'frontrun':
            return [
                {'action': 'detect_pending', 'victim_tx': '0xdef', 'action': 'swap'},
                {'action': 'submit_higher_gas', 'own_tx': '0xghi'},
                {'action': 'execute_first', 'profit_from': 'price_impact'}
            ]
        
        elif attack_type == 'backrun':
            return [
                {'action': 'monitor_mempool', 'target': 'large_swaps'},
                {'action': 'detect_opportunity', 'victim_tx': '0xjkl'},
                {'action': 'submit_immediately_after', 'own_tx': '0xmno'},
                {'action': 'profit_from_price_change'}
            ]
        
        elif attack_type == 'liquidation':
            return [
                {'action': 'flashloan', 'protocol': 'aave', 'amount': 50000},
                {'action': 'liquidate', 'protocol': 'compound', 'target': 'undercollateralized_position'},
                {'action': 'receive_collateral', 'discount': '8%'},
                {'action': 'swap', 'dex': 'uniswap_v3', 'from': 'collateral', 'to': 'USDC'},
                {'action': 'repay', 'protocol': 'aave', 'amount': 50015}
            ]
        
        elif attack_type == 'oracle_manipulation':
            return [
                {'action': 'flashloan', 'protocol': 'aave', 'amount': 500000},
                {'action': 'manipulate_price', 'target': 'low_liquidity_pool'},
                {'action': 'trigger_oracle_update', 'oracle': 'vulnerable_oracle'},
                {'action': 'exploit_mispriced_protocol', 'protocol': 'lending_platform'},
                {'action': 'swap_back', 'dex': 'uniswap_v2'},
                {'action': 'repay', 'protocol': 'aave', 'amount': 500150}
            ]
        
        elif attack_type == 'protocol_exploit':
            return [
                {'action': 'identify_vulnerability', 'type': 'reentrancy|integer_overflow|access_control'},
                {'action': 'flashloan', 'protocol': 'aave', 'amount': 1000000},
                {'action': 'exploit_contract', 'vulnerability': 'specific_bug'},
                {'action': 'drain_funds', 'amount': 'maximum'},
                {'action': 'convert_to_stable', 'dex': '1inch'},
                {'action': 'repay', 'protocol': 'aave'}
            ]
        
        elif attack_type == 'jit_liquidity':
            return [
                {'action': 'detect_large_swap', 'pending_tx': '0xpqr'},
                {'action': 'add_liquidity', 'pool': 'target_pool', 'amount': 'large'},
                {'action': 'wait_for_swap', 'victim_tx': '0xpqr'},
                {'action': 'remove_liquidity', 'collect_fees': True},
                {'action': 'profit_from_fees'}
            ]
        
        elif attack_type == 'nft_snipe':
            return [
                {'action': 'monitor_new_listings', 'marketplace': 'opensea'},
                {'action': 'detect_underpriced', 'nft': 'rare_item'},
                {'action': 'submit_high_gas_buy', 'gas_price': 'max'},
                {'action': 'immediate_relist', 'price': 'market_rate'},
                {'action': 'profit_from_flip'}
            ]
        
        else:
            return [
                {'action': 'unknown', 'type': attack_type}
            ]
    
    def analyze_and_extract_patterns(self, attacks: List[FlashloanAttack]) -> List[StrategyPattern]:
        """
        Analyze attacks and extract reusable patterns
        
        This is the CORE learning function
        """
        cprint(f"\n🔬 Analyzing {len(attacks)} attacks for patterns...", "magenta", attrs=['bold'])
        
        # Group attacks by type and protocol combination
        grouped = defaultdict(list)
        
        for attack in attacks:
            # Create key from attack characteristics
            key = f"{attack.attack_type}_{'-'.join(sorted(attack.protocols_used))}"
            grouped[key].append(attack)
        
        patterns = []
        
        for pattern_key, pattern_attacks in grouped.items():
            if len(pattern_attacks) < 2:  # Need at least 2 instances
                continue
            
            # Extract pattern
            pattern = self._extract_pattern(pattern_key, pattern_attacks)
            
            if pattern:
                patterns.append(pattern)
                self.patterns[pattern.pattern_id] = pattern
                self.patterns_discovered += 1
                
                cprint(f"✅ Pattern discovered: {pattern.pattern_id}", "green")
                cprint(f"   Type: {pattern.attack_type}", "cyan")
                cprint(f"   Frequency: {pattern.frequency} attacks", "cyan")
                cprint(f"   Avg Profit: ${pattern.avg_profit_usd:,.2f}", "green")
                cprint(f"   Adaptable to Solana: {pattern.adaptable_to_solana}", "yellow" if pattern.adaptable_to_solana else "red")
        
        cprint(f"\n📊 Pattern Analysis Complete:", "magenta")
        cprint(f"   Total Patterns: {len(patterns)}", "cyan")
        cprint(f"   Adaptable: {sum(1 for p in patterns if p.adaptable_to_solana)}", "green")
        
        return patterns
    
    def _extract_pattern(self, pattern_key: str, attacks: List[FlashloanAttack]) -> Optional[StrategyPattern]:
        """Extract a reusable pattern from similar attacks"""
        # Calculate statistics
        profits = [a.profit_usd for a in attacks]
        avg_profit = np.mean(profits)
        
        # Success rate (all attacks in this list were successful)
        success_rate = 1.0
        
        # Extract common protocols
        all_protocols = []
        for a in attacks:
            all_protocols.extend(a.protocols_used)
        
        protocol_counts = defaultdict(int)
        for p in all_protocols:
            protocol_counts[p] += 1
        
        common_protocols = [p for p, count in protocol_counts.items() if count >= len(attacks) * 0.5]
        
        # Extract token patterns
        all_tokens = []
        for a in attacks:
            all_tokens.extend(a.tokens_traded)
        
        token_categories = self._categorize_tokens(all_tokens)
        
        # Extract optimal conditions
        optimal_conditions = {
            'min_flashloan_amount': np.percentile([a.flashloan_amount for a in attacks], 25),
            'max_complexity': int(np.median([a.complexity_score for a in attacks])),
            'preferred_tokens': token_categories
        }
        
        # Extract step template
        steps_template = self._extract_step_template(attacks)
        
        # Check if adaptable to Solana
        adaptable = self._check_solana_adaptability(common_protocols)
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(attacks)
        
        pattern = StrategyPattern(
            pattern_id=pattern_key,
            attack_type=attacks[0].attack_type,
            frequency=len(attacks),
            avg_profit_usd=avg_profit,
            success_rate=success_rate,
            protocols=common_protocols,
            token_patterns=token_categories,
            optimal_conditions=optimal_conditions,
            steps_template=steps_template,
            risk_level=risk_level,
            adaptable_to_solana=adaptable
        )
        
        return pattern
    
    def _categorize_tokens(self, tokens: List[str]) -> List[str]:
        """Categorize tokens into types"""
        categories = set()
        
        for token in tokens:
            for category, token_list in self.token_categories.items():
                if token in token_list:
                    categories.add(category)
        
        return list(categories)
    
    def _extract_step_template(self, attacks: List[FlashloanAttack]) -> List[str]:
        """Extract common step sequence"""
        # Find most common step sequence
        sequences = [tuple(step['action'] for step in a.steps) for a in attacks]
        
        from collections import Counter
        most_common = Counter(sequences).most_common(1)
        
        if most_common:
            return list(most_common[0][0])
        
        return []
    
    def _check_solana_adaptability(self, protocols: List[str]) -> bool:
        """Check if pattern can be adapted to Solana"""
        # Check if we have Solana equivalents for the protocols
        adaptable_count = sum(1 for p in protocols if p in self.protocol_mapping)
        
        # If we can adapt >70% of protocols, consider it adaptable
        return (adaptable_count / len(protocols)) > 0.7 if protocols else False
    
    def _calculate_risk_level(self, attacks: List[FlashloanAttack]) -> float:
        """Calculate risk level of pattern (0-1)"""
        # Risk factors:
        # 1. Complexity (more steps = more risk)
        # 2. Gas cost variance (high variance = unpredictable)
        # 3. Profit variance (unstable = risky)
        
        complexities = [a.complexity_score for a in attacks]
        gas_costs = [a.gas_cost_usd for a in attacks]
        profits = [a.profit_usd for a in attacks]
        
        # Normalize to 0-1
        complexity_risk = np.mean(complexities) / 10  # Max 10 steps assumed
        gas_variance_risk = np.std(gas_costs) / np.mean(gas_costs) if np.mean(gas_costs) > 0 else 0
        profit_variance_risk = np.std(profits) / np.mean(profits) if np.mean(profits) > 0 else 0
        
        total_risk = (complexity_risk * 0.3 + gas_variance_risk * 0.3 + profit_variance_risk * 0.4)
        
        return min(1.0, total_risk)
    
    def adapt_pattern_to_solana(self, pattern: StrategyPattern) -> Dict:
        """
        Adapt an Ethereum pattern to Solana
        
        Returns:
            Adapted strategy configuration
        """
        cprint(f"\n🔄 Adapting pattern '{pattern.pattern_id}' to Solana...", "yellow")
        
        # Map protocols
        solana_protocols = []
        for protocol in pattern.protocols:
            if protocol in self.protocol_mapping:
                solana_protocols.append(self.protocol_mapping[protocol])
        
        # Adapt step template
        solana_steps = []
        for step in pattern.steps_template:
            if step == 'flashloan':
                solana_steps.append('borrow_flashloan_solend')
            elif step == 'swap':
                solana_steps.append('swap_jupiter')
            elif step == 'liquidate':
                solana_steps.append('liquidate_position')
            elif step == 'repay':
                solana_steps.append('repay_flashloan_solend')
        
        adapted_strategy = {
            'original_pattern': pattern.pattern_id,
            'attack_type': pattern.attack_type,
            'solana_protocols': solana_protocols,
            'steps': solana_steps,
            'optimal_conditions': pattern.optimal_conditions,
            'expected_profit': pattern.avg_profit_usd,
            'risk_level': pattern.risk_level,
            'min_profit_threshold': pattern.avg_profit_usd * 0.5,  # Target 50% of avg
            'recommended_confidence': 95.0 if pattern.risk_level < 0.3 else 98.0
        }
        
        cprint(f"✅ Pattern adapted to Solana", "green")
        cprint(f"   Protocols: {', '.join(solana_protocols)}", "cyan")
        cprint(f"   Steps: {len(solana_steps)}", "cyan")
        cprint(f"   Expected Profit: ${adapted_strategy['expected_profit']:,.2f}", "green")
        
        return adapted_strategy
    
    def optimize_agent_genetics(self, pattern: StrategyPattern) -> Dict:
        """
        Generate optimal agent genetics based on learned pattern
        
        Returns:
            Genetic configuration for baby agents
        """
        genetics = {
            'min_profit_threshold': pattern.avg_profit_usd * 0.3 / 100,  # Convert to %
            'max_trade_size_usd': pattern.optimal_conditions.get('min_flashloan_amount', 10000),
            'risk_tolerance': 1.0 - pattern.risk_level,
            'dex_preference': self._get_solana_dex_preference(pattern.protocols),
            'aggression': 0.8 if pattern.success_rate > 0.9 else 0.5,
            'adaptability': 0.6,
            'strategy_source': f'eigenphi_pattern_{pattern.pattern_id}'
        }
        
        return genetics
    
    def _get_solana_dex_preference(self, protocols: List[str]) -> List[str]:
        """Get Solana DEX preferences from protocol list"""
        dexs = set()
        
        for protocol in protocols:
            if protocol in self.protocol_mapping:
                solana_equiv = self.protocol_mapping[protocol]
                if solana_equiv in ['raydium', 'orca', 'jupiter', 'meteora']:
                    dexs.add(solana_equiv)
        
        if not dexs:
            dexs = {'raydium', 'orca', 'jupiter'}  # Defaults
        
        return list(dexs)
    
    def generate_learning_report(self) -> Dict:
        """Generate comprehensive learning report"""
        report = {
            'summary': {
                'total_attacks_analyzed': self.total_attacks_analyzed,
                'total_profit_learned': self.total_profit_learned,
                'patterns_discovered': self.patterns_discovered,
                'adaptable_patterns': sum(1 for p in self.patterns.values() if p.adaptable_to_solana)
            },
            'top_patterns': [],
            'recommendations': []
        }
        
        # Top patterns by profit
        sorted_patterns = sorted(
            self.patterns.values(),
            key=lambda p: p.avg_profit_usd,
            reverse=True
        )
        
        for pattern in sorted_patterns[:5]:
            report['top_patterns'].append({
                'id': pattern.pattern_id,
                'type': pattern.attack_type,
                'avg_profit': pattern.avg_profit_usd,
                'frequency': pattern.frequency,
                'adaptable': pattern.adaptable_to_solana,
                'risk_level': pattern.risk_level
            })
        
        # Generate recommendations
        if sorted_patterns:
            best_pattern = sorted_patterns[0]
            report['recommendations'].append(
                f"Focus on '{best_pattern.attack_type}' strategies (${best_pattern.avg_profit_usd:,.2f} avg profit)"
            )
            
            if best_pattern.adaptable_to_solana:
                report['recommendations'].append(
                    f"Adapt pattern '{best_pattern.pattern_id}' to Solana immediately"
                )
        
        return report
    
    def continuous_learning_loop(self, interval_hours: int = 1):
        """
        Continuous learning loop that runs in background
        
        Args:
            interval_hours: How often to fetch new data
        """
        cprint(f"\n♾️ Starting continuous learning loop (every {interval_hours}h)", "magenta", attrs=['bold'])
        
        iteration = 0
        
        while True:
            iteration += 1
            
            cprint(f"\n{'='*60}", "magenta")
            cprint(f"📚 Learning Iteration #{iteration}", "magenta", attrs=['bold'])
            cprint(f"{'='*60}", "magenta")
            
            try:
                # Fetch new attacks
                attacks = self.fetch_recent_attacks(hours=interval_hours)
                
                if attacks:
                    # Analyze and extract patterns
                    new_patterns = self.analyze_and_extract_patterns(attacks)
                    
                    # Adapt profitable patterns
                    for pattern in new_patterns:
                        if pattern.adaptable_to_solana and pattern.avg_profit_usd >= 100:
                            adapted = self.adapt_pattern_to_solana(pattern)
                            
                            # This could update agent genetics
                            genetics = self.optimize_agent_genetics(pattern)
                            
                            cprint(f"\n💡 New strategy configuration generated:", "green")
                            cprint(f"   Min Profit Threshold: {genetics['min_profit_threshold']:.2f}%", "cyan")
                            cprint(f"   Max Trade Size: ${genetics['max_trade_size_usd']:,.0f}", "cyan")
                
                # Generate report
                report = self.generate_learning_report()
                
                cprint(f"\n📊 Learning Report:", "magenta")
                cprint(f"   Total Attacks: {report['summary']['total_attacks_analyzed']}", "cyan")
                cprint(f"   Total Profit: ${report['summary']['total_profit_learned']:,.2f}", "green")
                cprint(f"   Patterns: {report['summary']['patterns_discovered']}", "cyan")
                cprint(f"   Adaptable: {report['summary']['adaptable_patterns']}", "green")
                
            except Exception as e:
                cprint(f"❌ Learning error: {str(e)}", "red")
            
            # Wait for next iteration
            cprint(f"\n💤 Sleeping {interval_hours}h until next learning cycle...", "yellow")
            time.sleep(interval_hours * 3600)
    
    def export_learned_strategies(self, filepath: str):
        """Export learned strategies to JSON"""
        data = {
            'timestamp': time.time(),
            'statistics': {
                'total_attacks_analyzed': self.total_attacks_analyzed,
                'total_profit_learned': self.total_profit_learned,
                'patterns_discovered': self.patterns_discovered
            },
            'patterns': {k: v.to_dict() for k, v in self.patterns.items()},
            'adaptations': [
                self.adapt_pattern_to_solana(p)
                for p in self.patterns.values()
                if p.adaptable_to_solana
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        cprint(f"\n💾 Learned strategies exported to {filepath}", "green")
