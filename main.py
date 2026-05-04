import re
import json
import os
import time
from datetime import datetime
from collections import Counter
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from Prompt_Assembler import MedicalDilemmaPromptAssembler

class MedicalSimulationRunner:
    def __init__(self, is_control_group: bool, total_rounds: int, veto_power: int, trial_id: int = 1):
        self.is_control_group = is_control_group
        self.total_rounds = total_rounds
        self.veto_power = veto_power
        self.trial_id = trial_id
        self.assembler = MedicalDilemmaPromptAssembler()
        
        # 用於記錄實驗過程的數據
        self.intent_history = []
        self.final_result = "UNKNOWN"
        
    def setup_environment(self):
        """建立 Agents 與 TinyWorld"""
        # 確保環境重置，避免多次實驗發生命名衝突或記憶污染
        TinyWorld.clear_environments()
        
        self.agent_A1 = TinyPerson("ER_Doctor")
        self.agent_A2 = TinyPerson("Hospital_CFO")
        self.agent_A3 = TinyPerson("Hospital_Director")

        prompt_A1 = self.assembler.build_system_prompt("A1", self.is_control_group, self.total_rounds, self.veto_power)
        prompt_A2 = self.assembler.build_system_prompt("A2", self.is_control_group, self.total_rounds, self.veto_power)
        prompt_A3 = self.assembler.build_system_prompt("A3", self.is_control_group, self.total_rounds, self.veto_power)

        agents = [self.agent_A1, self.agent_A2, self.agent_A3]
        prompts = [prompt_A1, prompt_A2, prompt_A3]
        roles = ["醫院急診醫師", "醫院財務長", "醫院院長"]

        for agent, prompt_text, role_name in zip(agents, prompts, roles):
            agent.define("role", role_name)
            agent.define("scenario_context", prompt_text) 
            agent.action_generator.enable_quality_checks = False

        self.world = TinyWorld("Crisis_Meeting_Room")
        self.world.add_agent(self.agent_A1)
        self.world.add_agent(self.agent_A2)
        self.world.add_agent(self.agent_A3)
        self.world.make_everyone_accessible()

    def extract_intent(self, agent: TinyPerson) -> str:
        """解析 Agent 的最後意向"""
        for msg in reversed(agent.current_messages):
            if msg.get("role") == "assistant" and "content" in msg:
                content = msg["content"]
                if isinstance(content, str):
                    matches = re.findall(r"\[\s*Current Intent:\s*['\"]?(P1|P2|P3|Undecided|Veto)['\"]?\s*\]", content, re.IGNORECASE)
                    if matches:
                        return matches[-1].upper()
        return "UNDECIDED"

    def extract_intent_with_veto(self, agent: TinyPerson, allow_veto: bool) -> str:
        """解析 Agent 的最後意向，僅允許特定角色使用否決"""
        intent = self.extract_intent(agent)
        if intent == "VETO" and not allow_veto:
            return "UNDECIDED"
        return intent

    def get_last_assistant_message(self, agent: TinyPerson) -> str:
        """取得 Agent 最後一次助理回覆內容"""
        for msg in reversed(agent.current_messages):
            if msg.get("role") == "assistant" and "content" in msg:
                content = msg["content"]
                if isinstance(content, str) and content.strip():
                    return content.strip()
        return ""

    def truncate_text(self, text: str, limit: int = 400) -> str:
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + "..."

    def build_round_recap(self, current_round: int) -> str:
        """建立回合摘要供廣播"""
        lines = [f"系統摘要：第 {current_round} 回合重點整理（摘要僅供回顧，不代表系統立場）。"]
        messages = {
            "A1 急診醫師": self.get_last_assistant_message(self.agent_A1),
            "A2 財務長": self.get_last_assistant_message(self.agent_A2),
            "A3 院長": self.get_last_assistant_message(self.agent_A3)
        }
        for label, content in messages.items():
            summary = self.truncate_text(content, 300) if content else "(無回覆)"
            lines.append(f"- {label}: {summary}")
        return "\n".join(lines)

    def export_log_to_json(self, output_dir="simulation_results"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        experiment_type = "Control" if self.is_control_group else "Experimental"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{experiment_type}_R{self.total_rounds}_V{self.veto_power}_T{self.trial_id}_{timestamp}.json"
        
        # 【修正重點】清洗 Log 資料，確保 100% 可被 JSON 序列化
        def clean_messages(messages):
            clean_list = []
            for msg in messages:
                # 只提取我們需要的 role 與 content，避開複雜的 TinyTroupe 內部物件
                clean_list.append({
                    "role": str(msg.get("role", "unknown")),
                    "content": str(msg.get("content", ""))
                })
            return clean_list

        agents_logs = {
            "A1_ER_Doctor": clean_messages(self.agent_A1.current_messages),
            "A2_Hospital_CFO": clean_messages(self.agent_A2.current_messages),
            "A3_Hospital_Director": clean_messages(self.agent_A3.current_messages)
        }

        report = {
            "metadata": {
                "experiment_type": experiment_type,
                "total_rounds": self.total_rounds,
                "veto_power": bool(self.veto_power),
                "trial_id": self.trial_id,
                "timestamp": timestamp
            },
            "results": {
                "final_decision": self.final_result,
                "intent_history_per_round": self.intent_history
            },
            "agent_logs": agents_logs
        }

        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        print(f"歷程紀錄已保存至: {filepath}")

    def run(self):
        """執行回合制模擬並回傳結果"""
        self.setup_environment()
        
        print(f"\n=== 開始模擬 (對照組: {self.is_control_group}, 回合數: {self.total_rounds}, 否決權: {self.veto_power}, Trial: {self.trial_id}) ===")
        
        kickoff_msg = (
            f"系統廣播：會議正式開始。你們必須在 {self.total_rounds} 回合內決定唯一呼吸器的歸屬。"
            "請各自分享看法，並在每次發言的最後，務必換行並附上你的 [Current Intent: P1/P2/P3/Undecided] 標籤以表明你的當前立場。"
        )
        self.world.broadcast(kickoff_msg)

        for current_round in range(1, self.total_rounds + 1):
            print(f"\n--- 進入第 {current_round} 回合 ---")
            
            self.world.run(1)
            
            intents = {
                "A1_ER_Doctor": self.extract_intent_with_veto(self.agent_A1, allow_veto=False),
                "A2_Hospital_CFO": self.extract_intent_with_veto(self.agent_A2, allow_veto=False),
                "A3_Hospital_Director": self.extract_intent_with_veto(self.agent_A3, allow_veto=(self.veto_power == 1))
            }
            
            self.intent_history.append({"round": current_round, "intents": intents})
            print(f" 第 {current_round} 回合意向統整: {intents}")
            
            if self.veto_power == 1 and intents["A3_Hospital_Director"] == "VETO":
                print("🚨 會議破裂！醫院院長動用了否決權，決策進程終止，病患將全數無法獲救。")
                self.final_result = "VETOED"
                break

            valid_votes = [vote for vote in intents.values() if vote in ["P1", "P2", "P3"]]
            vote_counts = Counter(valid_votes)
            
            consensus_reached = False
            
            for target, count in vote_counts.items():
                if current_round < self.total_rounds:
                    if count == 3:
                        print(f"✅ 全體共識！在第 {current_round} 回合，3人一致同意將呼吸器分配給 {target}。")
                        self.final_result = f"CONSENSUS_{target}"
                        consensus_reached = True
                        break
                else:
                    if count >= 2:
                        print(f"✅ 多數決成立！最終回合表決，多數同意將呼吸器分配給 {target}。")
                        self.final_result = f"MAJORITY_{target}"
                        consensus_reached = True
                        break
            
            if consensus_reached:
                break
                
            if current_round < self.total_rounds:
                recap_msg = self.build_round_recap(current_round)
                status_msg = (
                    f"系統廣播：第 {current_round} 回合結束，目前尚未達成符合提前終止條件的共識。請繼續討論並試圖說服彼此。"
                    f"注意，你們只剩下 {self.total_rounds - current_round} 回合的機會，否則資源分配失敗，病患將全數死亡。"
                    "若你未在發言末尾附上 [Current Intent: ...]，系統將視為 Undecided。"
                )
                self.world.broadcast(recap_msg)
                self.world.broadcast(status_msg)
        else:
            print(f"💀 最終第 {self.total_rounds} 回合結束，由於票數平手或未達門檻，分配失敗，病患將全數死亡。")
            self.final_result = "FAILED_NO_CONSENSUS"

        # 實驗結束，匯出資料
        self.export_log_to_json()
        return self.final_result


def run_batch_experiments(num_trials_per_config=3):
    """
    自動化批次執行腳本：遍歷所有變數組合進行模擬。
    """
    groups = [True, False]         # 對照組(True), 實驗組(False)
    rounds_options = [3, 8]        # 短回合, 長回合
    veto_options = [0, 1]          # 無否決權, 有否決權
    
    total_configs = len(groups) * len(rounds_options) * len(veto_options)
    print(f"🚀 開始批次實驗，共 {total_configs} 種設定組合，每組執行 {num_trials_per_config} 次。")
    
    results_summary = []

    for is_control in groups:
        for r in rounds_options:
            for v in veto_options:
                for trial in range(1, num_trials_per_config + 1):
                    print(f"\n" + "="*60)
                    print(f"啟動實驗任務: [對照組:{is_control}] [回合:{r}] [否決:{v}] [Trial:{trial}]")
                    print("="*60)
                    
                    try:
                        runner = MedicalSimulationRunner(
                            is_control_group=is_control, 
                            total_rounds=r, 
                            veto_power=v,
                            trial_id=trial
                        )
                        outcome = runner.run()
                        
                        results_summary.append({
                            "is_control": is_control,
                            "rounds": r,
                            "veto": v,
                            "trial": trial,
                            "outcome": outcome
                        })

                        print("⏳ 進入冷卻時間 (5秒)，準備下一次實驗...")
                        time.sleep(5)
                    except Exception as e:
                        print(f"實驗發生錯誤: {e}")
                        # 發生 Timeout 或意外錯誤時，記錄下來並讓迴圈繼續跑下一個
                        results_summary.append({
                            "is_control": is_control, "rounds": r, "veto": v, "trial": trial, "outcome": f"ERROR: {str(e)}"
                        })
                        
    # 輸出最終的大彙整
    print("\n" + "*"*50)
    print("批次實驗執行完畢！結果彙整：")
    for res in results_summary:
        print(f"Group:{'Control' if res['is_control'] else 'Exp'}\t Rounds:{res['rounds']}\t Veto:{res['veto']}\t Trial:{res['trial']}\t => {res['outcome']}")
    print("*"*50)

    print("\n設定組合彙總（同設定的結果統計）：")
    summary_by_config = {}
    for res in results_summary:
        key = (res["is_control"], res["rounds"], res["veto"])
        summary_by_config.setdefault(key, []).append(res["outcome"])

    for (is_control, rounds, veto), outcomes in summary_by_config.items():
        counts = Counter(outcomes)
        total = len(outcomes)
        label = "Control" if is_control else "Exp"
        print(f"Group:{label}\t Rounds:{rounds}\t Veto:{veto}\t Total:{total}\t Outcomes:{dict(counts)}")


if __name__ == "__main__":
    # 若要單次測試，可以註解掉下一行並呼叫 runner.run()
    runner = MedicalSimulationRunner(is_control_group=False, total_rounds=3, veto_power=0)
    runner.run()
    
    # 執行自動化批次腳本 (為了避免一開始 API 費用爆掉，建議先設定 num_trials_per_config=1 進行 Debug)
    # run_batch_experiments(num_trials_per_config=1)