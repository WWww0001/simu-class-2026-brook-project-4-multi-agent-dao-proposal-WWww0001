"""
🌍 Project 4: 全局生态与时钟控制器 (The Master Environment)
你的环境继承自 Mesa。它是唯一握有 V3 实例的上帝对象。
"""
import mesa
import random

try:
    from src.simulator import V3Engine
    from src.agents.noise_trader import NoiseTrader
    from src.agents.arbitrageur import Arbitrageur
    from src.agents.smart_lp import SmartLPAgent
except ImportError as e:
    print(f"⚠️ 导入错误: {e}")
    raise ImportError("请确保从 P1/P2 获取 simulator.py 或已创建 src/simulator.py")


class V3MasterModel(mesa.Model):
    def __init__(self, n_noise=10, n_arb=2, n_lp=5,
                 initial_price=1.0, oracle_volatility=0.002):
        super().__init__()

        # TODO 1: 实例化你的 V3 核心印钞机
        self.v3_engine = V3Engine()

        # TODO 2: 设置随机抽取的 Mesa 调度器
        self.schedule = mesa.time.RandomActivation(self)

        # Oracle 价格配置
        self.oracle_price = initial_price
        self.oracle_volatility = oracle_volatility

        # 实例计数器
        self.noise_count = 0
        self.arb_count = 0
        self.lp_count = 0

        # TODO 3: 实例化三类怪物，并加入调度器
        for _ in range(n_noise):
            agent = NoiseTrader(unique_id=self.noise_count, model=self)
            self.schedule.add(agent)
            self.noise_count += 1

        for _ in range(n_arb):
            agent = Arbitrageur(unique_id=self.arb_count, model=self)
            self.schedule.add(agent)
            self.arb_count += 1

        for _ in range(n_lp):
            agent = SmartLPAgent(unique_id=self.lp_count, model=self)
            self.schedule.add(agent)
            self.lp_count += 1

        # TODO 4: 配置上帝视角的 DataCollector
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Oracle_Price": lambda m: m.oracle_price,
                "Spot_Price": lambda m: m.v3_engine.get_spot_price(),
                "Reserve0": lambda m: m.v3_engine.reserve0,
                "Reserve1": lambda m: m.v3_engine.reserve1,
                "Total_Noise_Wealth": lambda m: sum(a.wealth for a in m.schedule.agents if isinstance(a, NoiseTrader)),
                "Total_Arb_Wealth": lambda m: sum(a.wealth for a in m.schedule.agents if isinstance(a, Arbitrageur)),
                "Total_LP_Wealth": lambda m: sum(a.wealth for a in m.schedule.agents if isinstance(a, SmartLPAgent)),
                "Num_Agents": lambda m: len(m.schedule.agents),
            },
            agent_reporters={
                "Wealth": lambda a: getattr(a, 'wealth', 0),
                "Type": lambda a: type(a).__name__
            }
        )

        # 跟踪每类群体的财富历史
        self.noise_wealth_history = []
        self.arb_wealth_history = []
        self.lp_wealth_history = []

    def update_oracle(self):
        """释放随机游走的外部预言机大盘价 (Oracle Price)"""
        # 几何布朗运动风格的随机游走
        drift = 0
        volatility = self.oracle_volatility
        random_shock = random.gauss(drift, volatility)

        # 更新 oracle price (保持正值)
        new_price = self.oracle_price * (1 + random_shock)
        new_price = max(0.1, min(10.0, new_price))  # 保持在合理范围

        self.oracle_price = new_price
        self.v3_engine.update_oracle_price(new_price)

        return self.oracle_price

    def step(self):
        # 1. 保存当前宇宙截面数据
        self.datacollector.collect(self)

        # 2. 释放随机游走的外部预言机大盘价
        self.update_oracle()

        # 3. 按下推进按钮，让所有怪物行动一回合
        self.schedule.step()

    def get_agent_wealth_by_type(self, agent_type):
        """获取某类群体的总财富"""
        return sum(
            agent.wealth
            for agent in self.schedule.agents
            if isinstance(agent, agent_type)
        )

    def get_pool_liquidity(self):
        """获取池子流动性"""
        return self.v3_engine.liquidity

    def get_price_deviation(self):
        """获取当前价格偏离度"""
        spot = self.v3_engine.get_spot_price()
        oracle = self.oracle_price
        return (spot - oracle) / oracle if oracle > 0 else 0