"""
🌙 Moon Dev's Flashloan Baby Agent
Self-evolving arbitrage agents with survival mechanics
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from termcolor import cprint
from datetime import datetime

@dataclass
class AgentGenetics:
    """Genetic traits that determine agent behavior"""
    min_profit_threshold: float = 0.5  # Minimum profit % to attempt
    max_trade_size_usd: float = 10000  # Maximum trade size
    risk_tolerance: float = 0.5  # 0-1 scale
    dex_preference: List[str] = field(default_factory=lambda: ['raydium', 'orca', 'jupiter'])
    scan_interval_seconds: float = 30  # How often to scan
    aggression: float = 0.5  # How quickly to execute (0-1)
    adaptability: float = 0.5  # How much to mutate on evolution (0-1)
    
    def mutate(self, success_rate: float):
        """
        Evolve genetics based on performance
        
        Args:
            success_rate: Ratio of successful trades (0-1)
        """
        mutation_strength = self.adaptability * 0.2  # Max 20% change
        
        if success_rate > 0.7:
            # Successful agent - small optimizations
            self.min_profit_threshold *= random.uniform(0.95, 1.05)
            self.max_trade_size_usd *= random.uniform(1.0, 1.1)
            self.aggression *= random.uniform(1.0, 1.1)
        elif success_rate > 0.3:
            # Moderate success - medium mutations
            self.min_profit_threshold *= random.uniform(0.9, 1.1)
            self.max_trade_size_usd *= random.uniform(0.9, 1.1)
            self.scan_interval_seconds *= random.uniform(0.8, 1.2)
        else:
            # Poor performance - aggressive mutations
            self.min_profit_threshold *= random.uniform(0.7, 1.3)
            self.max_trade_size_usd *= random.uniform(0.7, 1.3)
            self.risk_tolerance *= random.uniform(0.5, 1.5)
            self.aggression *= random.uniform(0.5, 1.5)
            
            # Try different DEXs (DEX-ONLY, no CEX)
            solana_dexs_only = ['raydium', 'orca', 'jupiter', 'meteora']
            self.dex_preference = random.sample(solana_dexs_only, k=random.randint(2, 4))
        
        # Keep values in reasonable ranges
        self.min_profit_threshold = max(0.1, min(5.0, self.min_profit_threshold))
        self.max_trade_size_usd = max(100, min(100000, self.max_trade_size_usd))
        self.risk_tolerance = max(0.1, min(1.0, self.risk_tolerance))
        self.aggression = max(0.1, min(1.0, self.aggression))
        self.adaptability = max(0.1, min(1.0, self.adaptability))
        self.scan_interval_seconds = max(5, min(120, self.scan_interval_seconds))
    
    def to_dict(self) -> Dict:
        return {
            'min_profit_threshold': self.min_profit_threshold,
            'max_trade_size_usd': self.max_trade_size_usd,
            'risk_tolerance': self.risk_tolerance,
            'dex_preference': self.dex_preference,
            'scan_interval_seconds': self.scan_interval_seconds,
            'aggression': self.aggression,
            'adaptability': self.adaptability
        }


@dataclass
class TradeAttempt:
    """Record of a single trade attempt"""
    timestamp: float
    opportunity_token: str
    route: List[str]
    expected_profit: float
    actual_profit: float
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'token': self.opportunity_token,
            'route': self.route,
            'expected_profit': self.expected_profit,
            'actual_profit': self.actual_profit,
            'success': self.success,
            'error': self.error
        }


class FlashloanBabyAgent:
    """
    Self-evolving flashloan arbitrage agent
    - Dies after 3 failed attempts
    - Evolves and survives if profitable
    """
    
    # Class-level counter for unique IDs
    _next_id = 1
    
    def __init__(self, flashloan_core, tokens: List[str], genetics: Optional[AgentGenetics] = None):
        """
        Initialize a baby agent
        
        Args:
            flashloan_core: FlashloanCore instance for execution
            tokens: List of tokens to scan
            genetics: Optional genetic traits (random if None)
        """
        self.id = f"AGENT_{FlashloanBabyAgent._next_id:04d}"
        FlashloanBabyAgent._next_id += 1
        
        self.core = flashloan_core
        self.tokens = tokens
        self.genetics = genetics or self._create_random_genetics()
        
        # Lifecycle tracking
        self.birth_time = time.time()
        self.is_alive = True
        self.generation = 1
        self.parent_id = None
        
        # Performance tracking
        self.attempts = []
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.total_profit_usd = 0.0
        self.total_loss_usd = 0.0
        
        # Death conditions
        self.max_failed_attempts = 3
        self.consecutive_failures = 0
        
        cprint(f"\n👶 Baby Agent Born: {self.id}", "green", attrs=['bold'])
        cprint(f"   Generation: {self.generation}", "cyan")
        cprint(f"   Min Profit: {self.genetics.min_profit_threshold:.2f}%", "cyan")
        cprint(f"   Max Trade: ${self.genetics.max_trade_size_usd:,.0f}", "cyan")
        cprint(f"   DEX Preference: {', '.join(self.genetics.dex_preference)}", "cyan")
    
    def _create_random_genetics(self) -> AgentGenetics:
        """
        Create random genetic traits for diversity
        
        DEX-ONLY: Only Solana DEXs are allowed in preferences
        """
        # ONLY Solana DEXs - NO CEX allowed
        solana_dexs = ['raydium', 'orca', 'jupiter', 'meteora']
        
        return AgentGenetics(
            min_profit_threshold=random.uniform(0.3, 2.0),
            max_trade_size_usd=random.uniform(1000, 50000),
            risk_tolerance=random.uniform(0.2, 0.8),
            dex_preference=random.sample(solana_dexs, k=random.randint(2, 4)),
            scan_interval_seconds=random.uniform(15, 60),
            aggression=random.uniform(0.3, 0.9),
            adaptability=random.uniform(0.3, 0.8)
        )
    
    def scan_and_execute(self) -> Dict:
        """
        Scan for opportunities and attempt execution
        
        Returns:
            Execution result
        """
        if not self.is_alive:
            return {'error': 'Agent is dead', 'agent_id': self.id}
        
        cprint(f"\n🔍 {self.id} scanning for opportunities...", "cyan")
        
        # Scan with agent's genetic preferences
        opportunities = self.core.scan_arbitrage_opportunities(
            self.tokens,
            min_profit_percent=self.genetics.min_profit_threshold
        )
        
        if not opportunities:
            cprint(f"   No profitable opportunities found", "yellow")
            return {'success': False, 'message': 'No opportunities'}
        
        # Filter by agent preferences
        filtered_opps = self._filter_opportunities(opportunities)
        
        if not filtered_opps:
            cprint(f"   No opportunities match agent preferences", "yellow")
            return {'success': False, 'message': 'No matching opportunities'}
        
        # Execute best opportunity
        best_opp = filtered_opps[0]
        
        cprint(f"   Found {len(filtered_opps)} opportunities", "green")
        cprint(f"   Best: ${best_opp.net_profit_usd:.4f} via {' → '.join(best_opp.route)}", "green")
        
        result = self._execute_opportunity(best_opp)
        
        # Update fitness based on result
        self._update_fitness(result)
        
        return result
    
    def _filter_opportunities(self, opportunities):
        """Filter opportunities based on genetic preferences"""
        filtered = []
        
        for opp in opportunities:
            # Check if DEXs match preferences
            if (opp.buy_dex in self.genetics.dex_preference and 
                opp.sell_dex in self.genetics.dex_preference):
                
                # Check trade size limits
                if opp.optimal_amount * opp.buy_price <= self.genetics.max_trade_size_usd:
                    
                    # Check risk tolerance
                    risk_score = self._calculate_risk(opp)
                    if risk_score <= self.genetics.risk_tolerance:
                        filtered.append(opp)
        
        return filtered
    
    def _calculate_risk(self, opportunity) -> float:
        """Calculate risk score for opportunity (0-1)"""
        # Simple risk model based on:
        # - Liquidity (lower = higher risk)
        # - Profit margin (lower = higher risk)
        # - Price impact
        
        liquidity_risk = 1.0 - min(opportunity.liquidity_available / 100000, 1.0)
        profit_risk = 1.0 - min(opportunity.profit_percent / 5.0, 1.0)
        
        total_risk = (liquidity_risk * 0.6 + profit_risk * 0.4)
        return total_risk
    
    def _execute_opportunity(self, opportunity) -> Dict:
        """Execute a flashloan arbitrage opportunity"""
        self.total_attempts += 1
        
        cprint(f"\n⚡ {self.id} executing trade #{self.total_attempts}", "yellow")
        
        try:
            # Execute via core
            result = self.core.execute_flashloan_arbitrage(opportunity)
            
            # Record attempt
            attempt = TradeAttempt(
                timestamp=time.time(),
                opportunity_token=opportunity.token_address,
                route=opportunity.route,
                expected_profit=opportunity.net_profit_usd,
                actual_profit=result.get('profit', 0) if result.get('success') else 0,
                success=result.get('success', False),
                error=result.get('error')
            )
            
            self.attempts.append(attempt)
            
            return {
                'success': attempt.success,
                'agent_id': self.id,
                'attempt_number': self.total_attempts,
                'profit': attempt.actual_profit,
                'opportunity': opportunity.to_dict(),
                'result': result
            }
            
        except Exception as e:
            cprint(f"❌ Execution error: {str(e)}", "red")
            
            attempt = TradeAttempt(
                timestamp=time.time(),
                opportunity_token=opportunity.token_address,
                route=opportunity.route,
                expected_profit=opportunity.net_profit_usd,
                actual_profit=0,
                success=False,
                error=str(e)
            )
            
            self.attempts.append(attempt)
            
            return {
                'success': False,
                'agent_id': self.id,
                'error': str(e)
            }
    
    def _update_fitness(self, result: Dict):
        """
        Update agent fitness and check survival
        
        This is where the life/death decision happens
        """
        if result.get('success'):
            profit = result.get('profit', 0)
            
            if profit > 0:
                # PROFITABLE TRADE - AGENT SURVIVES!
                self.successful_attempts += 1
                self.total_profit_usd += profit
                self.consecutive_failures = 0
                
                cprint(f"\n✅ {self.id} PROFITABLE! +${profit:.4f}", "green", attrs=['bold'])
                cprint(f"   Total Profit: ${self.total_profit_usd:.4f}", "green")
                cprint(f"   Success Rate: {self.get_success_rate():.1f}%", "green")
                
                # Evolve if performance is good
                if self.successful_attempts % 3 == 0:
                    self.evolve()
            else:
                # Trade succeeded but no profit
                self.failed_attempts += 1
                self.consecutive_failures += 1
                self.total_loss_usd += abs(profit)
                
                cprint(f"\n⚠️ {self.id} trade complete but no profit", "yellow")
        else:
            # FAILED TRADE
            self.failed_attempts += 1
            self.consecutive_failures += 1
            
            cprint(f"\n❌ {self.id} FAILED (attempt {self.total_attempts})", "red")
            cprint(f"   Consecutive Failures: {self.consecutive_failures}/{self.max_failed_attempts}", "red")
        
        # CHECK DEATH CONDITION
        if self.consecutive_failures >= self.max_failed_attempts:
            self.die()
    
    def die(self):
        """Agent dies after too many failures"""
        self.is_alive = False
        lifetime = time.time() - self.birth_time
        
        cprint(f"\n💀 {self.id} HAS DIED", "red", attrs=['bold'])
        cprint(f"   Lifetime: {lifetime:.0f} seconds", "red")
        cprint(f"   Total Attempts: {self.total_attempts}", "red")
        cprint(f"   Successful: {self.successful_attempts}", "red")
        cprint(f"   Failed: {self.failed_attempts}", "red")
        cprint(f"   Total P/L: ${self.total_profit_usd - self.total_loss_usd:.4f}", "red")
        cprint(f"   Cause: {self.consecutive_failures} consecutive failures", "red")
    
    def evolve(self):
        """Agent evolves based on performance"""
        old_genetics = self.genetics.to_dict()
        
        success_rate = self.get_success_rate() / 100.0
        self.genetics.mutate(success_rate)
        self.generation += 1
        
        cprint(f"\n🧬 {self.id} EVOLVED to Generation {self.generation}!", "magenta", attrs=['bold'])
        cprint(f"   Min Profit: {old_genetics['min_profit_threshold']:.2f}% → {self.genetics.min_profit_threshold:.2f}%", "magenta")
        cprint(f"   Max Trade: ${old_genetics['max_trade_size_usd']:,.0f} → ${self.genetics.max_trade_size_usd:,.0f}", "magenta")
        cprint(f"   Aggression: {old_genetics['aggression']:.2f} → {self.genetics.aggression:.2f}", "magenta")
    
    def spawn_child(self) -> 'FlashloanBabyAgent':
        """
        Create a child agent with mutated genetics
        Only successful agents can reproduce
        """
        if self.total_profit_usd <= 0:
            raise ValueError("Only profitable agents can spawn children")
        
        # Create child with mutated genetics
        child_genetics = AgentGenetics(**self.genetics.to_dict())
        child_genetics.mutate(self.get_success_rate() / 100.0)
        
        child = FlashloanBabyAgent(self.core, self.tokens, child_genetics)
        child.parent_id = self.id
        child.generation = self.generation + 1
        
        cprint(f"\n🍼 {self.id} spawned child {child.id}", "cyan", attrs=['bold'])
        cprint(f"   Child Generation: {child.generation}", "cyan")
        
        return child
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return {
            'id': self.id,
            'is_alive': self.is_alive,
            'generation': self.generation,
            'parent_id': self.parent_id,
            'age_seconds': time.time() - self.birth_time,
            'total_attempts': self.total_attempts,
            'successful_attempts': self.successful_attempts,
            'failed_attempts': self.failed_attempts,
            'consecutive_failures': self.consecutive_failures,
            'success_rate': self.get_success_rate(),
            'total_profit': self.total_profit_usd,
            'total_loss': self.total_loss_usd,
            'net_profit': self.total_profit_usd - self.total_loss_usd,
            'genetics': self.genetics.to_dict(),
            'attempts': [a.to_dict() for a in self.attempts[-10:]]  # Last 10 attempts
        }
    
    def to_dict(self) -> Dict:
        """Convert agent to dictionary"""
        return self.get_stats()
