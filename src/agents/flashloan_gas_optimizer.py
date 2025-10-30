"""
🌙 Moon Dev's Gas Fee Optimizer
Dynamic gas fee optimization targeting $100+ net profits
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from termcolor import cprint
from collections import deque
import requests

@dataclass
class GasFeeMetrics:
    """Real-time gas fee metrics"""
    timestamp: float
    base_fee_lamports: int
    priority_fee_lamports: int
    compute_units: int
    total_cost_sol: float
    total_cost_usd: float
    network_congestion: float  # 0-1 scale
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'base_fee_lamports': self.base_fee_lamports,
            'priority_fee_lamports': self.priority_fee_lamports,
            'compute_units': self.compute_units,
            'total_cost_sol': self.total_cost_sol,
            'total_cost_usd': self.total_cost_usd,
            'network_congestion': self.network_congestion
        }


@dataclass
class OptimizedTradeParams:
    """Optimized trade parameters based on gas analysis"""
    optimal_trade_size_usd: float
    expected_gas_cost_usd: float
    expected_net_profit_usd: float
    recommended_priority_fee: int
    compute_units_required: int
    profit_margin_pct: float
    meets_target: bool  # Does it meet $100 target?
    
    def to_dict(self) -> Dict:
        return {
            'optimal_trade_size_usd': self.optimal_trade_size_usd,
            'expected_gas_cost_usd': self.expected_gas_cost_usd,
            'expected_net_profit_usd': self.expected_net_profit_usd,
            'recommended_priority_fee': self.recommended_priority_fee,
            'compute_units_required': self.compute_units_required,
            'profit_margin_pct': self.profit_margin_pct,
            'meets_target': self.meets_target
        }


class GasOptimizer:
    """
    Advanced gas fee optimizer targeting $100+ net profits
    
    Features:
    1. Real-time gas price monitoring
    2. Dynamic trade size adjustment
    3. Compute unit optimization
    4. Priority fee bidding
    5. Network congestion analysis
    6. $100+ profit targeting
    """
    
    def __init__(self, sol_price_usd: float = 100.0, target_net_profit: float = 100.0):
        """
        Initialize gas optimizer
        
        Args:
            sol_price_usd: Current SOL price in USD
            target_net_profit: Target net profit in USD (default $100)
        """
        self.sol_price_usd = sol_price_usd
        self.target_net_profit = target_net_profit
        
        # Gas fee history for analysis
        self.gas_history: deque = deque(maxlen=100)
        
        # Compute unit estimates for different operations
        self.compute_units = {
            'flashloan_borrow': 100000,
            'dex_swap': 150000,
            'flashloan_repay': 80000,
            'token_transfer': 50000,
            'account_creation': 200000
        }
        
        # Priority fee strategies
        self.priority_strategies = {
            'low': 10000,      # Low priority (0.00001 SOL)
            'medium': 100000,  # Medium priority (0.0001 SOL)
            'high': 500000,    # High priority (0.0005 SOL)
            'ultra': 1000000   # Ultra priority (0.001 SOL)
        }
        
        # Dynamic adjustment parameters
        self.min_profit_to_gas_ratio = 20  # Profit should be 20x gas cost
        self.max_gas_to_profit_pct = 10    # Gas can't be >10% of profit
        
        # Network congestion thresholds
        self.congestion_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        
        cprint("\n⚡ Gas Fee Optimizer Initialized", "cyan", attrs=['bold'])
        cprint(f"   Target Net Profit: ${self.target_net_profit:.2f}", "green", attrs=['bold'])
        cprint(f"   SOL Price: ${self.sol_price_usd:.2f}", "cyan")
        cprint(f"   Min Profit/Gas Ratio: {self.min_profit_to_gas_ratio}x", "cyan")
        cprint(f"   Max Gas/Profit: {self.max_gas_to_profit_pct}%", "cyan")
    
    def get_current_gas_metrics(self) -> GasFeeMetrics:
        """
        Get current gas fee metrics from Solana network
        
        Fetches:
        - Recent priority fees
        - Network congestion
        - Compute unit costs
        """
        cprint("\n📊 Fetching current gas metrics...", "cyan")
        
        try:
            # Get recent priority fees from Helius or similar
            # This would use actual RPC calls in production
            priority_fee = self._fetch_priority_fees()
            
            # Estimate base fee (5000 lamports per signature on Solana)
            base_fee = 5000
            
            # Calculate total compute units for flashloan arb
            total_compute = (
                self.compute_units['flashloan_borrow'] +
                self.compute_units['dex_swap'] * 2 +  # Buy + Sell
                self.compute_units['flashloan_repay']
            )
            
            # Calculate total cost
            total_lamports = base_fee + priority_fee
            total_sol = total_lamports / 1e9
            total_usd = total_sol * self.sol_price_usd
            
            # Estimate network congestion
            congestion = self._estimate_network_congestion()
            
            metrics = GasFeeMetrics(
                timestamp=time.time(),
                base_fee_lamports=base_fee,
                priority_fee_lamports=priority_fee,
                compute_units=total_compute,
                total_cost_sol=total_sol,
                total_cost_usd=total_usd,
                network_congestion=congestion
            )
            
            # Store in history
            self.gas_history.append(metrics)
            
            cprint(f"   Base Fee: {base_fee:,} lamports", "white")
            cprint(f"   Priority Fee: {priority_fee:,} lamports", "yellow")
            cprint(f"   Total Compute: {total_compute:,} units", "white")
            cprint(f"   Total Cost: {total_sol:.8f} SOL (${total_usd:.6f})", "yellow")
            cprint(f"   Network Congestion: {congestion:.1%}", 
                   "red" if congestion > 0.8 else "yellow" if congestion > 0.5 else "green")
            
            return metrics
            
        except Exception as e:
            cprint(f"   ⚠️ Error fetching gas metrics: {str(e)}", "yellow")
            # Return default metrics
            return self._get_default_metrics()
    
    def _fetch_priority_fees(self) -> int:
        """
        Fetch current priority fees from network
        
        In production, this would query:
        - Helius priority fee recommendations
        - Recent blocks for fee trends
        - Mempool analysis
        """
        try:
            # Simulate dynamic priority fee based on time
            # Real implementation would use RPC calls
            base_priority = 100000
            
            # Add randomness to simulate network variance
            variance = np.random.uniform(0.5, 2.0)
            
            return int(base_priority * variance)
            
        except:
            return 100000  # Default
    
    def _estimate_network_congestion(self) -> float:
        """
        Estimate current network congestion (0-1 scale)
        
        Factors:
        - Recent block fullness
        - Transaction success rates
        - Priority fee trends
        """
        try:
            # In production, this would analyze:
            # 1. Recent block compute unit usage
            # 2. Failed transaction rate
            # 3. Priority fee escalation
            
            # Simulate based on time of day
            hour = time.localtime().tm_hour
            
            # Peak hours: 14:00-22:00 UTC (US trading hours)
            if 14 <= hour <= 22:
                return np.random.uniform(0.6, 0.9)  # High congestion
            elif 6 <= hour <= 14:
                return np.random.uniform(0.3, 0.6)  # Medium congestion
            else:
                return np.random.uniform(0.1, 0.3)  # Low congestion
                
        except:
            return 0.5  # Default medium congestion
    
    def _get_default_metrics(self) -> GasFeeMetrics:
        """Get default gas metrics when fetch fails"""
        return GasFeeMetrics(
            timestamp=time.time(),
            base_fee_lamports=5000,
            priority_fee_lamports=100000,
            compute_units=480000,
            total_cost_sol=0.000105,
            total_cost_usd=0.0105,
            network_congestion=0.5
        )
    
    def optimize_trade_for_gas(self, opportunity, current_gas: GasFeeMetrics) -> OptimizedTradeParams:
        """
        Optimize trade size to target $100+ net profit given gas costs
        
        This is the CORE optimization function
        
        Args:
            opportunity: Arbitrage opportunity
            current_gas: Current gas fee metrics
            
        Returns:
            Optimized trade parameters
        """
        cprint(f"\n🎯 OPTIMIZING TRADE FOR ${self.target_net_profit:.0f}+ NET PROFIT", "magenta", attrs=['bold'])
        
        # Current opportunity parameters
        base_trade_size = opportunity.optimal_amount * opportunity.buy_price
        base_profit_pct = opportunity.profit_percent
        
        cprint(f"   Base Trade Size: ${base_trade_size:,.2f}", "cyan")
        cprint(f"   Base Profit: {base_profit_pct:.2f}%", "cyan")
        cprint(f"   Current Gas Cost: ${current_gas.total_cost_usd:.6f}", "yellow")
        
        # Calculate minimum trade size needed for target profit
        min_trade_size = self._calculate_min_trade_size_for_target(
            target_profit=self.target_net_profit,
            profit_pct=base_profit_pct,
            gas_cost=current_gas.total_cost_usd
        )
        
        cprint(f"   Min Trade Size for ${self.target_net_profit:.0f} profit: ${min_trade_size:,.2f}", "green")
        
        # Check if opportunity can reach target
        max_trade_size = opportunity.liquidity_available * 0.3  # Max 30% of liquidity
        
        if min_trade_size > max_trade_size:
            cprint(f"   ⚠️ Target not reachable with available liquidity", "yellow")
            cprint(f"   Max possible trade: ${max_trade_size:,.2f}", "yellow")
            
            # Optimize for maximum profit within constraints
            optimal_size = self._optimize_within_constraints(
                opportunity, current_gas, max_trade_size
            )
        else:
            cprint(f"   ✅ Target reachable! Optimizing...", "green")
            optimal_size = min_trade_size
        
        # Calculate final metrics
        final_params = self._calculate_final_params(
            opportunity, optimal_size, current_gas
        )
        
        # Print optimization results
        self._print_optimization_results(final_params)
        
        return final_params
    
    def _calculate_min_trade_size_for_target(self, target_profit: float, 
                                            profit_pct: float, gas_cost: float) -> float:
        """
        Calculate minimum trade size needed to achieve target profit
        
        Formula:
        net_profit = (trade_size * profit_pct / 100) - gas_cost - fees
        
        Solving for trade_size:
        trade_size = (target_profit + gas_cost + fees) / (profit_pct / 100)
        """
        # Add buffer for fees (flashloan + DEX fees ~0.5%)
        fee_rate = 0.005
        
        # Account for slippage impact on larger trades
        slippage_rate = 0.01  # Assume 1% slippage
        
        # Effective profit after slippage
        effective_profit_pct = profit_pct - slippage_rate
        
        if effective_profit_pct <= 0:
            return float('inf')  # Can't reach target
        
        # Calculate required trade size
        # net = (size * eff_profit%) - gas - (size * fee%)
        # net = size * (eff_profit% - fee%) - gas
        # size = (net + gas) / (eff_profit% - fee%)
        
        net_profit_rate = (effective_profit_pct / 100) - fee_rate
        
        if net_profit_rate <= 0:
            return float('inf')
        
        required_size = (target_profit + gas_cost) / net_profit_rate
        
        return required_size
    
    def _optimize_within_constraints(self, opportunity, gas_metrics: GasFeeMetrics,
                                     max_size: float) -> float:
        """
        Optimize trade size within liquidity constraints
        
        Uses binary search to find optimal size
        """
        low = max_size * 0.1  # Min 10% of max
        high = max_size
        best_size = low
        best_profit = 0
        
        for _ in range(20):  # 20 iterations
            mid = (low + high) / 2
            
            # Calculate expected profit at this size
            profit = self._calculate_expected_profit(opportunity, mid, gas_metrics)
            
            if profit > best_profit:
                best_profit = profit
                best_size = mid
            
            # Binary search logic
            if profit < self.target_net_profit:
                low = mid  # Need larger size
            else:
                high = mid  # Can use smaller size
            
            if abs(high - low) < max_size * 0.01:
                break
        
        return best_size
    
    def _calculate_expected_profit(self, opportunity, trade_size: float,
                                   gas_metrics: GasFeeMetrics) -> float:
        """Calculate expected net profit for a given trade size"""
        # Gross profit
        gross_profit = trade_size * (opportunity.profit_percent / 100)
        
        # Costs
        gas_cost = gas_metrics.total_cost_usd
        flashloan_fee = trade_size * 0.0005  # 0.05%
        dex_fees = trade_size * 0.003  # 0.3%
        
        # Slippage (increases with size)
        liquidity = opportunity.liquidity_available
        slippage_impact = (trade_size / liquidity) * gross_profit * 0.5
        
        # Net profit
        net = gross_profit - gas_cost - flashloan_fee - dex_fees - slippage_impact
        
        return net
    
    def _calculate_final_params(self, opportunity, optimal_size: float,
                               gas_metrics: GasFeeMetrics) -> OptimizedTradeParams:
        """Calculate final optimized parameters"""
        # Expected profit
        expected_profit = self._calculate_expected_profit(
            opportunity, optimal_size, gas_metrics
        )
        
        # Determine priority fee based on profit
        priority_fee = self._select_priority_fee(expected_profit, gas_metrics)
        
        # Recalculate gas with selected priority
        gas_cost_with_priority = (
            (gas_metrics.base_fee_lamports + priority_fee) / 1e9 * self.sol_price_usd
        )
        
        # Profit margin
        profit_margin = (expected_profit / optimal_size) * 100 if optimal_size > 0 else 0
        
        # Check if meets target
        meets_target = expected_profit >= self.target_net_profit
        
        return OptimizedTradeParams(
            optimal_trade_size_usd=optimal_size,
            expected_gas_cost_usd=gas_cost_with_priority,
            expected_net_profit_usd=expected_profit,
            recommended_priority_fee=priority_fee,
            compute_units_required=gas_metrics.compute_units,
            profit_margin_pct=profit_margin,
            meets_target=meets_target
        )
    
    def _select_priority_fee(self, expected_profit: float, 
                           gas_metrics: GasFeeMetrics) -> int:
        """
        Select optimal priority fee based on expected profit
        
        Strategy:
        - High profit (>$200): Ultra priority (fast inclusion)
        - Medium profit ($100-200): High priority
        - Low profit (<$100): Medium priority
        """
        congestion = gas_metrics.network_congestion
        
        if expected_profit >= 200:
            # High profit - use ultra priority
            base = self.priority_strategies['ultra']
        elif expected_profit >= 100:
            # Target profit - use high priority
            base = self.priority_strategies['high']
        elif expected_profit >= 50:
            # Medium profit - use medium priority
            base = self.priority_strategies['medium']
        else:
            # Low profit - use low priority
            base = self.priority_strategies['low']
        
        # Adjust for network congestion
        congestion_multiplier = 1.0 + congestion  # 1.0-2.0x
        
        return int(base * congestion_multiplier)
    
    def _print_optimization_results(self, params: OptimizedTradeParams):
        """Print optimization results"""
        cprint(f"\n   {'='*60}", "green" if params.meets_target else "yellow")
        
        if params.meets_target:
            cprint(f"   ✅ TARGET ACHIEVED: ${params.expected_net_profit_usd:.2f} NET PROFIT", 
                   "green", attrs=['bold'])
        else:
            cprint(f"   ⚠️ Best Possible: ${params.expected_net_profit_usd:.2f} NET PROFIT", 
                   "yellow", attrs=['bold'])
        
        cprint(f"   {'='*60}", "green" if params.meets_target else "yellow")
        cprint(f"   Optimal Trade Size: ${params.optimal_trade_size_usd:,.2f}", "white")
        cprint(f"   Expected Gas Cost: ${params.expected_gas_cost_usd:.6f}", "yellow")
        cprint(f"   Priority Fee: {params.recommended_priority_fee:,} lamports", "cyan")
        cprint(f"   Profit Margin: {params.profit_margin_pct:.2f}%", "green")
        cprint(f"   Gas/Profit Ratio: {(params.expected_gas_cost_usd / params.expected_net_profit_usd * 100):.2f}%", "cyan")
        cprint(f"   {'='*60}\n", "green" if params.meets_target else "yellow")
    
    def update_sol_price(self, new_price: float):
        """Update SOL price for gas calculations"""
        old_price = self.sol_price_usd
        self.sol_price_usd = new_price
        
        cprint(f"💱 SOL price updated: ${old_price:.2f} → ${new_price:.2f}", "cyan")
    
    def adjust_target_profit(self, new_target: float):
        """Adjust target profit dynamically"""
        old_target = self.target_net_profit
        self.target_net_profit = new_target
        
        cprint(f"🎯 Target profit adjusted: ${old_target:.2f} → ${new_target:.2f}", "green")
    
    def get_gas_statistics(self) -> Dict:
        """Get gas fee statistics from history"""
        if not self.gas_history:
            return {'status': 'no_data'}
        
        recent = list(self.gas_history)[-20:]
        
        priority_fees = [g.priority_fee_lamports for g in recent]
        gas_costs_usd = [g.total_cost_usd for g in recent]
        congestion_levels = [g.network_congestion for g in recent]
        
        return {
            'avg_priority_fee': np.mean(priority_fees),
            'max_priority_fee': np.max(priority_fees),
            'min_priority_fee': np.min(priority_fees),
            'avg_gas_cost_usd': np.mean(gas_costs_usd),
            'avg_congestion': np.mean(congestion_levels),
            'current_congestion': recent[-1].network_congestion,
            'samples': len(recent)
        }
    
    def recommend_best_execution_time(self) -> Dict:
        """
        Recommend best time to execute based on gas analysis
        
        Returns current conditions and whether to wait
        """
        current = self.get_current_gas_metrics()
        stats = self.get_gas_statistics()
        
        if stats.get('status') == 'no_data':
            return {'recommendation': 'execute', 'reason': 'no_historical_data'}
        
        current_fee = current.priority_fee_lamports
        avg_fee = stats['avg_priority_fee']
        
        # If current fee is significantly above average, consider waiting
        if current_fee > avg_fee * 1.5:
            return {
                'recommendation': 'wait',
                'reason': f'High gas fees ({current_fee:,} vs avg {avg_fee:,.0f})',
                'current_cost': current.total_cost_usd,
                'avg_cost': stats['avg_gas_cost_usd'],
                'potential_savings': current.total_cost_usd - stats['avg_gas_cost_usd']
            }
        
        # If congestion is very high, might want to use higher priority
        if current.network_congestion > 0.8:
            return {
                'recommendation': 'execute_with_high_priority',
                'reason': 'High network congestion - use ultra priority',
                'current_cost': current.total_cost_usd,
                'recommended_priority': self.priority_strategies['ultra']
            }
        
        # Good conditions for execution
        return {
            'recommendation': 'execute',
            'reason': 'Favorable gas conditions',
            'current_cost': current.total_cost_usd,
            'current_priority': current.priority_fee_lamports
        }
