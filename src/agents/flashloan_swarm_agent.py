"""
🌙 Moon Dev's Flashloan Swarm Agent
Evolutionary self-improving flashloan arbitrage swarm
Built with love by Moon Dev 🚀

Inspired by moon-dev-ai-agents-for-trading architecture
"""

import os
import sys
import json
import time
import signal
from typing import Dict, List, Optional
from datetime import datetime
from termcolor import cprint
from pathlib import Path

# Import swarm components
from flashloan_core import FlashloanCore, ArbitrageOpportunity
from flashloan_baby_agent import FlashloanBabyAgent, AgentGenetics
from flashloan_discovery import FlashloanDiscovery
from flashloan_learning import ReinforcementLearner, AdaptiveGeneticLearner, TradeExperience
from flashloan_slippage import SlippagePredictor

class FlashloanSwarm:
    """
    Evolutionary flashloan arbitrage swarm orchestrator
    
    Features:
    1. Autonomous token/DEX discovery
    2. Self-evolving baby agents
    3. Reinforcement learning
    4. Slippage prediction & optimization
    5. MEV protection
    6. Agent lifecycle management (birth/death/evolution)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the swarm"""
        cprint("\n" + "="*80, "cyan")
        cprint("🌙 MOON DEV'S FLASHLOAN ARBITRAGE SWARM", "cyan", attrs=['bold'])
        cprint("="*80 + "\n", "cyan")
        
        self.config = config or self._default_config()
        
        # Initialize core systems
        cprint("🔧 Initializing core systems...", "yellow")
        self.core = FlashloanCore()
        self.discovery = FlashloanDiscovery()
        self.rl_learner = ReinforcementLearner(
            learning_rate=self.config['learning_rate'],
            discount_factor=self.config['discount_factor'],
            epsilon=self.config['exploration_rate']
        )
        self.genetic_learner = AdaptiveGeneticLearner()
        self.slippage_predictor = SlippagePredictor()
        
        # Agent population
        self.agents: Dict[str, FlashloanBabyAgent] = {}
        self.dead_agents: List[Dict] = []
        self.generation_history: List[Dict] = []
        
        # Discovered opportunities
        self.active_tokens: List[str] = []
        self.opportunity_history: List[Dict] = []
        
        # Swarm statistics
        self.total_agents_born = 0
        self.total_agents_died = 0
        self.total_trades_attempted = 0
        self.total_trades_successful = 0
        self.total_profit_usd = 0.0
        self.total_loss_usd = 0.0
        self.swarm_start_time = time.time()
        
        # Control flags
        self.running = False
        self.shutdown_requested = False
        
        # Setup data directory
        self.data_dir = Path("src/data/flashloan_swarm")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        cprint("\n✅ Flashloan Swarm initialized successfully!", "green", attrs=['bold'])
        self._print_config()
    
    def _default_config(self) -> Dict:
        """Default swarm configuration"""
        return {
            # Population settings
            'initial_population': 5,
            'max_population': 20,
            'min_population': 2,
            
            # Discovery settings
            'discover_tokens_every': 300,  # 5 minutes
            'max_tokens_tracked': 100,
            'min_token_liquidity': 10000,
            
            # Learning settings
            'learning_rate': 0.1,
            'discount_factor': 0.95,
            'exploration_rate': 0.3,
            'replay_training_every': 10,  # trades
            
            # Trading settings
            'min_profit_threshold': 0.5,  # 0.5%
            'max_slippage_tolerance': 2.0,  # 2%
            'scan_interval_seconds': 30,
            
            # Evolution settings
            'evolve_after_trades': 3,
            'reproduction_threshold': 5,  # Min trades before reproduction
            'min_profit_for_reproduction': 1.0,  # $1 minimum
            
            # Safety settings
            'max_consecutive_failures': 3,
            'emergency_shutdown_loss': 100.0,  # $100 loss triggers shutdown
            
            # Save settings
            'save_state_every': 300,  # 5 minutes
            'auto_save': True
        }
    
    def _print_config(self):
        """Print swarm configuration"""
        cprint("\n📋 Swarm Configuration:", "cyan")
        cprint(f"   Initial Population: {self.config['initial_population']}", "white")
        cprint(f"   Max Population: {self.config['max_population']}", "white")
        cprint(f"   Learning Rate: {self.config['learning_rate']}", "white")
        cprint(f"   Exploration Rate: {self.config['exploration_rate']}", "white")
        cprint(f"   Min Profit Threshold: {self.config['min_profit_threshold']}%", "white")
        cprint(f"   Max Slippage: {self.config['max_slippage_tolerance']}%", "white")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        cprint("\n\n⚠️ Shutdown signal received...", "yellow", attrs=['bold'])
        self.shutdown_requested = True
    
    def start(self):
        """Start the swarm"""
        cprint("\n🚀 Starting Flashloan Swarm...", "green", attrs=['bold'])
        
        self.running = True
        
        # Phase 1: Discovery
        self._initial_discovery()
        
        # Phase 2: Spawn initial population
        self._spawn_initial_population()
        
        # Phase 3: Main swarm loop
        self._swarm_loop()
    
    def _initial_discovery(self):
        """Initial token and DEX discovery"""
        cprint("\n🔍 Phase 1: Initial Discovery", "cyan", attrs=['bold'])
        
        # Discover new tokens
        discovered_tokens = self.discovery.discover_new_tokens(limit=self.config['max_tokens_tracked'])
        
        # Get top opportunities
        top_opportunities = self.discovery.get_top_opportunities(count=20)
        
        self.active_tokens = [t.address for t in top_opportunities]
        
        cprint(f"✅ Discovery complete: {len(self.active_tokens)} tokens ready for arbitrage", "green")
        
        # Discover DEXs
        discovered_dexs = self.discovery.discover_new_dexs()
        cprint(f"✅ Found {len(discovered_dexs)} DEX protocols", "green")
    
    def _spawn_initial_population(self):
        """Spawn initial agent population"""
        cprint(f"\n👶 Phase 2: Spawning Initial Population ({self.config['initial_population']} agents)", "cyan", attrs=['bold'])
        
        for i in range(self.config['initial_population']):
            self._spawn_agent()
            time.sleep(0.1)  # Small delay for readability
        
        cprint(f"✅ Population spawned: {len(self.agents)} agents alive", "green")
    
    def _spawn_agent(self, parent_genetics: Optional[AgentGenetics] = None) -> FlashloanBabyAgent:
        """Spawn a new baby agent"""
        agent = FlashloanBabyAgent(
            flashloan_core=self.core,
            tokens=self.active_tokens,
            genetics=parent_genetics
        )
        
        self.agents[agent.id] = agent
        self.total_agents_born += 1
        
        return agent
    
    def _swarm_loop(self):
        """Main swarm execution loop"""
        cprint(f"\n♾️  Phase 3: Swarm Loop Starting", "cyan", attrs=['bold'])
        cprint("   Press Ctrl+C to shutdown gracefully\n", "yellow")
        
        last_discovery = time.time()
        last_save = time.time()
        iteration = 0
        
        while self.running and not self.shutdown_requested:
            iteration += 1
            
            cprint(f"\n{'='*80}", "cyan")
            cprint(f"🔄 SWARM ITERATION #{iteration}", "cyan", attrs=['bold'])
            cprint(f"{'='*80}", "cyan")
            
            # 1. Periodic token discovery
            if time.time() - last_discovery > self.config['discover_tokens_every']:
                self._periodic_discovery()
                last_discovery = time.time()
            
            # 2. Each agent scans and executes
            self._agent_execution_cycle()
            
            # 3. Learning phase
            self._learning_phase()
            
            # 4. Evolution phase
            self._evolution_phase()
            
            # 5. Population management
            self._manage_population()
            
            # 6. Print statistics
            self._print_swarm_stats()
            
            # 7. Save state periodically
            if self.config['auto_save'] and time.time() - last_save > self.config['save_state_every']:
                self._save_swarm_state()
                last_save = time.time()
            
            # 8. Emergency shutdown check
            if self._check_emergency_shutdown():
                break
            
            # 9. Sleep before next iteration
            cprint(f"\n💤 Sleeping {self.config['scan_interval_seconds']}s before next iteration...", "yellow")
            time.sleep(self.config['scan_interval_seconds'])
        
        # Graceful shutdown
        self._shutdown()
    
    def _periodic_discovery(self):
        """Periodic token discovery"""
        cprint("\n🔍 Periodic Discovery Phase", "magenta")
        
        new_tokens = self.discovery.discover_new_tokens(limit=50)
        top_opps = self.discovery.get_top_opportunities(count=self.config['max_tokens_tracked'])
        
        # Update active tokens
        self.active_tokens = [t.address for t in top_opps]
        
        # Update all agents with new tokens
        for agent in self.agents.values():
            agent.tokens = self.active_tokens
        
        cprint(f"✅ Discovery updated: {len(self.active_tokens)} active tokens", "green")
    
    def _agent_execution_cycle(self):
        """Execute trading cycle for all agents"""
        cprint(f"\n🤖 Agent Execution Cycle ({len(self.agents)} agents)", "yellow", attrs=['bold'])
        
        alive_agents = [a for a in self.agents.values() if a.is_alive]
        
        for agent in alive_agents:
            try:
                # Agent scans and executes
                result = agent.scan_and_execute()
                
                self.total_trades_attempted += 1
                
                if result.get('success'):
                    self.total_trades_successful += 1
                    profit = result.get('profit', 0)
                    
                    if profit > 0:
                        self.total_profit_usd += profit
                    else:
                        self.total_loss_usd += abs(profit)
                
                # Create experience for RL
                if result.get('opportunity'):
                    self._create_learning_experience(agent, result)
                
                # Track genetic learning
                if result.get('success') and result.get('profit', 0) > 0:
                    self.genetic_learner.record_performance(agent.id, result['profit'])
                else:
                    self.genetic_learner.record_performance(agent.id, -1.0)
                
            except Exception as e:
                cprint(f"❌ Agent {agent.id} error: {str(e)}", "red")
                continue
    
    def _create_learning_experience(self, agent: FlashloanBabyAgent, result: Dict):
        """Create RL experience from trade result"""
        opportunity = result.get('opportunity', {})
        
        # Extract state
        state = self.rl_learner.extract_state_features(
            opportunity,
            agent.get_stats()
        )
        
        # Action taken
        action = {
            'type': 'execute' if result.get('success') else 'skip',
            'size': opportunity.get('optimal_amount', 0)
        }
        
        # Reward
        reward = self.rl_learner.calculate_reward({
            'success': result.get('success', False),
            'profit': result.get('profit', 0),
            'agent_died': not agent.is_alive
        })
        
        # Next state (after trade)
        next_state = self.rl_learner.extract_state_features(
            opportunity,
            agent.get_stats()
        )
        
        # Create experience
        experience = TradeExperience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            terminal=not agent.is_alive,
            timestamp=time.time()
        )
        
        # Store and learn
        self.rl_learner.store_experience(experience)
        self.rl_learner.learn_from_experience(experience)
    
    def _learning_phase(self):
        """Replay learning from past experiences"""
        if self.total_trades_attempted % self.config['replay_training_every'] == 0:
            cprint("\n🧠 Replay Learning Phase", "magenta")
            self.rl_learner.replay_training()
            
            stats = self.rl_learner.get_learning_stats()
            cprint(f"   Average Reward: {stats['avg_reward']:.2f}", "cyan")
            cprint(f"   Exploration Rate: {stats['epsilon']:.3f}", "cyan")
    
    def _evolution_phase(self):
        """Handle agent evolution and reproduction"""
        cprint("\n🧬 Evolution Phase", "magenta")
        
        alive_agents = [a for a in self.agents.values() if a.is_alive]
        
        # Check for agents ready to evolve
        for agent in alive_agents:
            if (agent.successful_attempts > 0 and 
                agent.successful_attempts % self.config['evolve_after_trades'] == 0):
                agent.evolve()
        
        # Reproduction: successful agents spawn children
        if len(alive_agents) < self.config['max_population']:
            eligible_parents = [
                a for a in alive_agents
                if (a.total_attempts >= self.config['reproduction_threshold'] and
                    a.total_profit_usd >= self.config['min_profit_for_reproduction'])
            ]
            
            if eligible_parents:
                # Select best parents using genetic learner
                parent_ids = [a.id for a in eligible_parents]
                best_parents = self.genetic_learner.select_parents_for_reproduction(
                    parent_ids,
                    num_parents=min(2, len(parent_ids))
                )
                
                if best_parents:
                    parent = next((a for a in eligible_parents if a.id == best_parents[0]), None)
                    if parent:
                        child = parent.spawn_child()
                        self.agents[child.id] = child
                        self.total_agents_born += 1
    
    def _manage_population(self):
        """Manage population size and remove dead agents"""
        # Remove dead agents from active population
        dead_ids = [agent_id for agent_id, agent in self.agents.items() if not agent.is_alive]
        
        for agent_id in dead_ids:
            dead_agent = self.agents.pop(agent_id)
            self.dead_agents.append(dead_agent.to_dict())
            self.total_agents_died += 1
        
        # If population too low, spawn new agents
        alive_count = len([a for a in self.agents.values() if a.is_alive])
        
        if alive_count < self.config['min_population']:
            needed = self.config['min_population'] - alive_count
            cprint(f"\n⚠️ Population too low ({alive_count}), spawning {needed} new agents", "yellow")
            
            for _ in range(needed):
                self._spawn_agent()
    
    def _print_swarm_stats(self):
        """Print swarm statistics"""
        alive_agents = [a for a in self.agents.values() if a.is_alive]
        
        runtime = time.time() - self.swarm_start_time
        net_profit = self.total_profit_usd - self.total_loss_usd
        success_rate = (self.total_trades_successful / max(1, self.total_trades_attempted)) * 100
        
        cprint("\n" + "="*80, "cyan")
        cprint("📊 SWARM STATISTICS", "cyan", attrs=['bold'])
        cprint("="*80, "cyan")
        
        cprint(f"\n🕐 Runtime: {runtime/60:.1f} minutes", "white")
        
        cprint(f"\n👥 Population:", "yellow")
        cprint(f"   Alive: {len(alive_agents)}", "green")
        cprint(f"   Dead: {self.total_agents_died}", "red")
        cprint(f"   Total Born: {self.total_agents_born}", "cyan")
        
        cprint(f"\n💼 Trading:", "yellow")
        cprint(f"   Total Attempts: {self.total_trades_attempted}", "white")
        cprint(f"   Successful: {self.total_trades_successful}", "green")
        cprint(f"   Success Rate: {success_rate:.1f}%", "green" if success_rate > 50 else "yellow")
        
        cprint(f"\n💰 Profit/Loss:", "yellow")
        cprint(f"   Total Profit: ${self.total_profit_usd:.2f}", "green")
        cprint(f"   Total Loss: ${self.total_loss_usd:.2f}", "red")
        cprint(f"   Net P/L: ${net_profit:.2f}", "green" if net_profit > 0 else "red")
        
        cprint(f"\n🧠 Learning:", "yellow")
        learning_stats = self.rl_learner.get_learning_stats()
        cprint(f"   Experiences: {learning_stats['total_experiences']}", "cyan")
        cprint(f"   Avg Reward: {learning_stats['avg_reward']:.2f}", "cyan")
        cprint(f"   Exploration: {learning_stats['epsilon']:.3f}", "cyan")
        
        # Top performing agents
        if alive_agents:
            cprint(f"\n🏆 Top Agents:", "yellow")
            top_agents = sorted(alive_agents, key=lambda a: a.total_profit_usd, reverse=True)[:3]
            for i, agent in enumerate(top_agents, 1):
                cprint(f"   {i}. {agent.id}: ${agent.total_profit_usd:.2f} (Gen {agent.generation})", "green")
        
        cprint("\n" + "="*80, "cyan")
    
    def _check_emergency_shutdown(self) -> bool:
        """Check if emergency shutdown is needed"""
        net_loss = self.total_loss_usd - self.total_profit_usd
        
        if net_loss > self.config['emergency_shutdown_loss']:
            cprint(f"\n🚨 EMERGENCY SHUTDOWN TRIGGERED!", "red", attrs=['bold'])
            cprint(f"   Net loss ${net_loss:.2f} exceeds limit ${self.config['emergency_shutdown_loss']:.2f}", "red")
            return True
        
        return False
    
    def _save_swarm_state(self):
        """Save swarm state to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        state = {
            'timestamp': time.time(),
            'runtime_seconds': time.time() - self.swarm_start_time,
            'config': self.config,
            'statistics': {
                'total_agents_born': self.total_agents_born,
                'total_agents_died': self.total_agents_died,
                'total_trades_attempted': self.total_trades_attempted,
                'total_trades_successful': self.total_trades_successful,
                'total_profit_usd': self.total_profit_usd,
                'total_loss_usd': self.total_loss_usd,
                'net_profit_usd': self.total_profit_usd - self.total_loss_usd
            },
            'agents': {
                'alive': [a.to_dict() for a in self.agents.values() if a.is_alive],
                'dead': self.dead_agents[-100:]  # Keep last 100
            },
            'learning_stats': self.rl_learner.get_learning_stats()
        }
        
        filepath = self.data_dir / f"swarm_state_{timestamp}.json"
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Save RL model
        model_path = self.data_dir / f"rl_model_{timestamp}.pkl"
        self.rl_learner.save_model(str(model_path))
        
        cprint(f"\n💾 Swarm state saved to {filepath}", "green")
    
    def _shutdown(self):
        """Graceful shutdown"""
        cprint("\n" + "="*80, "yellow")
        cprint("🛑 SWARM SHUTTING DOWN", "yellow", attrs=['bold'])
        cprint("="*80 + "\n", "yellow")
        
        self.running = False
        
        # Save final state
        cprint("💾 Saving final state...", "cyan")
        self._save_swarm_state()
        
        # Export discoveries
        discovery_path = self.data_dir / f"discoveries_{int(time.time())}.json"
        self.discovery.export_discoveries(str(discovery_path))
        
        # Print final statistics
        self._print_swarm_stats()
        
        cprint("\n✅ Shutdown complete. See you on the moon! 🌙", "green", attrs=['bold'])


def main():
    """Main entry point"""
    # Load config from file if exists
    config_path = Path("src/data/flashloan_swarm/config.json")
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        cprint(f"✅ Loaded config from {config_path}", "green")
    else:
        config = None
        cprint("ℹ️ Using default configuration", "cyan")
    
    # Create and start swarm
    swarm = FlashloanSwarm(config=config)
    swarm.start()


if __name__ == "__main__":
    main()
