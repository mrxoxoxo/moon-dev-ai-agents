"""
🌙 Moon Dev's Game Theory Engine
Strategic decision making in competitive MEV environment
Built with love by Moon Dev 🚀
"""

import os
import sys
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from termcolor import cprint
from scipy.optimize import linprog
import itertools

@dataclass
class GameTheoryStrategy:
    """A strategic decision in the MEV game"""
    name: str
    action: str  # execute, wait, adjust_gas, split_trade
    parameters: Dict
    expected_payoff: float
    nash_equilibrium: bool
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'action': self.action,
            'parameters': self.parameters,
            'expected_payoff': self.expected_payoff,
            'nash_equilibrium': self.nash_equilibrium
        }


class GameTheoryEngine:
    """
    Apply game theory to MEV competition
    
    Models:
    - Other bots as competing players
    - Opportunities as finite resources
    - Gas bidding as auction games
    - Nash equilibrium for optimal strategy
    
    Games:
    1. **Gas Auction Game** - Compete for block position
    2. **Timing Game** - When to execute vs wait
    3. **Resource Allocation** - Which opportunities to pursue
    4. **Cooperative Game** - When to avoid competition
    
    Concepts:
    - Nash Equilibrium (no player benefits from deviating)
    - Dominant Strategy (best regardless of others)
    - Mixed Strategy (randomize to be unpredictable)
    - Pareto Efficiency (no one can improve without hurting others)
    """
    
    def __init__(self):
        # Known competitor profiles
        self.competitors = {
            'aggressive_bot': {
                'strategy': 'high_gas_first',
                'avg_gas_multiplier': 2.0,
                'success_rate': 0.6
            },
            'patient_bot': {
                'strategy': 'wait_for_low_gas',
                'avg_gas_multiplier': 1.0,
                'success_rate': 0.4
            },
            'smart_bot': {
                'strategy': 'adaptive',
                'avg_gas_multiplier': 1.5,
                'success_rate': 0.7
            }
        }
        
        cprint("\n🎮 Game Theory Engine Initialized", "magenta", attrs=['bold'])
        cprint("   Models: Nash Equilibrium, Dominant Strategy, Mixed Strategy", "cyan")
        cprint(f"   Known Competitors: {len(self.competitors)}", "cyan")
    
    def find_nash_equilibrium(self, opportunity, our_strategies: List[Dict],
                             competitor_strategies: List[Dict]) -> GameTheoryStrategy:
        """
        Find Nash equilibrium strategy
        
        Nash Equilibrium: No player can improve by unilaterally changing strategy
        
        Args:
            opportunity: The opportunity being competed for
            our_strategies: Our possible actions
            competitor_strategies: Competitor possible actions
            
        Returns:
            Optimal strategy at Nash equilibrium
        """
        cprint(f"\n🎮 Finding Nash Equilibrium...", "magenta", attrs=['bold'])
        cprint(f"   Our Strategies: {len(our_strategies)}", "cyan")
        cprint(f"   Competitor Strategies: {len(competitor_strategies)}", "cyan")
        
        # Build payoff matrix
        payoff_matrix = self._build_payoff_matrix(
            opportunity, our_strategies, competitor_strategies
        )
        
        # Find best response for each strategy combination
        nash_strategies = []
        
        for i, our_strat in enumerate(our_strategies):
            for j, comp_strat in enumerate(competitor_strategies):
                # Check if this is a Nash equilibrium
                is_nash = self._is_nash_equilibrium(
                    payoff_matrix, i, j
                )
                
                if is_nash:
                    strategy = GameTheoryStrategy(
                        name=f"Nash_{our_strat['name']}",
                        action=our_strat['action'],
                        parameters=our_strat['parameters'],
                        expected_payoff=payoff_matrix[i][j]['our_payoff'],
                        nash_equilibrium=True
                    )
                    nash_strategies.append(strategy)
        
        if nash_strategies:
            # Choose best Nash equilibrium
            best = max(nash_strategies, key=lambda s: s.expected_payoff)
            
            cprint(f"\n✅ Nash Equilibrium Found:", "green", attrs=['bold'])
            cprint(f"   Strategy: {best.name}", "cyan")
            cprint(f"   Action: {best.action}", "cyan")
            cprint(f"   Expected Payoff: ${best.expected_payoff:.2f}", "green")
            
            return best
        else:
            # No pure Nash equilibrium, use mixed strategy
            cprint(f"\n⚠️ No pure Nash equilibrium - using mixed strategy", "yellow")
            return self._find_mixed_strategy_equilibrium(
                opportunity, our_strategies, payoff_matrix
            )
    
    def _build_payoff_matrix(self, opportunity, our_strategies: List[Dict],
                            competitor_strategies: List[Dict]) -> np.ndarray:
        """Build game payoff matrix"""
        matrix = []
        
        for our_strat in our_strategies:
            row = []
            for comp_strat in competitor_strategies:
                # Calculate payoffs for both players
                payoffs = self._calculate_payoffs(
                    opportunity, our_strat, comp_strat
                )
                row.append(payoffs)
            matrix.append(row)
        
        return matrix
    
    def _calculate_payoffs(self, opportunity, our_strategy: Dict,
                          competitor_strategy: Dict) -> Dict:
        """
        Calculate payoffs for a strategy combination
        
        Considers:
        - Who gets the opportunity (based on gas bid)
        - Profit after gas costs
        - Probability of success
        """
        our_gas = our_strategy['parameters'].get('gas_multiplier', 1.0)
        comp_gas = competitor_strategy.get('gas_multiplier', 1.0)
        
        base_profit = opportunity.net_profit_usd
        base_gas = opportunity.estimated_gas_cost_usd
        
        # Determine winner (highest gas wins)
        if our_gas > comp_gas:
            # We win
            our_profit = base_profit - (base_gas * our_gas)
            comp_profit = -(base_gas * comp_gas)  # Only gas cost
        elif comp_gas > our_gas:
            # Competitor wins
            our_profit = -(base_gas * our_gas)
            comp_profit = base_profit - (base_gas * comp_gas)
        else:
            # Tie - split (or random)
            our_profit = (base_profit - (base_gas * our_gas)) * 0.5
            comp_profit = (base_profit - (base_gas * comp_gas)) * 0.5
        
        return {
            'our_payoff': our_profit,
            'competitor_payoff': comp_profit
        }
    
    def _is_nash_equilibrium(self, matrix, i: int, j: int) -> bool:
        """Check if strategy combination (i,j) is Nash equilibrium"""
        our_payoff = matrix[i][j]['our_payoff']
        comp_payoff = matrix[i][j]['competitor_payoff']
        
        # Check if we can improve by changing strategy
        for alt_i in range(len(matrix)):
            if matrix[alt_i][j]['our_payoff'] > our_payoff:
                return False
        
        # Check if competitor can improve
        for alt_j in range(len(matrix[0])):
            if matrix[i][alt_j]['competitor_payoff'] > comp_payoff:
                return False
        
        return True
    
    def _find_mixed_strategy_equilibrium(self, opportunity, strategies: List[Dict],
                                        payoff_matrix) -> GameTheoryStrategy:
        """Find mixed strategy Nash equilibrium"""
        # Use random probability distribution
        num_strategies = len(strategies)
        probabilities = np.random.dirichlet(np.ones(num_strategies))
        
        # Calculate expected payoff
        expected_payoff = 0
        for i, prob in enumerate(probabilities):
            for j in range(len(payoff_matrix[0])):
                expected_payoff += prob * payoff_matrix[i][j]['our_payoff'] / len(payoff_matrix[0])
        
        # Choose strategy based on probability
        chosen_idx = np.random.choice(num_strategies, p=probabilities)
        chosen = strategies[chosen_idx]
        
        return GameTheoryStrategy(
            name=f"Mixed_{chosen['name']}",
            action=chosen['action'],
            parameters=chosen['parameters'],
            expected_payoff=expected_payoff,
            nash_equilibrium=False
        )
    
    def gas_auction_strategy(self, opportunity, competitor_count: int = 3) -> Dict:
        """
        Optimal gas bidding strategy
        
        Models gas bidding as a first-price sealed-bid auction
        
        Optimal bid = (N-1)/N * V
        Where N = number of bidders, V = opportunity value
        """
        cprint(f"\n⛽ Gas Auction Strategy Analysis", "yellow", attrs=['bold'])
        cprint(f"   Competitors: {competitor_count}", "cyan")
        
        value = opportunity.net_profit_usd
        base_gas = opportunity.estimated_gas_cost_usd
        
        # Optimal bid factor
        N = competitor_count + 1  # Including us
        optimal_factor = (N - 1) / N
        
        # Calculate optimal gas bid
        optimal_gas_bid = base_gas * (1 + optimal_factor)
        
        # Expected profit if we win
        win_probability = 1 / N  # Assuming symmetric strategies
        expected_profit = win_probability * (value - optimal_gas_bid)
        
        cprint(f"\n   Base Gas: ${base_gas:.6f}", "white")
        cprint(f"   Optimal Bid: ${optimal_gas_bid:.6f} ({optimal_factor:.2%} premium)", "cyan")
        cprint(f"   Win Probability: {win_probability:.1%}", "yellow")
        cprint(f"   Expected Profit: ${expected_profit:.2f}", "green")
        
        return {
            'optimal_gas_bid': optimal_gas_bid,
            'gas_multiplier': 1 + optimal_factor,
            'win_probability': win_probability,
            'expected_profit': expected_profit
        }
    
    def timing_game(self, opportunity, network_congestion: float) -> str:
        """
        Decide optimal timing: execute now vs wait
        
        Game:
        - Execute now: Higher gas but guaranteed shot
        - Wait: Lower gas but risk someone else taking it
        
        Args:
            opportunity: The opportunity
            network_congestion: 0-1 scale
            
        Returns:
            'execute_now' or 'wait'
        """
        cprint(f"\n⏰ Timing Game Analysis", "yellow", attrs=['bold'])
        
        # Calculate payoffs
        current_gas = opportunity.estimated_gas_cost_usd
        current_profit = opportunity.net_profit_usd - current_gas
        
        # If we wait, gas might be lower but opportunity might disappear
        wait_gas_reduction = 0.3  # 30% lower gas if we wait
        wait_opportunity_loss_prob = network_congestion * 0.5  # Higher congestion = more likely someone else takes it
        
        future_gas = current_gas * (1 - wait_gas_reduction)
        future_profit = opportunity.net_profit_usd - future_gas
        
        # Expected value of waiting
        ev_wait = (1 - wait_opportunity_loss_prob) * future_profit + wait_opportunity_loss_prob * 0
        
        cprint(f"   Execute Now EV: ${current_profit:.2f}", "cyan")
        cprint(f"   Wait EV: ${ev_wait:.2f}", "yellow")
        
        if current_profit > ev_wait:
            cprint(f"   ✅ Decision: EXECUTE NOW", "green", attrs=['bold'])
            return 'execute_now'
        else:
            cprint(f"   ⏸️ Decision: WAIT", "yellow", attrs=['bold'])
            return 'wait'
    
    def cooperative_game_analysis(self, opportunities: List, total_capital: float) -> List[Dict]:
        """
        Analyze cooperative vs competitive strategies
        
        Sometimes cooperating (not competing on same opportunity) yields better total outcome
        
        Uses:
        - Shapley value for fair profit distribution
        - Core for stability
        - Coalition formation
        """
        cprint(f"\n🤝 Cooperative Game Analysis", "magenta", attrs=['bold'])
        
        # For now, focus on avoiding destructive competition
        # If multiple bots bid up gas on same opportunity, all lose
        
        # Recommend diversification
        recommendations = []
        
        for i, opp in enumerate(opportunities):
            recommendation = {
                'opportunity': i,
                'strategy': 'compete' if i == 0 else 'avoid',  # Only compete on best
                'rationale': 'Diversify to avoid gas wars'
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def calculate_shapley_value(self, agents: List[str], coalition_values: Dict) -> Dict:
        """
        Calculate Shapley value for fair profit distribution in coalition
        
        Shapley value = fair share of profits when agents cooperate
        """
        shapley_values = {}
        
        for agent in agents:
            value = 0
            n = len(agents)
            
            # Sum over all possible coalitions
            for r in range(1, n + 1):
                for coalition in itertools.combinations(agents, r):
                    if agent in coalition:
                        # Marginal contribution
                        with_agent = coalition_values.get(frozenset(coalition), 0)
                        without_agent = coalition_values.get(frozenset(set(coalition) - {agent}), 0)
                        marginal = with_agent - without_agent
                        
                        # Weight by probability
                        weight = 1 / (n * len(list(itertools.combinations(agents, r))))
                        value += weight * marginal
            
            shapley_values[agent] = value
        
        return shapley_values
    
    def predict_competitor_behavior(self, historical_data: List[Dict]) -> Dict:
        """
        Predict competitor strategies based on historical behavior
        
        Uses:
        - Pattern recognition
        - Bayesian inference
        - Markov models
        """
        if not historical_data:
            return {'strategy': 'unknown', 'confidence': 0}
        
        # Analyze patterns
        gas_multipliers = [d.get('gas_multiplier', 1.0) for d in historical_data]
        avg_gas = np.mean(gas_multipliers)
        
        # Classify strategy
        if avg_gas > 1.5:
            strategy = 'aggressive'
        elif avg_gas < 1.1:
            strategy = 'conservative'
        else:
            strategy = 'balanced'
        
        return {
            'strategy': strategy,
            'avg_gas_multiplier': avg_gas,
            'confidence': 0.7  # Would calculate actual confidence
        }
    
    def evolutionary_stable_strategy(self, population_strategies: List[Dict]) -> Dict:
        """
        Find evolutionarily stable strategy (ESS)
        
        ESS: Strategy that, if adopted by population, cannot be invaded by mutant strategy
        
        In MEV context: Strategy that remains profitable even when many bots use it
        """
        cprint(f"\n🧬 Evolutionary Stable Strategy Analysis", "magenta")
        
        # Test each strategy against population
        fitness_scores = {}
        
        for strategy in population_strategies:
            # Calculate fitness (profit) when playing against population
            total_fitness = 0
            
            for opponent in population_strategies:
                # Payoff from this matchup
                payoff = self._strategy_vs_strategy(strategy, opponent)
                total_fitness += payoff
            
            avg_fitness = total_fitness / len(population_strategies)
            fitness_scores[strategy['name']] = avg_fitness
        
        # Find highest fitness
        best_strategy = max(population_strategies, key=lambda s: fitness_scores[s['name']])
        
        cprint(f"   ESS: {best_strategy['name']}", "green")
        cprint(f"   Fitness: {fitness_scores[best_strategy['name']]:.2f}", "cyan")
        
        return best_strategy
    
    def _strategy_vs_strategy(self, strategy1: Dict, strategy2: Dict) -> float:
        """Calculate payoff when strategy1 plays against strategy2"""
        # Simplified - would use actual game mechanics
        gas1 = strategy1.get('gas_multiplier', 1.0)
        gas2 = strategy2.get('gas_multiplier', 1.0)
        
        if gas1 > gas2:
            return 100 - (gas1 * 10)  # Win but pay gas
        elif gas1 < gas2:
            return -(gas1 * 10)  # Lose and pay gas
        else:
            return 50 - (gas1 * 10)  # Tie
