"""
🌙 Moon Dev's Dynamic Profit Maximizer
Scale position size based on opportunity (100 - 10M+)
Built with love by Moon Dev 🚀
"""

import os
import sys
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from termcolor import cprint
import numpy as np

@dataclass
class ProfitTier:
    """Profit tier configuration"""
    name: str
    min_profit: float
    max_profit: float
    target_size_multiplier: float
    risk_tolerance: float
    max_slippage: float
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'min_profit': self.min_profit,
            'max_profit': self.max_profit,
            'size_multiplier': self.target_size_multiplier,
            'risk_tolerance': self.risk_tolerance,
            'max_slippage': self.max_slippage
        }


class DynamicProfitMaximizer:
    """
    Dynamically scale trade size based on profit potential
    
    Profit Tiers:
    - Small: $100-1K → Standard size
    - Medium: $1K-10K → 2-5x size
    - Large: $10K-100K → 5-10x size
    - Huge: $100K-1M → 10-50x size
    - Massive: $1M-10M → 50-100x size
    - Mega: $10M+ → Maximum size (up to capital limits)
    
    Strategy:
    - Larger opportunities = larger positions
    - Maintain same risk-adjusted returns
    - Account for increased slippage at scale
    """
    
    def __init__(self, max_capital_usd: float = 1000000):
        self.max_capital = max_capital_usd
        
        # Define profit tiers
        self.tiers = {
            'small': ProfitTier(
                name='SMALL',
                min_profit=100,
                max_profit=1000,
                target_size_multiplier=1.0,
                risk_tolerance=0.3,
                max_slippage=0.02  # 2%
            ),
            'medium': ProfitTier(
                name='MEDIUM',
                min_profit=1000,
                max_profit=10000,
                target_size_multiplier=3.0,
                risk_tolerance=0.4,
                max_slippage=0.03  # 3%
            ),
            'large': ProfitTier(
                name='LARGE',
                min_profit=10000,
                max_profit=100000,
                target_size_multiplier=7.0,
                risk_tolerance=0.5,
                max_slippage=0.05  # 5%
            ),
            'huge': ProfitTier(
                name='HUGE',
                min_profit=100000,
                max_profit=1000000,
                target_size_multiplier=25.0,
                risk_tolerance=0.6,
                max_slippage=0.08  # 8%
            ),
            'massive': ProfitTier(
                name='MASSIVE',
                min_profit=1000000,
                max_profit=10000000,
                target_size_multiplier=75.0,
                risk_tolerance=0.7,
                max_slippage=0.12  # 12%
            ),
            'mega': ProfitTier(
                name='MEGA',
                min_profit=10000000,
                max_profit=float('inf'),
                target_size_multiplier=100.0,
                risk_tolerance=0.8,
                max_slippage=0.15  # 15%
            )
        }
        
        cprint("\n💎 Dynamic Profit Maximizer Initialized", "magenta", attrs=['bold'])
        cprint(f"   Max Capital: ${self.max_capital:,.0f}", "cyan")
        cprint(f"   Profit Tiers: {len(self.tiers)}", "cyan")
        
        # Print tiers
        for tier_name, tier in self.tiers.items():
            cprint(f"   {tier.name}: ${tier.min_profit:,.0f}-${tier.max_profit:,.0f} → {tier.target_size_multiplier}x size", "yellow")
    
    def calculate_optimal_position(self, opportunity, base_size: float = 10000) -> Dict:
        """
        Calculate optimal position size based on profit potential
        
        Args:
            opportunity: Arbitrage opportunity
            base_size: Base trade size in USD
            
        Returns:
            Optimal position parameters
        """
        expected_profit = opportunity.net_profit_usd
        
        # Determine tier
        tier = self._get_profit_tier(expected_profit)
        
        cprint(f"\n💰 PROFIT MAXIMIZATION ANALYSIS", "magenta", attrs=['bold'])
        cprint(f"   Expected Profit: ${expected_profit:,.2f}", "green", attrs=['bold'])
        cprint(f"   Tier: {tier.name}", "yellow", attrs=['bold'])
        
        # Calculate optimal size
        optimal_size = self._calculate_size_for_tier(
            base_size, tier, opportunity, expected_profit
        )
        
        # Calculate expected total profit
        size_multiplier = optimal_size / base_size
        total_expected_profit = expected_profit * size_multiplier
        
        # Account for slippage at larger sizes
        slippage_impact = self._estimate_slippage_impact(
            optimal_size, opportunity.liquidity_available
        )
        
        # Adjusted profit
        adjusted_profit = total_expected_profit * (1 - slippage_impact)
        
        # Risk assessment
        risk_assessment = self._assess_scaled_risk(
            optimal_size, tier, opportunity
        )
        
        result = {
            'tier': tier.name,
            'base_size': base_size,
            'optimal_size': optimal_size,
            'size_multiplier': size_multiplier,
            'expected_profit_base': expected_profit,
            'expected_profit_scaled': total_expected_profit,
            'slippage_impact_pct': slippage_impact * 100,
            'adjusted_profit': adjusted_profit,
            'risk_score': risk_assessment['risk_score'],
            'recommended': risk_assessment['recommended'],
            'warnings': risk_assessment['warnings']
        }
        
        self._print_maximization_results(result)
        
        return result
    
    def _get_profit_tier(self, expected_profit: float) -> ProfitTier:
        """Determine which profit tier this opportunity belongs to"""
        for tier in self.tiers.values():
            if tier.min_profit <= expected_profit < tier.max_profit:
                return tier
        
        # Default to mega for anything above
        return self.tiers['mega']
    
    def _calculate_size_for_tier(self, base_size: float, tier: ProfitTier,
                                 opportunity, expected_profit: float) -> float:
        """Calculate optimal size for this tier"""
        # Start with tier multiplier
        target_size = base_size * tier.target_size_multiplier
        
        # Adjust for liquidity constraints
        max_liquidity_size = opportunity.liquidity_available * 0.4  # Max 40% of liquidity
        
        # Adjust for capital constraints
        max_capital_size = self.max_capital * 0.3  # Max 30% of capital per trade
        
        # Take minimum of constraints
        optimal_size = min(target_size, max_liquidity_size, max_capital_size)
        
        # Ensure minimum size
        optimal_size = max(optimal_size, base_size)
        
        return optimal_size
    
    def _estimate_slippage_impact(self, trade_size: float, liquidity: float) -> float:
        """
        Estimate slippage impact for larger trade sizes
        
        Uses square root market impact model
        """
        if liquidity <= 0:
            return 0.1  # 10% default high slippage
        
        # Market impact = k * sqrt(trade_size / liquidity)
        k = 0.1  # Impact coefficient
        
        liquidity_usage = trade_size / liquidity
        impact = k * np.sqrt(liquidity_usage)
        
        return min(impact, 0.2)  # Cap at 20%
    
    def _assess_scaled_risk(self, trade_size: float, tier: ProfitTier,
                           opportunity) -> Dict:
        """Assess risk of scaled position"""
        warnings = []
        
        # Check liquidity usage
        liquidity_usage = trade_size / opportunity.liquidity_available
        
        if liquidity_usage > 0.5:
            warnings.append(f"High liquidity usage: {liquidity_usage:.1%}")
        
        # Check capital usage
        capital_usage = trade_size / self.max_capital
        
        if capital_usage > 0.5:
            warnings.append(f"High capital usage: {capital_usage:.1%}")
        
        # Calculate overall risk score
        risk_factors = [
            liquidity_usage,
            capital_usage,
            tier.risk_tolerance
        ]
        
        risk_score = np.mean(risk_factors)
        
        # Recommendation
        recommended = risk_score < 0.7 and len(warnings) < 2
        
        return {
            'risk_score': risk_score,
            'recommended': recommended,
            'warnings': warnings
        }
    
    def _print_maximization_results(self, result: Dict):
        """Print maximization analysis results"""
        cprint(f"\n   {'='*60}", "magenta")
        cprint(f"   💎 MAXIMIZATION RESULTS", "magenta", attrs=['bold'])
        cprint(f"   {'='*60}", "magenta")
        
        cprint(f"   Base Size: ${result['base_size']:,.0f}", "white")
        cprint(f"   Optimal Size: ${result['optimal_size']:,.0f} ({result['size_multiplier']:.1f}x)", "cyan", attrs=['bold'])
        cprint(f"   Expected Profit (base): ${result['expected_profit_base']:,.2f}", "yellow")
        cprint(f"   Expected Profit (scaled): ${result['expected_profit_scaled']:,.2f}", "green", attrs=['bold'])
        cprint(f"   Slippage Impact: {result['slippage_impact_pct']:.2f}%", "yellow")
        cprint(f"   Adjusted Profit: ${result['adjusted_profit']:,.2f}", "green", attrs=['bold'])
        cprint(f"   Risk Score: {result['risk_score']:.2f}/1.0", "yellow" if result['risk_score'] < 0.7 else "red")
        
        if result['recommended']:
            cprint(f"   ✅ RECOMMENDED FOR EXECUTION", "green", attrs=['bold'])
        else:
            cprint(f"   ⚠️ REVIEW WARNINGS BEFORE EXECUTION", "yellow", attrs=['bold'])
        
        if result['warnings']:
            cprint(f"\n   ⚠️ Warnings:", "yellow")
            for warning in result['warnings']:
                cprint(f"      - {warning}", "yellow")
        
        cprint(f"   {'='*60}\n", "magenta")
    
    def should_execute_max_size(self, opportunity) -> bool:
        """
        Determine if we should go for maximum size
        
        Criteria:
        - Expected profit > $100K
        - High confidence (>95%)
        - Sufficient liquidity
        - Low risk score
        """
        if opportunity.net_profit_usd < 100000:
            return False
        
        # Would check additional criteria
        return True
    
    def calculate_max_safe_size(self, opportunity) -> float:
        """Calculate maximum safe position size"""
        # Based on liquidity
        liquidity_limit = opportunity.liquidity_available * 0.5
        
        # Based on capital
        capital_limit = self.max_capital * 0.5
        
        # Based on slippage tolerance
        slippage_limit = self._calculate_size_for_slippage_target(
            opportunity, target_slippage=0.05  # 5% max
        )
        
        return min(liquidity_limit, capital_limit, slippage_limit)
    
    def _calculate_size_for_slippage_target(self, opportunity, target_slippage: float) -> float:
        """Calculate trade size that keeps slippage under target"""
        # Inverse of slippage formula
        # impact = k * sqrt(size / liquidity)
        # size = (impact/k)^2 * liquidity
        
        k = 0.1
        liquidity = opportunity.liquidity_available
        
        max_size = ((target_slippage / k) ** 2) * liquidity
        
        return max_size
