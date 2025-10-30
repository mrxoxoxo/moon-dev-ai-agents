"""
🌙 Moon Dev's Monte Carlo Simulation Engine
Probabilistic analysis for optimal decision making
Built with love by Moon Dev 🚀
"""

import os
import sys
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from termcolor import cprint
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
from scipy import stats

@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation"""
    mean_profit: float
    median_profit: float
    std_dev: float
    var_95: float  # Value at Risk (95% confidence)
    cvar_95: float  # Conditional VaR
    probability_profit: float
    probability_loss: float
    best_case: float  # 95th percentile
    worst_case: float  # 5th percentile
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    simulations: int
    
    def to_dict(self) -> Dict:
        return {
            'mean_profit': self.mean_profit,
            'median_profit': self.median_profit,
            'std_dev': self.std_dev,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'prob_profit': self.probability_profit,
            'prob_loss': self.probability_loss,
            'best_case': self.best_case,
            'worst_case': self.worst_case,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'simulations': self.simulations
        }


class MonteCarloSimulator:
    """
    Monte Carlo simulation for flashloan arbitrage
    
    Simulates thousands of possible outcomes considering:
    - Price volatility
    - Slippage variance
    - Gas cost fluctuation
    - Execution probability
    - Market impact
    - Competition
    
    Uses to:
    - Assess risk before execution
    - Choose between multiple opportunities
    - Optimize position sizing
    - Estimate confidence intervals
    """
    
    def __init__(self, num_simulations: int = 10000):
        self.num_simulations = num_simulations
        
        # Risk-free rate (for Sharpe calculation)
        self.risk_free_rate = 0.0  # Conservative assumption
        
        cprint("\n🎲 Monte Carlo Simulator Initialized", "cyan", attrs=['bold'])
        cprint(f"   Simulations per analysis: {self.num_simulations:,}", "cyan")
        cprint("   Risk Metrics: VaR, CVaR, Sharpe, Sortino", "cyan")
    
    def simulate_opportunity(self, opportunity, trade_size: float,
                           historical_data: Optional[Dict] = None) -> MonteCarloResult:
        """
        Run Monte Carlo simulation on an opportunity
        
        Args:
            opportunity: Arbitrage opportunity
            trade_size: Proposed trade size
            historical_data: Historical execution data for better estimates
            
        Returns:
            Monte Carlo results with risk metrics
        """
        cprint(f"\n🎲 Running {self.num_simulations:,} Monte Carlo simulations...", "cyan", attrs=['bold'])
        
        # Extract parameters
        expected_profit = opportunity.net_profit_usd
        expected_slippage = 0.01  # 1% base estimate
        gas_cost = opportunity.estimated_gas_cost_usd
        
        # Generate probability distributions
        profits = []
        
        for i in range(self.num_simulations):
            # Simulate random variables
            simulated_profit = self._simulate_single_trade(
                expected_profit,
                expected_slippage,
                gas_cost,
                trade_size,
                opportunity
            )
            
            profits.append(simulated_profit)
        
        profits = np.array(profits)
        
        # Calculate statistics
        result = self._calculate_statistics(profits)
        
        # Print results
        self._print_mc_results(result)
        
        return result
    
    def _simulate_single_trade(self, expected_profit: float, expected_slippage: float,
                               gas_cost: float, trade_size: float, opportunity) -> float:
        """
        Simulate a single trade outcome
        
        Considers random variations in:
        - Price (log-normal distribution)
        - Slippage (gamma distribution)
        - Gas costs (log-normal)
        - Execution probability (binomial)
        """
        # Price volatility (log-normal)
        price_volatility = 0.02  # 2% volatility
        price_factor = np.random.lognormal(0, price_volatility)
        
        # Slippage (gamma distribution - right-skewed)
        alpha, beta = 2.0, expected_slippage / 2.0
        actual_slippage = np.random.gamma(alpha, beta)
        
        # Gas cost (log-normal - can spike)
        gas_volatility = 0.5  # 50% volatility in gas
        actual_gas = gas_cost * np.random.lognormal(0, gas_volatility)
        
        # Execution probability (bernoulli)
        execution_prob = 0.95  # 95% chance of execution
        executed = np.random.random() < execution_prob
        
        if not executed:
            # Failed execution - only gas cost
            return -actual_gas
        
        # Calculate profit
        gross_profit = expected_profit * price_factor
        slippage_loss = trade_size * actual_slippage
        net_profit = gross_profit - slippage_loss - actual_gas
        
        # Additional random factors
        # MEV competition (10% chance someone front-runs)
        if np.random.random() < 0.10:
            net_profit *= 0.5  # Lose half to competition
        
        return net_profit
    
    def _calculate_statistics(self, profits: np.ndarray) -> MonteCarloResult:
        """Calculate comprehensive statistics from simulations"""
        # Basic statistics
        mean_profit = np.mean(profits)
        median_profit = np.median(profits)
        std_dev = np.std(profits)
        
        # Value at Risk (VaR) - 5th percentile loss
        var_95 = np.percentile(profits, 5)
        
        # Conditional VaR (expected loss beyond VaR)
        cvar_95 = np.mean(profits[profits <= var_95])
        
        # Probabilities
        prob_profit = np.sum(profits > 0) / len(profits)
        prob_loss = np.sum(profits < 0) / len(profits)
        
        # Best/worst cases
        best_case = np.percentile(profits, 95)
        worst_case = np.percentile(profits, 5)
        
        # Sharpe Ratio (risk-adjusted return)
        if std_dev > 0:
            sharpe_ratio = (mean_profit - self.risk_free_rate) / std_dev
        else:
            sharpe_ratio = 0
        
        # Sortino Ratio (downside risk only)
        downside_returns = profits[profits < 0]
        if len(downside_returns) > 0:
            downside_std = np.std(downside_returns)
            if downside_std > 0:
                sortino_ratio = (mean_profit - self.risk_free_rate) / downside_std
            else:
                sortino_ratio = 0
        else:
            sortino_ratio = float('inf') if mean_profit > 0 else 0
        
        # Maximum Drawdown
        cumulative = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        return MonteCarloResult(
            mean_profit=mean_profit,
            median_profit=median_profit,
            std_dev=std_dev,
            var_95=var_95,
            cvar_95=cvar_95,
            probability_profit=prob_profit,
            probability_loss=prob_loss,
            best_case=best_case,
            worst_case=worst_case,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            simulations=len(profits)
        )
    
    def _print_mc_results(self, result: MonteCarloResult):
        """Print Monte Carlo results"""
        cprint(f"\n   {'='*70}", "cyan")
        cprint(f"   🎲 MONTE CARLO RESULTS ({result.simulations:,} simulations)", "cyan", attrs=['bold'])
        cprint(f"   {'='*70}", "cyan")
        
        cprint(f"\n   📊 Profit Distribution:", "yellow")
        cprint(f"      Mean: ${result.mean_profit:.2f}", "white")
        cprint(f"      Median: ${result.median_profit:.2f}", "white")
        cprint(f"      Std Dev: ${result.std_dev:.2f}", "white")
        
        cprint(f"\n   📈 Percentiles:", "yellow")
        cprint(f"      Best Case (95th): ${result.best_case:.2f}", "green")
        cprint(f"      Worst Case (5th): ${result.worst_case:.2f}", "red")
        
        cprint(f"\n   ⚠️ Risk Metrics:", "yellow")
        cprint(f"      VaR (95%): ${result.var_95:.2f}", "red" if result.var_95 < 0 else "green")
        cprint(f"      CVaR (95%): ${result.cvar_95:.2f}", "red" if result.cvar_95 < 0 else "green")
        cprint(f"      Max Drawdown: ${result.max_drawdown:.2f}", "red")
        
        cprint(f"\n   📊 Probabilities:", "yellow")
        cprint(f"      Profit: {result.probability_profit:.1%}", "green")
        cprint(f"      Loss: {result.probability_loss:.1%}", "red")
        
        cprint(f"\n   📉 Risk-Adjusted Returns:", "yellow")
        cprint(f"      Sharpe Ratio: {result.sharpe_ratio:.2f}", "green" if result.sharpe_ratio > 1 else "yellow")
        cprint(f"      Sortino Ratio: {result.sortino_ratio:.2f}", "green" if result.sortino_ratio > 1 else "yellow")
        
        # Decision recommendation
        if result.probability_profit > 0.90 and result.mean_profit > 100:
            cprint(f"\n   ✅ STRONG OPPORTUNITY - High probability success", "green", attrs=['bold'])
        elif result.probability_profit > 0.80 and result.mean_profit > 50:
            cprint(f"\n   ✅ GOOD OPPORTUNITY - Favorable risk/reward", "green")
        elif result.probability_profit > 0.70:
            cprint(f"\n   ⚠️ MODERATE OPPORTUNITY - Acceptable risk", "yellow")
        else:
            cprint(f"\n   ❌ HIGH RISK - Consider skipping", "red", attrs=['bold'])
        
        cprint(f"   {'='*70}\n", "cyan")
    
    def compare_opportunities(self, opportunities: List[Tuple], trade_size: float) -> List[Dict]:
        """
        Compare multiple opportunities using Monte Carlo
        
        Args:
            opportunities: List of (opportunity, name) tuples
            trade_size: Trade size for each
            
        Returns:
            Ranked list with scores
        """
        cprint(f"\n🎯 Comparing {len(opportunities)} opportunities...", "magenta", attrs=['bold'])
        
        results = []
        
        for opportunity, name in opportunities:
            cprint(f"\n--- Analyzing: {name} ---", "cyan")
            
            mc_result = self.simulate_opportunity(opportunity, trade_size)
            
            # Calculate composite score
            score = self._calculate_opportunity_score(mc_result)
            
            results.append({
                'name': name,
                'opportunity': opportunity,
                'mc_result': mc_result,
                'score': score
            })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Print rankings
        cprint(f"\n🏆 OPPORTUNITY RANKINGS:", "magenta", attrs=['bold'])
        for i, result in enumerate(results, 1):
            cprint(f"   {i}. {result['name']}", "cyan")
            cprint(f"      Score: {result['score']:.2f}", "green")
            cprint(f"      Expected: ${result['mc_result'].mean_profit:.2f}", "white")
            cprint(f"      Probability: {result['mc_result'].probability_profit:.1%}", "white")
        
        return results
    
    def _calculate_opportunity_score(self, mc_result: MonteCarloResult) -> float:
        """
        Calculate composite opportunity score
        
        Factors:
        - Expected profit (40%)
        - Probability of profit (30%)
        - Sharpe ratio (20%)
        - Low risk (10%)
        """
        # Normalize components
        profit_score = min(100, mc_result.mean_profit / 10)  # $1000 = 100 points
        prob_score = mc_result.probability_profit * 100
        sharpe_score = min(100, mc_result.sharpe_ratio * 30)
        risk_score = 100 - min(100, abs(mc_result.var_95) / 10)  # Lower VaR = higher score
        
        # Weighted average
        total_score = (
            profit_score * 0.4 +
            prob_score * 0.3 +
            sharpe_score * 0.2 +
            risk_score * 0.1
        )
        
        return total_score
    
    def optimize_position_size(self, opportunity, min_size: float = 1000,
                              max_size: float = 100000, step: float = 5000) -> Dict:
        """
        Find optimal position size using Monte Carlo
        
        Varies position size and finds the one with best risk-adjusted return
        
        Args:
            opportunity: Arbitrage opportunity
            min_size: Minimum trade size
            max_size: Maximum trade size
            step: Size increment for testing
            
        Returns:
            Optimal size and expected results
        """
        cprint(f"\n🎯 Optimizing position size...", "cyan")
        
        sizes = np.arange(min_size, max_size + step, step)
        best_size = min_size
        best_sharpe = -float('inf')
        best_result = None
        
        for size in sizes:
            # Quick simulation (fewer iterations for speed)
            quick_sim = MonteCarloSimulator(num_simulations=1000)
            result = quick_sim.simulate_opportunity(opportunity, size)
            
            if result.sharpe_ratio > best_sharpe and result.probability_profit > 0.8:
                best_sharpe = result.sharpe_ratio
                best_size = size
                best_result = result
        
        cprint(f"\n✅ Optimal Size: ${best_size:,.0f}", "green", attrs=['bold'])
        cprint(f"   Sharpe Ratio: {best_sharpe:.2f}", "cyan")
        cprint(f"   Expected Profit: ${best_result.mean_profit:.2f}", "green")
        
        return {
            'optimal_size': best_size,
            'sharpe_ratio': best_sharpe,
            'mc_result': best_result
        }
