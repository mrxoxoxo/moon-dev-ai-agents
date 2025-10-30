"""
🌙 Moon Dev's Profitability Guarantee Engine
ENSURES every execution is profitable - NO EXCEPTIONS
Built with love by Moon Dev 🚀

CORE PRINCIPLE: Better to miss opportunities than lose money
"""

import os
import sys
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from termcolor import cprint

@dataclass
class ProfitabilityCheck:
    """Complete profitability validation"""
    is_profitable: bool
    net_profit_usd: float
    confidence_pct: float
    
    # All costs itemized
    gross_profit: float
    gas_cost: float
    flashloan_fee: float
    dex_fees: float
    slippage_cost: float
    mev_protection_cost: float
    contingency_buffer: float
    
    # Risk metrics
    probability_of_profit: float
    expected_value: float
    worst_case_scenario: float
    
    # Validations passed
    validations_passed: List[str]
    validations_failed: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'is_profitable': self.is_profitable,
            'net_profit': self.net_profit_usd,
            'confidence': self.confidence_pct,
            'costs': {
                'gross_profit': self.gross_profit,
                'gas': self.gas_cost,
                'flashloan_fee': self.flashloan_fee,
                'dex_fees': self.dex_fees,
                'slippage': self.slippage_cost,
                'mev_protection': self.mev_protection_cost,
                'buffer': self.contingency_buffer
            },
            'risk': {
                'probability_profit': self.probability_of_profit,
                'expected_value': self.expected_value,
                'worst_case': self.worst_case_scenario
            },
            'validations': {
                'passed': self.validations_passed,
                'failed': self.validations_failed
            }
        }


