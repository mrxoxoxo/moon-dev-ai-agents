"""
🌙 Moon Dev's Flashloan Reinforcement Learning Engine
Agents learn from mistakes and successes using RL
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
import random
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from termcolor import cprint
from collections import deque
import pickle

@dataclass
class TradeExperience:
    """A single trade experience for learning"""
    # State (before trade)
    state: Dict
    
    # Action taken
    action: Dict
    
    # Reward received
    reward: float
    
    # Next state (after trade)
    next_state: Dict
    
    # Was it terminal (agent died)?
    terminal: bool
    
    # Timestamp
    timestamp: float
    
    def to_dict(self) -> Dict:
        return {
            'state': self.state,
            'action': self.action,
            'reward': self.reward,
            'next_state': self.next_state,
            'terminal': self.terminal,
            'timestamp': self.timestamp
        }


class ReinforcementLearner:
    """
    Reinforcement Learning system for flashloan arbitrage
    
    Uses Q-Learning with experience replay to learn optimal trading strategies
    """
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.95, 
                 epsilon: float = 0.2, epsilon_decay: float = 0.995):
        """
        Initialize RL system
        
        Args:
            learning_rate: How fast to learn (alpha)
            discount_factor: Future reward importance (gamma)
            epsilon: Exploration rate (0-1)
            epsilon_decay: How fast to reduce exploration
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = 0.05  # Always keep some exploration
        
        # Q-table: state-action values
        # For continuous states, we'll use discretization and approximation
        self.q_table: Dict[str, Dict[str, float]] = {}
        
        # Experience replay buffer
        self.memory = deque(maxlen=10000)
        self.batch_size = 32
        
        # Learning statistics
        self.total_experiences = 0
        self.total_rewards = 0.0
        self.episodes = 0
        
        # State feature extractors
        self.state_features = [
            'profit_percent',
            'liquidity_ratio',
            'dex_diversity',
            'gas_cost_ratio',
            'recent_success_rate'
        ]
        
        cprint("\n🧠 Reinforcement Learning Engine Initialized", "magenta", attrs=['bold'])
        cprint(f"   Learning Rate: {self.learning_rate}", "cyan")
        cprint(f"   Discount Factor: {self.discount_factor}", "cyan")
        cprint(f"   Exploration Rate: {self.epsilon}", "cyan")
        cprint(f"   Memory Size: {len(self.memory)}/{self.memory.maxlen}", "cyan")
    
    def extract_state_features(self, opportunity, agent_stats: Dict) -> Dict:
        """
        Extract state features from current situation
        
        State represents the current trading environment and agent status
        """
        state = {
            # Opportunity features
            'profit_percent': self._discretize(opportunity.profit_percent, [0.5, 1.0, 2.0, 5.0]),
            'liquidity_ratio': self._discretize(opportunity.liquidity_available / 100000, [0.1, 0.5, 1.0, 5.0]),
            'gas_cost_ratio': self._discretize(opportunity.estimated_gas_cost_usd / opportunity.estimated_profit_usd if opportunity.estimated_profit_usd > 0 else 1, [0.1, 0.2, 0.5, 1.0]),
            'net_profit_usd': self._discretize(opportunity.net_profit_usd, [0.01, 0.1, 1.0, 10.0]),
            
            # DEX features
            'dex_diversity': len(set([opportunity.buy_dex, opportunity.sell_dex])),
            'buy_dex': opportunity.buy_dex,
            'sell_dex': opportunity.sell_dex,
            
            # Agent performance features
            'recent_success_rate': self._discretize(agent_stats.get('success_rate', 0), [0, 25, 50, 75]),
            'consecutive_failures': min(agent_stats.get('consecutive_failures', 0), 3),
            'total_attempts': min(agent_stats.get('total_attempts', 0), 10),
            
            # Time features
            'time_of_day': (int(time.time()) % 86400) // 3600,  # Hour of day
        }
        
        return state
    
    def _discretize(self, value: float, thresholds: List[float]) -> int:
        """Discretize continuous value into buckets"""
        for i, threshold in enumerate(thresholds):
            if value < threshold:
                return i
        return len(thresholds)
    
    def _state_to_key(self, state: Dict) -> str:
        """Convert state dict to hashable key for Q-table"""
        # Use most important features for key
        key_features = [
            state.get('profit_percent', 0),
            state.get('liquidity_ratio', 0),
            state.get('recent_success_rate', 0),
            state.get('consecutive_failures', 0),
            state.get('buy_dex', 'unknown'),
            state.get('sell_dex', 'unknown')
        ]
        return str(tuple(key_features))
    
    def choose_action(self, state: Dict, available_actions: List[str]) -> Tuple[str, bool]:
        """
        Choose action using epsilon-greedy policy
        
        Args:
            state: Current state features
            available_actions: List of possible actions
            
        Returns:
            (action, is_exploration): Chosen action and whether it was exploratory
        """
        # Epsilon-greedy: explore vs exploit
        if random.random() < self.epsilon:
            # EXPLORE: Random action
            action = random.choice(available_actions)
            return action, True
        else:
            # EXPLOIT: Best known action
            state_key = self._state_to_key(state)
            
            if state_key not in self.q_table:
                self.q_table[state_key] = {a: 0.0 for a in available_actions}
            
            # Get Q-values for all actions in this state
            q_values = self.q_table[state_key]
            
            # Choose action with highest Q-value
            best_action = max(available_actions, key=lambda a: q_values.get(a, 0.0))
            return best_action, False
    
    def calculate_reward(self, trade_result: Dict) -> float:
        """
        Calculate reward from trade result
        
        Reward structure:
        - Positive profit = positive reward (scaled)
        - Loss = negative reward (scaled)
        - Failed trade = penalty
        - Death = large penalty
        """
        success = trade_result.get('success', False)
        profit = trade_result.get('profit', 0)
        
        if not success:
            # Failed trade penalty
            reward = -1.0
            
            # Extra penalty if agent died
            if trade_result.get('agent_died', False):
                reward = -10.0
        else:
            # Successful trade
            if profit > 0:
                # Scale profit to reasonable reward range
                # $1 profit = +10 reward, $10 profit = +100 reward
                reward = profit * 10
                
                # Bonus for efficiency (high profit relative to gas)
                gas_cost = trade_result.get('gas_cost', 0.01)
                if gas_cost > 0:
                    efficiency = profit / gas_cost
                    if efficiency > 10:
                        reward *= 1.5  # 50% bonus for efficient trades
            else:
                # Trade succeeded but no profit
                reward = -0.5
        
        return reward
    
    def learn_from_experience(self, experience: TradeExperience):
        """
        Update Q-values from a single experience using Q-learning
        
        Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        """
        state_key = self._state_to_key(experience.state)
        next_state_key = self._state_to_key(experience.next_state)
        action = experience.action.get('type', 'execute')
        
        # Initialize Q-table entries if needed
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        if action not in self.q_table[state_key]:
            self.q_table[state_key][action] = 0.0
        
        # Current Q-value
        current_q = self.q_table[state_key][action]
        
        # Calculate target Q-value
        if experience.terminal:
            # No future rewards if terminal state
            target_q = experience.reward
        else:
            # Q-learning update with future rewards
            if next_state_key not in self.q_table or not self.q_table[next_state_key]:
                max_next_q = 0.0
            else:
                max_next_q = max(self.q_table[next_state_key].values())
            
            target_q = experience.reward + self.discount_factor * max_next_q
        
        # Update Q-value
        new_q = current_q + self.learning_rate * (target_q - current_q)
        self.q_table[state_key][action] = new_q
        
        # Update statistics
        self.total_experiences += 1
        self.total_rewards += experience.reward
        
        # Decay exploration rate
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
    
    def store_experience(self, experience: TradeExperience):
        """Store experience in replay buffer"""
        self.memory.append(experience)
    
    def replay_training(self):
        """
        Experience replay: Learn from random batch of past experiences
        
        This helps break correlation between consecutive experiences
        """
        if len(self.memory) < self.batch_size:
            return
        
        # Sample random batch
        batch = random.sample(self.memory, self.batch_size)
        
        # Learn from each experience in batch
        for experience in batch:
            self.learn_from_experience(experience)
        
        cprint(f"🧠 Replay training on {self.batch_size} experiences", "magenta")
    
    def get_value_estimate(self, state: Dict) -> float:
        """Get estimated value of a state (max Q-value)"""
        state_key = self._state_to_key(state)
        
        if state_key not in self.q_table or not self.q_table[state_key]:
            return 0.0
        
        return max(self.q_table[state_key].values())
    
    def get_action_values(self, state: Dict) -> Dict[str, float]:
        """Get Q-values for all actions in a state"""
        state_key = self._state_to_key(state)
        
        if state_key not in self.q_table:
            return {}
        
        return self.q_table[state_key].copy()
    
    def save_model(self, filepath: str):
        """Save learned Q-table and parameters"""
        model_data = {
            'q_table': self.q_table,
            'epsilon': self.epsilon,
            'total_experiences': self.total_experiences,
            'total_rewards': self.total_rewards,
            'episodes': self.episodes,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        cprint(f"\n💾 Model saved to {filepath}", "green")
        cprint(f"   Experiences: {self.total_experiences}", "cyan")
        cprint(f"   Q-table size: {len(self.q_table)} states", "cyan")
    
    def load_model(self, filepath: str):
        """Load previously learned Q-table"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.q_table = model_data.get('q_table', {})
            self.epsilon = model_data.get('epsilon', self.epsilon)
            self.total_experiences = model_data.get('total_experiences', 0)
            self.total_rewards = model_data.get('total_rewards', 0.0)
            self.episodes = model_data.get('episodes', 0)
            
            cprint(f"\n📥 Model loaded from {filepath}", "green")
            cprint(f"   Experiences: {self.total_experiences}", "cyan")
            cprint(f"   Q-table size: {len(self.q_table)} states", "cyan")
            cprint(f"   Exploration rate: {self.epsilon:.3f}", "cyan")
            
        except Exception as e:
            cprint(f"❌ Failed to load model: {str(e)}", "red")
    
    def get_learning_stats(self) -> Dict:
        """Get learning statistics"""
        avg_reward = self.total_rewards / max(1, self.total_experiences)
        
        return {
            'total_experiences': self.total_experiences,
            'total_rewards': self.total_rewards,
            'avg_reward': avg_reward,
            'episodes': self.episodes,
            'epsilon': self.epsilon,
            'q_table_size': len(self.q_table),
            'memory_size': len(self.memory),
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor
        }
    
    def reset_episode(self):
        """Mark end of episode for statistics"""
        self.episodes += 1


class AdaptiveGeneticLearner:
    """
    Combines genetic algorithms with RL for agent evolution
    
    Agents that learn faster get to reproduce more
    """
    
    def __init__(self):
        """Initialize adaptive learner"""
        self.population_learning_rates: Dict[str, float] = {}
        self.population_performance: Dict[str, List[float]] = {}
        
    def track_agent_learning(self, agent_id: str, learning_rate: float):
        """Track how fast an agent is learning"""
        if agent_id not in self.population_performance:
            self.population_performance[agent_id] = []
        
        self.population_learning_rates[agent_id] = learning_rate
    
    def record_performance(self, agent_id: str, reward: float):
        """Record agent performance over time"""
        if agent_id not in self.population_performance:
            self.population_performance[agent_id] = []
        
        self.population_performance[agent_id].append(reward)
    
    def get_learning_rate(self, agent_id: str) -> float:
        """
        Calculate learning rate based on recent performance
        
        Fast learners = agents that improve quickly
        """
        if agent_id not in self.population_performance:
            return 0.0
        
        performance = self.population_performance[agent_id]
        
        if len(performance) < 2:
            return 0.0
        
        # Calculate improvement rate (slope of recent performance)
        recent = performance[-10:]  # Last 10 trades
        if len(recent) < 2:
            return 0.0
        
        # Simple linear regression slope
        x = np.arange(len(recent))
        y = np.array(recent)
        slope = np.polyfit(x, y, 1)[0]
        
        return float(slope)
    
    def select_parents_for_reproduction(self, agent_ids: List[str], num_parents: int = 2) -> List[str]:
        """
        Select best learning agents for reproduction
        
        Fitness = combination of:
        1. Total rewards
        2. Learning rate (improvement speed)
        3. Consistency
        """
        fitness_scores = {}
        
        for agent_id in agent_ids:
            if agent_id not in self.population_performance:
                fitness_scores[agent_id] = 0.0
                continue
            
            performance = self.population_performance[agent_id]
            
            # Total reward
            total_reward = sum(performance)
            
            # Learning rate (improvement)
            learning_rate = self.get_learning_rate(agent_id)
            
            # Consistency (low variance is good)
            consistency = -np.var(performance) if len(performance) > 1 else 0
            
            # Combined fitness
            fitness = total_reward * 0.5 + learning_rate * 100 * 0.3 + consistency * 0.2
            fitness_scores[agent_id] = fitness
        
        # Select top performers
        sorted_agents = sorted(agent_ids, key=lambda x: fitness_scores.get(x, 0), reverse=True)
        
        return sorted_agents[:num_parents]
