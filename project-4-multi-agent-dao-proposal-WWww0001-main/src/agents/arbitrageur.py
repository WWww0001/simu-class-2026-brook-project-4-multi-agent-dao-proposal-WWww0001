import mesa

class Arbitrageur(mesa.Agent):
    """
    剧毒的机械猎兵（MEV / Toxic Arbitrageur）。
    他什么风险都不承担，他的唯一目标是盯着池子里的价格与外界比对。
    如果有油水，一秒钟抽干它！
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = 100000.0  # 它拥有天量级的吸血资金
        self.threshold = 0.005  # 千分之五差价才值得动手（覆盖池子手续费）

    def step(self):
        # 1. 向主神获取当前外部的真理天平价格 (Oracle Price)
        # oracle_price = self.model.external_oracle_price
        
        # 2. 从 self.model.v3_engine 捞取目前池子里的实际推算价格。
        
        # 3. 如果偏差 > threshold，开启核弹攻击！
        # TODO: 算出到底要精准爆砸多少以太坊，才能把池子里的价格推平到和 Oracle 一样！
        pass
