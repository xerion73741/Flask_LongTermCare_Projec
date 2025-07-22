import random

class GuessNumberGame:
    def __init__(self, start=1, end=100):
        self.start = start
        self.end = end
        self.target = random.randint(start, end)
        self.attempts = 0
        self.is_over = False

    def guess(self, num):
        if self.is_over:
            return "遊戲已結束"

        self.attempts += 1
        if num == self.target:
            self.is_over = True
            return f"恭喜！猜對了，答案是 {self.target}，共猜了 {self.attempts} 次"
        elif num < self.target:
            return "太小了"
        else:
            return "太大了"


class WhackAMoleGame:
    def __init__(self, holes=5, rounds=10):
        self.holes = holes
        self.rounds = rounds
        self.score = 0

    def play_round(self, hit_position):
        mole_position = random.randint(1, self.holes)
        print(f"👀 地鼠出現在第 {mole_position} 洞！")

        if hit_position == mole_position:
            self.score += 1
            return "💥 打中了！"
        else:
            return "😵 沒打中..."


class RacingGame:
    def __init__(self, total_laps=3):
        self.total_laps = total_laps
        self.current_lap = 0
        self.position = 0  # 目前賽車位置，0代表起點

    def advance(self, distance):
        self.position += distance
        if self.position >= 100:  # 假設賽道長度100單位
            self.current_lap += 1
            self.position = self.position % 100

    def is_finished(self):
        return self.current_lap >= self.total_laps


if __name__ == "__main__":
    # game = GuessNumberGame()

    # print("🎯 猜數字遊戲開始！請猜 1 到 100 間的數字")

    # while not game.is_over:
    #     try:
    #         user_input = int(input("請輸入你的猜測："))
    #         result = game.guess(user_input)
    #         print(result)
    #     except ValueError:
    #         print("⚠️ 請輸入有效的整數！")



    game = WhackAMoleGame()

    print("🔨 打地鼠遊戲開始！一共有 10 回合，請輸入 1 到 5 間的洞口位置")

    for round_num in range(1, game.rounds + 1):
        print(f"\n第 {round_num} 回合")
        try:
            choice = int(input("你要打哪一個洞？（1~5）："))
            if 1 <= choice <= game.holes:
                result = game.play_round(choice)  # <<<<<<<< 傳入參數
                print(result)
            else:
                print("⚠️ 請輸入 1 到 5 的數字")
        except ValueError:
            print("⚠️ 請輸入整數！")

    print(f"\n🏁 遊戲結束！你的總得分是：{game.score} 分")