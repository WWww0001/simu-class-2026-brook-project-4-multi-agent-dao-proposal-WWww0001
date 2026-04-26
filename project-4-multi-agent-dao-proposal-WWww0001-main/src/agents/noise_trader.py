import mesa
import random

class NoiseTrader(mesa.Agent):
    """
    噪音散户：抛硬币的送财童子。
    他不在乎亏损，只在乎在 V3 里进行交易换钱，向系统提供手续费营养。
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = 10000.0  # 进场本金

    def step(self):
        # TODO: 使用 random() 判断要不要买，买多少。
        # 如果买，向 self.model.v3_engine 发起 swap 并承担滑点。
        # 每一次换出来的钱（扣除了滑点和手续费），就是自己的新 wealth。
        pass