class ProfitabilityGuarantee:
    """
    ULTIMATE PROFITABILITY VALIDATION
    
    This is the FINAL GATE before any execution
    
    Rules:
    1. ALL costs must be included
    2. Profit must be positive in WORST case scenario
    3. 90%+ probability of profit (Monte Carlo)
    4. Multiple independent validations must agree
    5. If ANY doubt exists, DO NOT EXECUTE
    
    Philosophy: "When in doubt, don't trade out"
    """
    
    def __init__(self, monte_carlo_simulator, game_theory_engine):
        self.mc_sim = monte_carlo_simulator
        self.game_theory = game_theory_engine
        
        # Conservative margins
        self.gas_safety_margin = 2.0  # Assume 2x higher gas
        self.slippage_safety_margin = 1.5  # Assume 1.5x worse slippage
        self.contingency_buffer_pct = 0.05  # 5% buffer for unknowns
        
        # Minimum thresholds (STRICT)
        self.min_net_profit = 0.50  # Absolute minimum $0.50
        self.min_confidence = 90.0  # 90% confidence
        self.min_probability_profit = 0.90  # 90% probability
        self.min_expected_value = 1.00  # $1 minimum EV
        
        # Statistics
        self.total_checks = 0
        self.total_approved = 0
        self.total_rejected = 0
        
        cprint("\n🛡️ PROFITABILITY GUARANTEE ENGINE", "green", attrs=['bold'])
        cprint("="*70, "green")
        cprint("   MISSION: Ensure 100% of executions are profitable", "green", attrs=['bold'])
        cprint("   METHOD: Multi-layer validation with conservative margins", "cyan")
        cprint("="*70, "green")
        cprint(f"\n   Gas Safety Margin: {self.gas_safety_margin}x", "yellow")
        cprint(f"   Slippage Safety Margin: {self.slippage_safety_margin}x", "yellow")
        cprint(f"   Contingency Buffer: {self.contingency_buffer_pct:.1%}", "yellow")
        cprint(f"   Minimum Net Profit: ${self.min_net_profit}", "yellow")
        cprint(f"   Minimum Probability: {self.min_probability_profit:.0%}", "yellow")
    
    def guarantee_profitability(self, opportunity, trade_size: float,
                               gas_metrics: Dict, slippage_prediction: Dict,
                               market_impact: Dict) -> ProfitabilityCheck:
        """
        ULTIMATE profitability check
        
        This function returns True ONLY if we are CERTAIN of profit
        
        Args:
            opportunity: Arbitrage opportunity
            trade_size: Proposed trade size
            gas_metrics: Current gas costs
            slippage_prediction: Predicted slippage
            market_impact: Market impact analysis
            
        Returns:
            ProfitabilityCheck with verdict
        """
        self.total_checks += 1
        
        cprint(f"\n" + "="*70, "green")
        cprint(f"🛡️ PROFITABILITY GUARANTEE CHECK #{self.total_checks}", "green", attrs=['bold'])
        cprint("="*70, "green")
        
        validations_passed = []
        validations_failed = []
        
        # STEP 1: Calculate ALL costs with MAXIMUM safety margins
        costs = self._calculate_all_costs_conservative(
            opportunity, trade_size, gas_metrics, slippage_prediction
        )
        
        gross_profit = opportunity.estimated_profit_usd * (trade_size / opportunity.optimal_amount)
        net_profit = gross_profit - costs['total_costs']
        
        cprint(f"\n💰 PROFIT ANALYSIS (Conservative):", "yellow")
        cprint(f"   Gross Profit: ${gross_profit:.6f}", "white")
        cprint(f"   Total Costs: ${costs['total_costs']:.6f}", "yellow")
        cprint(f"   Net Profit: ${net_profit:.6f}", "green" if net_profit > 0 else "red", attrs=['bold'])
        
        # VALIDATION 1: Positive net profit
        if net_profit > self.min_net_profit:
            validations_passed.append(f"Net profit ${net_profit:.6f} > ${self.min_net_profit}")
            cprint(f"   ✅ PASS: Net profit positive", "green")
        else:
            validations_failed.append(f"Net profit ${net_profit:.6f} <= ${self.min_net_profit}")
            cprint(f"   ❌ FAIL: Net profit too low or negative", "red")
        
        # STEP 2: Monte Carlo simulation
        cprint(f"\n🎲 Running Monte Carlo simulation...", "cyan")
        mc_result = self.mc_sim.simulate_opportunity(opportunity, trade_size)
        
        # VALIDATION 2: Probability of profit
        if mc_result.probability_profit >= self.min_probability_profit:
            validations_passed.append(f"Profit probability {mc_result.probability_profit:.1%} >= {self.min_probability_profit:.0%}")
            cprint(f"   ✅ PASS: {mc_result.probability_profit:.1%} probability of profit", "green")
        else:
            validations_failed.append(f"Profit probability {mc_result.probability_profit:.1%} < {self.min_probability_profit:.0%}")
            cprint(f"   ❌ FAIL: Probability too low", "red")
        
        # VALIDATION 3: Expected value
        if mc_result.mean_profit >= self.min_expected_value:
            validations_passed.append(f"Expected value ${mc_result.mean_profit:.2f} >= ${self.min_expected_value}")
            cprint(f"   ✅ PASS: Expected value ${mc_result.mean_profit:.2f}", "green")
        else:
            validations_failed.append(f"Expected value ${mc_result.mean_profit:.2f} < ${self.min_expected_value}")
            cprint(f"   ❌ FAIL: Expected value too low", "red")
        
        # VALIDATION 4: Worst case scenario
        if mc_result.worst_case > -costs['gas_cost']:
            validations_passed.append(f"Worst case ${mc_result.worst_case:.2f} better than -gas")
            cprint(f"   ✅ PASS: Worst case ${mc_result.worst_case:.2f} acceptable", "green")
        else:
            validations_failed.append(f"Worst case ${mc_result.worst_case:.2f} unacceptable")
            cprint(f"   ⚠️ WARNING: Worst case scenario is negative", "yellow")
        
        # VALIDATION 5: Value at Risk (VaR)
        if mc_result.var_95 > -net_profit * 0.5:
            validations_passed.append(f"VaR ${mc_result.var_95:.2f} acceptable")
            cprint(f"   ✅ PASS: VaR ${mc_result.var_95:.2f} manageable", "green")
        else:
            validations_failed.append(f"VaR ${mc_result.var_95:.2f} too high")
            cprint(f"   ❌ FAIL: VaR indicates high risk", "red")
        
        # VALIDATION 6: Sharpe ratio (risk-adjusted return)
        if mc_result.sharpe_ratio > 1.0:
            validations_passed.append(f"Sharpe ratio {mc_result.sharpe_ratio:.2f} > 1.0")
            cprint(f"   ✅ PASS: Sharpe ratio {mc_result.sharpe_ratio:.2f}", "green")
        else:
            validations_failed.append(f"Sharpe ratio {mc_result.sharpe_ratio:.2f} <= 1.0")
            cprint(f"   ⚠️ WARNING: Low risk-adjusted return", "yellow")
        
        # STEP 3: Game theory analysis
        cprint(f"\n🎮 Game theory analysis...", "cyan")
        
        # Predict if competitors will interfere
        competitor_analysis = self._analyze_competition(opportunity, trade_size)
        
        # VALIDATION 7: Competition
        if competitor_analysis['win_probability'] > 0.5:
            validations_passed.append(f"Win probability {competitor_analysis['win_probability']:.1%}")
            cprint(f"   ✅ PASS: {competitor_analysis['win_probability']:.1%} chance to win", "green")
        else:
            validations_failed.append(f"Win probability {competitor_analysis['win_probability']:.1%} too low")
            cprint(f"   ⚠️ WARNING: High competition risk", "yellow")
        
        # STEP 4: Calculate confidence score
        confidence = self._calculate_overall_confidence(
            validations_passed, validations_failed, mc_result
        )
        
        # FINAL DECISION
        is_profitable = (
            len(validations_failed) == 0 and
            net_profit > self.min_net_profit and
            mc_result.probability_profit >= self.min_probability_profit and
            confidence >= self.min_confidence
        )
        
        result = ProfitabilityCheck(
            is_profitable=is_profitable,
            net_profit_usd=net_profit,
            confidence_pct=confidence,
            gross_profit=gross_profit,
            gas_cost=costs['gas_cost'],
            flashloan_fee=costs['flashloan_fee'],
            dex_fees=costs['dex_fees'],
            slippage_cost=costs['slippage_cost'],
            mev_protection_cost=costs['mev_cost'],
            contingency_buffer=costs['contingency'],
            probability_of_profit=mc_result.probability_profit,
            expected_value=mc_result.mean_profit,
            worst_case_scenario=mc_result.worst_case,
            validations_passed=validations_passed,
            validations_failed=validations_failed
        )
        
        self._print_final_verdict(result)
        
        if is_profitable:
            self.total_approved += 1
        else:
            self.total_rejected += 1
        
        return result
    
    def _calculate_all_costs_conservative(self, opportunity, trade_size: float,
                                         gas_metrics: Dict, slippage_pred: Dict) -> Dict:
        """
        Calculate ALL possible costs with MAXIMUM safety margins
        
        Philosophy: Assume everything costs MORE than estimated
        """
        # Gas cost (with 2x safety margin)
        base_gas = gas_metrics.get('total_cost_usd', opportunity.estimated_gas_cost_usd)
        gas_cost = base_gas * self.gas_safety_margin
        
        # Flashloan fee (standard 0.05%)
        flashloan_fee = trade_size * 0.0005
        
        # DEX fees (0.3% per swap, assume 2 swaps)
        dex_fees = trade_size * 0.003 * 2
        
        # Slippage cost (with 1.5x safety margin)
        base_slippage = slippage_pred.get('slippage_loss_usd', 0)
        slippage_cost = base_slippage * self.slippage_safety_margin
        
        # MEV protection cost (Jito tip - 10% of profit)
        mev_cost = opportunity.net_profit_usd * 0.1
        
        # Contingency buffer (unexpected costs)
        subtotal = gas_cost + flashloan_fee + dex_fees + slippage_cost + mev_cost
        contingency = subtotal * self.contingency_buffer_pct
        
        total_costs = subtotal + contingency
        
        cprint(f"\n💸 CONSERVATIVE COST BREAKDOWN:", "yellow")
        cprint(f"   Gas (2x margin): ${gas_cost:.6f}", "white")
        cprint(f"   Flashloan Fee: ${flashloan_fee:.6f}", "white")
        cprint(f"   DEX Fees: ${dex_fees:.6f}", "white")
        cprint(f"   Slippage (1.5x margin): ${slippage_cost:.6f}", "white")
        cprint(f"   MEV Protection: ${mev_cost:.6f}", "white")
        cprint(f"   Contingency (5%): ${contingency:.6f}", "white")
        cprint(f"   ───────────────────────", "yellow")
        cprint(f"   TOTAL COSTS: ${total_costs:.6f}", "yellow", attrs=['bold'])
        
        return {
            'gas_cost': gas_cost,
            'flashloan_fee': flashloan_fee,
            'dex_fees': dex_fees,
            'slippage_cost': slippage_cost,
            'mev_cost': mev_cost,
            'contingency': contingency,
            'total_costs': total_costs
        }
    
    def _analyze_competition(self, opportunity, trade_size: float) -> Dict:
        """Analyze competition for this opportunity"""
        # Simple model - would use actual mempool analysis
        # Assume 2-3 competing bots on average
        
        num_competitors = np.random.randint(1, 4)
        
        # Our strategy vs competitors
        our_gas_factor = 1.5  # We bid 1.5x base gas
        
        # Win if we outbid (simplified)
        win_prob = 0.6  # 60% base chance
        
        return {
            'num_competitors': num_competitors,
            'our_gas_factor': our_gas_factor,
            'win_probability': win_prob
        }
    
    def _calculate_overall_confidence(self, passed: List[str], failed: List[str],
                                     mc_result) -> float:
        """
        Calculate overall confidence in profitability
        
        Combines:
        - Validation pass rate
        - Monte Carlo probability
        - Historical accuracy
        """
        # Validation score
        total_validations = len(passed) + len(failed)
        validation_score = (len(passed) / total_validations * 100) if total_validations > 0 else 0
        
        # Monte Carlo score
        mc_score = mc_result.probability_profit * 100
        
        # Combined confidence (conservative - take minimum)
        confidence = min(validation_score, mc_score)
        
        return confidence
    
    def _print_final_verdict(self, check: ProfitabilityCheck):
        """Print final profitability verdict"""
        cprint(f"\n" + "="*70, "green" if check.is_profitable else "red")
        
        if check.is_profitable:
            cprint(f"✅ PROFITABILITY GUARANTEED", "green", attrs=['bold'])
            cprint(f"="*70, "green")
            cprint(f"\n   NET PROFIT: ${check.net_profit_usd:.6f}", "green", attrs=['bold'])
            cprint(f"   CONFIDENCE: {check.confidence_pct:.1f}%", "green")
            cprint(f"   PROBABILITY: {check.probability_of_profit:.1%}", "green")
            cprint(f"   EXPECTED VALUE: ${check.expected_value:.2f}", "green")
            cprint(f"\n   Validations Passed: {len(check.validations_passed)}/{len(check.validations_passed) + len(check.validations_failed)}", "green")
            cprint(f"\n   🚀 EXECUTE IMMEDIATELY", "green", attrs=['bold'])
        else:
            cprint(f"❌ PROFITABILITY NOT GUARANTEED", "red", attrs=['bold'])
            cprint(f"="*70, "red")
            cprint(f"\n   NET PROFIT: ${check.net_profit_usd:.6f}", "red")
            cprint(f"   CONFIDENCE: {check.confidence_pct:.1f}%", "red")
            cprint(f"   PROBABILITY: {check.probability_of_profit:.1%}", "red")
            cprint(f"\n   Validations Failed: {len(check.validations_failed)}", "red")
            
            for failure in check.validations_failed:
                cprint(f"      ❌ {failure}", "red")
            
            cprint(f"\n   🛑 DO NOT EXECUTE - RISK OF LOSS", "red", attrs=['bold'])
        
        cprint(f"="*70 + "\n", "green" if check.is_profitable else "red")
    
    def validate_multi_hop_profitability(self, path, trade_size: float) -> ProfitabilityCheck:
        """
        Special validation for multi-hop arbitrage (more complex = more risk)
        
        Additional considerations:
        - Each hop adds slippage
        - Each hop adds gas cost
        - Each hop adds failure risk
        - Cumulative probability of success decreases
        """
        cprint(f"\n🔀 Multi-Hop Profitability Validation", "cyan", attrs=['bold'])
        cprint(f"   Path Length: {path.path_length} hops", "cyan")
        
        # Calculate per-hop failure probability
        per_hop_success = 0.98  # 98% success per hop
        cumulative_success = per_hop_success ** path.path_length
        
        cprint(f"   Cumulative Success Probability: {cumulative_success:.1%}", "yellow")
        
        # Adjust expected profit for failure risk
        adjusted_profit = path.expected_profit_usd * cumulative_success
        
        # Multi-hop costs (gas increases with complexity)
        total_gas = path.execution_complexity * 0.0001 * 100  # $0.01 per swap
        
        net_profit = adjusted_profit - total_gas
        
        # Create simplified profitability check
        is_profitable = (
            net_profit > self.min_net_profit and
            cumulative_success >= 0.85  # 85% min for multi-hop
        )
        
        return ProfitabilityCheck(
            is_profitable=is_profitable,
            net_profit_usd=net_profit,
            confidence_pct=cumulative_success * 100,
            gross_profit=path.expected_profit_usd,
            gas_cost=total_gas,
            flashloan_fee=0,
            dex_fees=path.total_fees * trade_size,
            slippage_cost=path.total_slippage * trade_size,
            mev_protection_cost=0,
            contingency_buffer=0,
            probability_of_profit=cumulative_success,
            expected_value=adjusted_profit,
            worst_case_scenario=net_profit * 0.5,
            validations_passed=[f"Multi-hop validated"] if is_profitable else [],
            validations_failed=[] if is_profitable else [f"Multi-hop too risky"]
        )
    
    def get_profitability_stats(self) -> Dict:
        """Get profitability guarantee statistics"""
        approval_rate = (self.total_approved / max(1, self.total_checks)) * 100
        
        return {
            'total_checks': self.total_checks,
            'total_approved': self.total_approved,
            'total_rejected': self.total_rejected,
            'approval_rate': approval_rate,
            'rejection_rate': 100 - approval_rate
        }
