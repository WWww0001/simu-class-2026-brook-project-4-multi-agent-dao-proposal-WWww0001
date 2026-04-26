import mesa
import math


class SmartLPAgent(mesa.Agent):
    """
    内卷同行：这就像是 P2 和 P3 时你的作品。
    他们想安安静静地赚手续费，但也常常被 Toxic Arbitrageur 割的体无完肤。
    """
    def __init__(self, unique_id, model,
                 tick_lower=-100, tick_upper=100,
                 initial_token0=50000.0, initial_token1=50000.0):
        super().__init__(unique_id, model)
        self.wealth = 10000.0
        self.position_id = None

        # LP 参数
        self.tick_lower = tick_lower
        self.tick_upper = tick_upper
        self.initial_token0 = initial_token0
        self.initial_token1 = initial_token1
        self.gas_fee = 0.001  # 重平衡的 Gas 费用

        # 是否已初始化仓位
        self._initialized = False

    def step(self):
        # 1. 检查自己手头的部位
        if not self._initialized:
            self.initialize_position()
            return

        # 2. 如果因为大盘的随机摆荡，自己脱离了池子的赚钱区间 (Out-of-range)
        if not self.model.v3_engine.is_in_range(self.unique_id):
            # 3. 就老老实实交一笔极度高昂的 Gas 费，重平衡（Rebalance）它
            self.rebalance()

    def initialize_position(self):
        """初始化 LP 仓位"""
        # 初始做市：投入一半 Token0，一半 Token1
        amount0 = self.initial_token0
        amount1 = self.initial_token1

        # 添加流动性
        liquidity = self.model.v3_engine.addLiquidity(
            agent_id=self.unique_id,
            amount0=amount0,
            amount1=amount1,
            tick_lower=self.tick_lower,
            tick_upper=self.tick_upper
        )

        if liquidity > 0:
            self._initialized = True
            # 扣除初始投入的财富
            spot_price = self.model.v3_engine.get_spot_price()
            self.wealth -= (amount0 + amount1 * spot_price)
            self.wealth = max(0, self.wealth)

    def rebalance(self):
        """重平衡仓位"""
        # 记录重平衡前的价值
        old_pos_value = self.calculate_position_value()

        # 执行重平衡
        new_amounts = self.model.v3_engine.rebalance_position(
            agent_id=self.unique_id,
            new_tick_lower=self.tick_lower,
            new_tick_upper=self.tick_upper
        )

        # 扣除 Gas 费用
        self.wealth -= self.gas_fee * self.wealth

        # 计算新的仓位价值
        new_pos_value = self.calculate_position_value()

        # 记入自己的净资产流血损耗
        loss = old_pos_value - new_pos_value
        if loss > 0:
            self.wealth -= loss

    def calculate_position_value(self):
        """计算当前仓位的价值"""
        if self.unique_id not in self.model.v3_engine.positions:
            return 0

        pos = self.model.v3_engine.positions[self.unique_id]
        spot_price = self.model.v3_engine.get_spot_price()

        # 仓位价值 = Token0 数量 + Token1 数量 * 当前价格
        return pos['amount0'] + pos['amount1'] * spot_price

    def collect_fees(self):
        """收集手续费收益"""
        # 在实际实现中，需要追踪未提取的手续费
        pass