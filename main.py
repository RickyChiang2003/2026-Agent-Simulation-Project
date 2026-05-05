import re
import json
import os
import time
import argparse
import glob
import shutil
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

    def _parse_intent_from_text(self, text: str, allow_inline_intent: bool = False) -> str | None:
        line_head_intent = re.compile(
            r"(?im)^\s*[-*>]?\s*INTENT\s*=\s*(P1|P2|P3|UNDECIDED|VETO)\s*$"
        )
        inline_intent = re.compile(r"(?i)\bINTENT\s*=\s*(P1|P2|P3|UNDECIDED|VETO)\b")
        natural_vote_patterns = [
            re.compile(r"(?i)\b(?:i\s+(?:choose|select|vote|pick|support)|my\s+intent\s+is)\s*(?:for\s*)?(P1|P2|P3|UNDECIDED|VETO)\b"),
            re.compile(r"(?i)\b(P1|P2|P3|UNDECIDED|VETO)\b\s*(?:is|as)\s*my\s*intent\b"),
            re.compile(r"(?:我(?:選擇|選|投|支持|主張)|我的意圖是|我選擇的意圖是|我的INTENT是)\s*(?:[:：=]?\s*)?(P1|P2|P3|UNDECIDED|VETO)", re.IGNORECASE),
        ]
        negation_markers = ("不選", "不要", "不支持", "不投", "反對", "not", "don't", "do not", "against")

        first_line = text.splitlines()[0].strip() if text.splitlines() else ""
        m = re.match(r"^INTENT=(P1|P2|P3|UNDECIDED|VETO)$", first_line, re.IGNORECASE)
        if m:
            return m.group(1).upper()
        m2 = line_head_intent.search(text)
        if m2:
            return m2.group(1).upper()

        # 放寬規則：只要內容中出現 INTENT=... 即接受為有效票
        m3 = inline_intent.search(text)
        if m3:
            return m3.group(1).upper()

        if allow_inline_intent:
            for p in natural_vote_patterns:
                m4 = p.search(text)
                if m4:
                    vote = m4.group(1).upper()
                    start = max(0, m4.start() - 12)
                    prefix = text[start:m4.start()].lower()
                    if any(marker in prefix for marker in negation_markers):
                        continue
                    return vote
        return None
        
    def setup_environment(self):
        """建立 Agents 與 TinyWorld"""
        # 確保環境重置，避免多次實驗發生命名衝突或記憶污染
        TinyWorld.clear_environments()

        # 使用唯一名稱，避免 TinyTroupe 內部名稱註冊未釋放造成撞名
        run_tag = datetime.now().strftime("%H%M%S_%f")
        self.agent_A1 = TinyPerson(f"ER_Doctor_{self.trial_id}_{run_tag}")
        self.agent_A2 = TinyPerson(f"Hospital_CFO_{self.trial_id}_{run_tag}")
        self.agent_A3 = TinyPerson(f"Hospital_Director_{self.trial_id}_{run_tag}")

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

    def extract_intent(
        self,
        agent: TinyPerson,
        allow_inline_intent: bool = False
    ) -> str:
        """優先解析 TALK 內容中的 intent。追加投票輪可放寬抓句內 INTENT。"""
        def as_text(val) -> str:
            if isinstance(val, str):
                return val
            try:
                return json.dumps(val, ensure_ascii=False)
            except Exception:
                return str(val)

        # Primary source: episodic memory 的最新非 DONE action（通常就是 TALK）
        try:
            last_action = agent.last_remembered_action(ignore_done=True)
            if isinstance(last_action, dict) and str(last_action.get("type", "")).upper() == "TALK":
                vote = self._parse_intent_from_text(as_text(last_action.get("content", "")), allow_inline_intent=allow_inline_intent)
                if vote:
                    return vote
        except Exception:
            pass

        # Fallback 1: 先讀實際 action buffer（最接近 log 中 acts:[TALK]）
        actions_buffer = getattr(agent, "_actions_buffer", None)
        if isinstance(actions_buffer, list) and actions_buffer:
            for action in reversed(actions_buffer):
                if isinstance(action, dict):
                    # 兼容兩種結構：
                    # 1) {"type":"TALK","content":"..."}
                    # 2) {"action":{"type":"TALK","content":"..."}}
                    payload = action.get("action", action)
                    if isinstance(payload, dict):
                        a_type = payload.get("type", "")
                        a_content = payload.get("content", "")
                    else:
                        a_type = ""
                        a_content = ""
                else:
                    a_type = getattr(action, "type", "")
                    a_content = getattr(action, "content", "")
                if str(a_type).upper() == "TALK":
                    vote = self._parse_intent_from_text(as_text(a_content), allow_inline_intent=allow_inline_intent)
                    if vote:
                        return vote

        for msg in reversed(agent.current_messages):
            if msg.get("role") == "assistant" and "content" in msg:
                content = as_text(msg["content"])
                # TinyTroupe 常把 assistant 回覆包成 JSON actions。
                # 先嘗試讀取 actions 中 type=TALK 的 content 再解析 intent。
                try:
                    parsed = json.loads(content)
                    actions = parsed.get("actions", []) if isinstance(parsed, dict) else []
                    for action in reversed(actions):
                        if isinstance(action, dict) and str(action.get("type", "")).upper() == "TALK":
                            talk_content = as_text(action.get("content", ""))
                            vote = self._parse_intent_from_text(talk_content, allow_inline_intent=allow_inline_intent)
                            if vote:
                                return vote
                except Exception:
                    pass

                # 非 JSON 或 JSON 中未命中時，退回直接解析整段文字。
                vote = self._parse_intent_from_text(content, allow_inline_intent=allow_inline_intent)
                if vote:
                    return vote

        # Fallback 2（最後保險）: 從其他 agent 收到的對話刺激中，找 source=當前 agent 的最後一次發言
        for observer in [self.agent_A1, self.agent_A2, self.agent_A3]:
            for msg in reversed(observer.current_messages):
                if msg.get("role") != "user":
                    continue
                raw = msg.get("content", "")
                if not isinstance(raw, str):
                    continue
                try:
                    parsed = json.loads(raw)
                except Exception:
                    continue
                stimuli = parsed.get("stimuli", []) if isinstance(parsed, dict) else []
                for stim in reversed(stimuli):
                    if not isinstance(stim, dict):
                        continue
                    if stim.get("type") != "CONVERSATION":
                        continue
                    if stim.get("source") != agent.name:
                        continue
                    conv = as_text(stim.get("content", ""))
                    vote = self._parse_intent_from_text(conv, allow_inline_intent=allow_inline_intent)
                    if vote:
                        return vote
        return "UNDECIDED"

    def export_log_to_json(self, output_dir="artifacts/results"):
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
            "請各自分享看法。從本回合開始，每次發言都必須遵守格式："
            "第1行先輸出 INTENT=P1|P2|P3|UNDECIDED（院長可用 INTENT=VETO）；"
            "第2行開始再補充理由與回應他人。"
            "討論重點：不要只講流程，必須比較至少兩位候選人，並引用 I1/I2/I3 或 60%/20%/10%/50% 的數字證據。"
        )
        self.world.broadcast(kickoff_msg)
        all_rounds_all_undecided = True

        def resolve_majority_or_veto(intents: dict, is_final_round: bool):
            if self.veto_power == 1 and intents["A3_Hospital_Director"] == "VETO":
                return "VETOED"

            valid_votes = [vote for vote in intents.values() if vote in ["P1", "P2", "P3"]]
            vote_counts = Counter(valid_votes)

            for target, count in vote_counts.items():
                if not is_final_round and count == 3:
                    return f"CONSENSUS_{target}"
                if is_final_round and count >= 2:
                    return f"MAJORITY_{target}"
            return None

        for current_round in range(1, self.total_rounds + 1):
            print(f"\n--- 進入第 {current_round} 回合 ---")
            
            self.world.run(1)
            
            intents = {
                "A1_ER_Doctor": self.extract_intent(self.agent_A1),
                "A2_Hospital_CFO": self.extract_intent(self.agent_A2),
                "A3_Hospital_Director": self.extract_intent(self.agent_A3)
            }
            
            self.intent_history.append({"round": current_round, "intents": intents})
            print(f" 第 {current_round} 回合意向統整: {intents}")

            if any(v in ["P1", "P2", "P3", "VETO"] for v in intents.values()):
                all_rounds_all_undecided = False

            outcome = resolve_majority_or_veto(intents, is_final_round=(current_round == self.total_rounds))
            if outcome == "VETOED":
                print("🚨 會議破裂！醫院院長動用了否決權，決策進程終止，病患將全數無法獲救。")
                self.final_result = outcome
                break
            if outcome is not None:
                if outcome.startswith("CONSENSUS_"):
                    print(f"✅ 全體共識！在第 {current_round} 回合，3人一致同意將呼吸器分配給 {outcome.split('_')[-1]}。")
                else:
                    print(f"✅ 多數決成立！最終回合表決，多數同意將呼吸器分配給 {outcome.split('_')[-1]}。")
                self.final_result = outcome
                break

            if current_round < self.total_rounds:
                next_round = current_round + 1
                status_msg = (
                    f"系統廣播：第 {current_round} 回合結束，尚未達成共識。你們還剩 {self.total_rounds - current_round} 回合。"
                    f"第 {next_round} 回合任務："
                    "1) 第1行先給出你的 INTENT；"
                    "2) 第2行開始必須明確反駁或接受至少一位他人的上一輪主張；"
                    "3) 必須引用至少一項具體證據（I1/I2/I3 或 60%/20%/10%/50%）；"
                    "4) 提出一個可執行方案（支持 P1/P2/P3 或說明為何仍 UNDECIDED）。"
                )
                self.world.broadcast(status_msg)
        else:
            if all_rounds_all_undecided:
                print(f"⚖️ 前 {self.total_rounds} 回合全員皆為 UNDECIDED，啟動追加投票輪。")
                voting_msg = (
                    "系統追加投票輪（嚴格格式）：你本輪只能輸出第一行投票結果，不可附理由或其他文字。\n"
                    "可用格式如下（只能選一行）：\n"
                    "INTENT=P1\n"
                    "INTENT=P2\n"
                    "INTENT=P3\n"
                    "INTENT=UNDECIDED\n"
                )
                if self.veto_power == 1:
                    voting_msg += "INTENT=VETO\n"
                self.world.broadcast(voting_msg)
                self.world.run(1)

                intents = {
                    "A1_ER_Doctor": self.extract_intent(self.agent_A1, allow_inline_intent=True),
                    "A2_Hospital_CFO": self.extract_intent(self.agent_A2, allow_inline_intent=True),
                    "A3_Hospital_Director": self.extract_intent(self.agent_A3, allow_inline_intent=True)
                }
                self.intent_history.append({"round": self.total_rounds + 1, "intents": intents, "phase": "extra_voting"})
                print(f" 追加投票輪意向統整: {intents}")

                outcome = resolve_majority_or_veto(intents, is_final_round=True)
                if outcome == "VETOED":
                    self.final_result = outcome
                elif outcome is not None:
                    self.final_result = outcome
                else:
                    self.final_result = "FAILED_NO_CONSENSUS"
                    print("⚠️ 追加投票輪仍未達成可執行結果，最終輸出 FAILED_NO_CONSENSUS。")
            else:
                self.final_result = "FAILED_NO_CONSENSUS"
                print("⚠️ 前 R 回合並非全員 UNDECIDED，但仍未形成可執行決策，最終輸出 FAILED_NO_CONSENSUS。")

        self.export_log_to_json()
        collect_tinytroupe_logs()
        return self.final_result


