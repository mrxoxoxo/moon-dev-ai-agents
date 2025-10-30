"""
🌙 Moon Dev's Flashloan Execution Validator
Ensures 80%+ accuracy and prevents unprofitable executions
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

@dataclass
class ExecutionDecision:
    """Decision whether to execute a trade"""
    should_execute: bool
    confidence: float  # 0-100%
    expected_net_profit: float
    risk_score: float
    reasons: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'should_execute': self.should_execute,
            'confidence': self.confidence,
            'expected_net_profit': self.expected_net_profit,
            'risk_score': self.risk_score,
            'reasons': self.reasons,
            'warnings': self.warnings
        }


class FlashloanValidator:
    """
    Validates flashloan executions with 80% minimum accuracy requirement
    
    CRITICAL RULES:
    1. Gas fees MUST be profitable
    2. Net profit MUST be positive after ALL costs
    3. Confidence MUST be >= 80% to execute
    4. Track accuracy and adapt thresholds
    """
    
    def __init__(self, min_accuracy_target: float = 80.0):
        """
        Initialize validator
        
        Args:
            min_accuracy_target: Minimum accuracy % required (default 80%)
        """
        self.min_accuracy_target = min_accuracy_target
        
        # Execution history for accuracy tracking
        self.execution_history: deque = deque(maxlen=100)
        
        # Validation thresholds (adaptive)
        self.min_confidence = 80.0  # Start at 80%
        self.min_net_profit_usd = 0.01  # Must profit at least 1 cent
        self.max_risk_score = 0.3  # Max 30% risk
        
        # Gas cost safety margins
        self.gas_safety_multiplier = 1.5  # Assume 50% higher gas than estimated
        
        # Accuracy statistics
        self.total_validations = 0
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        
        cprint("\n🛡️ Flashloan Validator Initialized", "cyan", attrs=['bold'])
        cprint(f"   Minimum Accuracy Target: {self.min_accuracy_target}%", "yellow")
        cprint(f"   Minimum Confidence: {self.min_confidence}%", "yellow")
        cprint(f"   Minimum Net Profit: ${self.min_net_profit_usd}", "yellow")
        cprint(f"   Gas Safety Margin: {self.gas_safety_multiplier}x", "yellow")
    
    def validate_execution(self, opportunity, slippage_prediction: Dict, 
                          market_impact: Dict) -> ExecutionDecision:
        """
        Validate if trade should be executed
        
        This is the CRITICAL GATE - only profitable trades with high confidence pass
        
        Args:
            opportunity: ArbitrageOpportunity object
            slippage_prediction: Slippage prediction from SlippagePredictor
            market_impact: Market impact analysis
            
        Returns:
            ExecutionDecision with verdict
        """
        self.total_validations += 1
        
        cprint(f"\n🔍 VALIDATING EXECUTION (Validation #{self.total_validations})", "yellow", attrs=['bold'])
        
        reasons = []
        warnings = []
        
        # STEP 1: Calculate TRUE net profit including ALL costs
        net_profit_analysis = self._calculate_true_net_profit(
            opportunity, slippage_prediction, market_impact
        )
        
        expected_net_profit = net_profit_analysis['net_profit_after_all_costs']
        
        cprint(f"   💰 Expected Net Profit: ${expected_net_profit:.6f}", 
               "green" if expected_net_profit > 0 else "red")
        
        # STEP 2: Check if profitable after ALL costs
        if expected_net_profit <= 0:
            reasons.append(f"Unprofitable after all costs: ${expected_net_profit:.6f}")
            cprint(f"   ❌ REJECTED: Unprofitable (${expected_net_profit:.6f})", "red", attrs=['bold'])
            
            return ExecutionDecision(
                should_execute=False,
                confidence=0.0,
                expected_net_profit=expected_net_profit,
                risk_score=1.0,
                reasons=reasons,
                warnings=warnings
            )
        
        if expected_net_profit < self.min_net_profit_usd:
            reasons.append(f"Profit too small: ${expected_net_profit:.6f} < ${self.min_net_profit_usd}")
            cprint(f"   ❌ REJECTED: Profit too small", "red")
            
            return ExecutionDecision(
                should_execute=False,
                confidence=0.0,
                expected_net_profit=expected_net_profit,
                risk_score=0.8,
                reasons=reasons,
                warnings=warnings
            )
        
        reasons.append(f"Profitable: ${expected_net_profit:.6f}")
        
        # STEP 3: Calculate confidence score
        confidence = self._calculate_confidence_score(
            opportunity, slippage_prediction, market_impact, net_profit_analysis
        )
        
        cprint(f"   📊 Confidence Score: {confidence:.1f}%", 
               "green" if confidence >= self.min_confidence else "yellow")
        
        # STEP 4: Check confidence threshold
        if confidence < self.min_confidence:
            reasons.append(f"Confidence too low: {confidence:.1f}% < {self.min_confidence}%")
            cprint(f"   ❌ REJECTED: Confidence below threshold", "red")
            
            return ExecutionDecision(
                should_execute=False,
                confidence=confidence,
                expected_net_profit=expected_net_profit,
                risk_score=0.6,
                reasons=reasons,
                warnings=warnings
            )
        
        reasons.append(f"High confidence: {confidence:.1f}%")
        
        # STEP 5: Calculate risk score
        risk_score = self._calculate_risk_score(opportunity, slippage_prediction, market_impact)
        
        cprint(f"   ⚠️ Risk Score: {risk_score:.2f} (0=safe, 1=risky)", 
               "green" if risk_score < 0.3 else "yellow" if risk_score < 0.6 else "red")
        
        # STEP 6: Check risk threshold
        if risk_score > self.max_risk_score:
            reasons.append(f"Risk too high: {risk_score:.2f} > {self.max_risk_score}")
            warnings.append(f"High risk trade: {risk_score:.2f}")
            cprint(f"   ❌ REJECTED: Risk too high", "red")
            
            return ExecutionDecision(
                should_execute=False,
                confidence=confidence,
                expected_net_profit=expected_net_profit,
                risk_score=risk_score,
                reasons=reasons,
                warnings=warnings
            )
        
        reasons.append(f"Acceptable risk: {risk_score:.2f}")
        
        # STEP 7: Final validation checks
        final_checks = self._final_validation_checks(opportunity, net_profit_analysis)
        
        if not final_checks['passed']:
            reasons.extend(final_checks['failures'])
            warnings.extend(final_checks['warnings'])
            cprint(f"   ❌ REJECTED: Failed final validation", "red")
            
            return ExecutionDecision(
                should_execute=False,
                confidence=confidence,
                expected_net_profit=expected_net_profit,
                risk_score=risk_score,
                reasons=reasons,
                warnings=warnings
            )
        
        # ALL CHECKS PASSED - APPROVE EXECUTION
        cprint(f"   ✅ APPROVED FOR EXECUTION", "green", attrs=['bold'])
        cprint(f"      Expected Profit: ${expected_net_profit:.6f}", "green")
        cprint(f"      Confidence: {confidence:.1f}%", "green")
        cprint(f"      Risk: {risk_score:.2f}", "green")
        
        return ExecutionDecision(
            should_execute=True,
            confidence=confidence,
            expected_net_profit=expected_net_profit,
            risk_score=risk_score,
            reasons=reasons,
            warnings=warnings
        )
    
    def _calculate_true_net_profit(self, opportunity, slippage_pred: Dict, 
                                   market_impact: Dict) -> Dict:
        """
        Calculate TRUE net profit including ALL costs
        
        Costs included:
        1. Gas fees (with safety margin)
        2. Flashloan fees
        3. DEX swap fees
        4. Slippage impact
        5. Market impact
        """
        # Gross profit before any costs
        gross_profit = opportunity.estimated_profit_usd
        
        # Cost 1: Gas fees (with safety margin for spikes)
        estimated_gas = opportunity.estimated_gas_cost_usd
        safe_gas_cost = estimated_gas * self.gas_safety_multiplier
        
        # Cost 2: Flashloan fees
        flashloan_fee = opportunity.flashloan_fee_usd
        
        # Cost 3: DEX swap fees (already in price, but double check)
        dex_fees = 0
        if hasattr(opportunity, 'buy_dex'):
            # Estimate DEX fees if not already included
            dex_fees = opportunity.optimal_amount * opportunity.buy_price * 0.003  # 0.3% typical
        
        # Cost 4: Slippage impact
        slippage_loss = slippage_pred.get('slippage_loss_usd', 0)
        
        # Cost 5: Market impact (if using larger size)
        market_impact_loss = 0
        if market_impact and market_impact.get('recommended_size', 0) > 0:
            # Market impact already factored into recommended size
            pass
        
        # Total costs
        total_costs = safe_gas_cost + flashloan_fee + dex_fees + slippage_loss + market_impact_loss
        
        # Net profit
        net_profit = gross_profit - total_costs
        
        analysis = {
            'gross_profit': gross_profit,
            'gas_cost': safe_gas_cost,
            'flashloan_fee': flashloan_fee,
            'dex_fees': dex_fees,
            'slippage_loss': slippage_loss,
            'market_impact_loss': market_impact_loss,
            'total_costs': total_costs,
            'net_profit_after_all_costs': net_profit,
            'profit_margin_pct': (net_profit / gross_profit * 100) if gross_profit > 0 else 0
        }
        
        # Print cost breakdown
        cprint(f"\n   💸 Cost Breakdown:", "cyan")
        cprint(f"      Gross Profit: ${gross_profit:.6f}", "white")
        cprint(f"      - Gas (w/ margin): ${safe_gas_cost:.6f}", "yellow")
        cprint(f"      - Flashloan Fee: ${flashloan_fee:.6f}", "yellow")
        cprint(f"      - DEX Fees: ${dex_fees:.6f}", "yellow")
        cprint(f"      - Slippage: ${slippage_loss:.6f}", "yellow")
        cprint(f"      = Net Profit: ${net_profit:.6f}", "green" if net_profit > 0 else "red")
        
        return analysis
    
    def _calculate_confidence_score(self, opportunity, slippage_pred: Dict,
                                    market_impact: Dict, net_profit_analysis: Dict) -> float:
        """
        Calculate confidence score (0-100%)
        
        Higher confidence = more likely to succeed
        """
        confidence_factors = []
        
        # Factor 1: Profit margin (higher = better)
        profit_margin = net_profit_analysis['profit_margin_pct']
        if profit_margin > 50:
            confidence_factors.append(95)
        elif profit_margin > 25:
            confidence_factors.append(85)
        elif profit_margin > 10:
            confidence_factors.append(75)
        else:
            confidence_factors.append(60)
        
        # Factor 2: Slippage prediction confidence
        slippage_confidence = slippage_pred.get('model_confidence', 0.5) * 100
        confidence_factors.append(slippage_confidence)
        
        # Factor 3: Liquidity depth (higher = better)
        liquidity = opportunity.liquidity_available
        if liquidity > 1000000:  # $1M+
            confidence_factors.append(95)
        elif liquidity > 500000:  # $500k+
            confidence_factors.append(85)
        elif liquidity > 100000:  # $100k+
            confidence_factors.append(75)
        else:
            confidence_factors.append(60)
        
        # Factor 4: Historical accuracy
        if len(self.execution_history) >= 10:
            recent_accuracy = self._get_recent_accuracy()
            confidence_factors.append(recent_accuracy)
        else:
            confidence_factors.append(70)  # Default if no history
        
        # Factor 5: Price stability (low slippage = stable)
        predicted_slippage = slippage_pred.get('predicted_slippage_pct', 5)
        if predicted_slippage < 0.5:
            confidence_factors.append(95)
        elif predicted_slippage < 1.0:
            confidence_factors.append(85)
        elif predicted_slippage < 2.0:
            confidence_factors.append(75)
        else:
            confidence_factors.append(60)
        
        # Weighted average
        total_confidence = np.mean(confidence_factors)
        
        return total_confidence
    
    def _calculate_risk_score(self, opportunity, slippage_pred: Dict, 
                             market_impact: Dict) -> float:
        """
        Calculate risk score (0-1, lower is better)
        
        Risk factors:
        - High slippage
        - Low liquidity
        - Large trade size relative to liquidity
        - Price volatility
        """
        risk_factors = []
        
        # Risk 1: Slippage risk
        slippage = slippage_pred.get('predicted_slippage_pct', 0)
        slippage_risk = min(1.0, slippage / 5.0)  # 5% slippage = max risk
        risk_factors.append(slippage_risk)
        
        # Risk 2: Liquidity risk
        liquidity = opportunity.liquidity_available
        if liquidity < 50000:
            liquidity_risk = 0.8
        elif liquidity < 100000:
            liquidity_risk = 0.5
        elif liquidity < 500000:
            liquidity_risk = 0.3
        else:
            liquidity_risk = 0.1
        risk_factors.append(liquidity_risk)
        
        # Risk 3: Size risk (trade size vs liquidity)
        trade_size = opportunity.optimal_amount * opportunity.buy_price
        liquidity_usage = trade_size / max(liquidity, 1)
        size_risk = min(1.0, liquidity_usage * 2)  # 50% usage = max risk
        risk_factors.append(size_risk)
        
        # Risk 4: Gas cost risk (high gas relative to profit)
        gas_ratio = opportunity.estimated_gas_cost_usd / max(opportunity.net_profit_usd, 0.01)
        gas_risk = min(1.0, gas_ratio)
        risk_factors.append(gas_risk)
        
        # Average risk
        total_risk = np.mean(risk_factors)
        
        return total_risk
    
    def _final_validation_checks(self, opportunity, net_profit_analysis: Dict) -> Dict:
        """Final sanity checks before execution"""
        failures = []
        warnings = []
        
        # Check 1: Profit must cover gas with margin
        gas_cost = net_profit_analysis['gas_cost']
        net_profit = net_profit_analysis['net_profit_after_all_costs']
        
        if net_profit < gas_cost * 2:
            warnings.append(f"Profit barely covers gas (${net_profit:.6f} vs ${gas_cost:.6f} gas)")
        
        # Check 2: Reasonable profit margin
        profit_margin = net_profit_analysis['profit_margin_pct']
        if profit_margin < 5:
            failures.append(f"Profit margin too thin: {profit_margin:.1f}%")
        
        # Check 3: Trade size is reasonable
        if hasattr(opportunity, 'optimal_amount'):
            if opportunity.optimal_amount <= 0:
                failures.append("Invalid trade size: 0")
        
        # Check 4: Prices are sane
        if hasattr(opportunity, 'buy_price') and hasattr(opportunity, 'sell_price'):
            if opportunity.buy_price <= 0 or opportunity.sell_price <= 0:
                failures.append("Invalid prices detected")
            
            if opportunity.sell_price <= opportunity.buy_price:
                failures.append("Sell price not higher than buy price")
        
        return {
            'passed': len(failures) == 0,
            'failures': failures,
            'warnings': warnings
        }
    
    def record_execution_result(self, decision: ExecutionDecision, 
                               actual_profit: float, success: bool):
        """
        Record execution result for accuracy tracking
        
        This is how we learn and adapt thresholds
        """
        result = {
            'timestamp': time.time(),
            'expected_profit': decision.expected_net_profit,
            'actual_profit': actual_profit,
            'confidence': decision.confidence,
            'risk_score': decision.risk_score,
            'success': success,
            'profitable': actual_profit > 0
        }
        
        self.execution_history.append(result)
        
        if decision.should_execute:
            self.total_executions += 1
            
            if success and actual_profit > 0:
                self.successful_executions += 1
                cprint(f"✅ Execution successful: ${actual_profit:.6f} profit", "green")
            else:
                self.failed_executions += 1
                cprint(f"❌ Execution failed: ${actual_profit:.6f}", "red")
        
        # Adapt thresholds based on accuracy
        self._adapt_thresholds()
    
    def _get_recent_accuracy(self) -> float:
        """Get recent execution accuracy %"""
        if not self.execution_history:
            return 0.0
        
        recent = list(self.execution_history)[-20:]  # Last 20
        successful = len([r for r in recent if r['success'] and r['profitable']])
        
        return (successful / len(recent)) * 100
    
    def _adapt_thresholds(self):
        """
        Adapt validation thresholds based on performance
        
        If accuracy < 80%: Increase thresholds (be more conservative)
        If accuracy > 90%: Decrease thresholds (be more aggressive)
        """
        if len(self.execution_history) < 10:
            return  # Need more data
        
        current_accuracy = self._get_recent_accuracy()
        
        cprint(f"\n📊 Current Accuracy: {current_accuracy:.1f}% (Target: {self.min_accuracy_target}%)", "cyan")
        
        if current_accuracy < self.min_accuracy_target:
            # Too many failures - be more conservative
            old_confidence = self.min_confidence
            self.min_confidence = min(95.0, self.min_confidence + 2.0)
            self.min_net_profit_usd *= 1.2
            self.max_risk_score *= 0.9
            
            cprint(f"⚠️ Accuracy below target - INCREASING thresholds", "yellow")
            cprint(f"   Confidence: {old_confidence:.1f}% → {self.min_confidence:.1f}%", "yellow")
            
        elif current_accuracy > 90.0:
            # Very high accuracy - can be more aggressive
            old_confidence = self.min_confidence
            self.min_confidence = max(75.0, self.min_confidence - 1.0)
            self.min_net_profit_usd *= 0.95
            self.max_risk_score = min(0.5, self.max_risk_score * 1.05)
            
            cprint(f"✅ High accuracy - DECREASING thresholds", "green")
            cprint(f"   Confidence: {old_confidence:.1f}% → {self.min_confidence:.1f}%", "green")
    
    def get_validation_stats(self) -> Dict:
        """Get validation statistics"""
        accuracy = (self.successful_executions / max(1, self.total_executions)) * 100
        execution_rate = (self.total_executions / max(1, self.total_validations)) * 100
        
        return {
            'total_validations': self.total_validations,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'accuracy_pct': accuracy,
            'execution_rate_pct': execution_rate,
            'current_min_confidence': self.min_confidence,
            'current_min_profit': self.min_net_profit_usd,
            'current_max_risk': self.max_risk_score,
            'meets_target': accuracy >= self.min_accuracy_target
        }