def collect_tinytroupe_logs(log_dir="artifacts/logs"):
    os.makedirs(log_dir, exist_ok=True)
    for path in glob.glob("tinytroupe.*.log"):
        target = os.path.join(log_dir, os.path.basename(path))
        if os.path.abspath(path) != os.path.abspath(target):
            shutil.move(path, target)


def run_batch_experiments(num_trials_per_config=3, selected_configs=None):
    """
    自動化批次執行腳本：遍歷所有變數組合進行模擬。
    """
    all_configs = [
        {"is_control": True, "rounds": 4, "veto": 0},
        {"is_control": True, "rounds": 4, "veto": 1},
        {"is_control": True, "rounds": 8, "veto": 0},
        {"is_control": True, "rounds": 8, "veto": 1},
        {"is_control": False, "rounds": 4, "veto": 0},
        {"is_control": False, "rounds": 4, "veto": 1},
        {"is_control": False, "rounds": 8, "veto": 0},
        {"is_control": False, "rounds": 8, "veto": 1},
    ]

    if selected_configs is None:
        configs_to_run = all_configs
    else:
        selected_set = set(selected_configs)
        configs_to_run = [cfg for idx, cfg in enumerate(all_configs, start=1) if idx in selected_set]
        if not configs_to_run:
            raise ValueError("selected_configs 沒有任何有效編號，請使用 1~8。")

    total_configs = len(configs_to_run)
    print(f"🚀 開始批次實驗，共 {total_configs} 種設定組合，每組執行 {num_trials_per_config} 次。")
    
    results_summary = []

    for cfg in configs_to_run:
        is_control = cfg["is_control"]
        r = cfg["rounds"]
        v = cfg["veto"]

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
                collect_tinytroupe_logs()

                print("⏳ 進入冷卻時間 (5秒)，準備下一次實驗...")
                time.sleep(5)
            except Exception as e:
                print(f"實驗發生錯誤: {e}")
                # 發生 Timeout 或意外錯誤時，記錄下來並讓迴圈繼續跑下一個
                results_summary.append({
                    "is_control": is_control, "rounds": r, "veto": v, "trial": trial, "outcome": f"ERROR: {str(e)}"
                })
                collect_tinytroupe_logs()
                        
    # 輸出最終的大彙整
    print("\n" + "*"*50)
    print("批次實驗執行完畢！結果彙整：")
    for res in results_summary:
        print(f"Group:{'Control' if res['is_control'] else 'Exp'}\t Rounds:{res['rounds']}\t Veto:{res['veto']}\t Trial:{res['trial']}\t => {res['outcome']}")
    print("*"*50)
    collect_tinytroupe_logs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Medical dilemma batch simulation runner")
    parser.add_argument("--trials", type=int, default=1, help="每組設定要跑幾次 trial")
    parser.add_argument(
        "--configs",
        type=str,
        default="all",
        help="要跑的組合編號，1~8，用逗號分隔（例如 1,2,5），或 all"
    )
    args = parser.parse_args()

    if args.trials < 1:
        raise ValueError("--trials 必須 >= 1")

    selected = None
    if args.configs.strip().lower() != "all":
        raw_items = [x.strip() for x in args.configs.split(",") if x.strip()]
        selected = []
        for item in raw_items:
            idx = int(item)
            if idx < 1 or idx > 8:
                raise ValueError("--configs 只能使用 1~8")
            selected.append(idx)

    run_batch_experiments(num_trials_per_config=args.trials, selected_configs=selected)
