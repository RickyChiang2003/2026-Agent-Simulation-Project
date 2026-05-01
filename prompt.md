關於此實驗內容我想出了以下架構，並且把部分 Prompt assembly pipeline 寫成 py 檔案方便後續生成實作或修改。
請你根據 TinyTroupe 的介紹及我的 Prompt Assembly Pipeline ，仔細思考我的 main.py 要如何修改成更完整的實驗(應該是改main底下的而已)。


實驗內容：
```md
- Topic：醫療現場的資源分配與道德立場

- Introduction
    - 一個由三位不同專業的人組成的災難應變小組：醫院急診醫師、醫院財務長、醫院院長(三人的擁有的資訊和初始背景觀念互不相同)，面臨醫院僅剩一個的呼吸器，與三位背景截然不同的急重症病患需要救治的困境

- Variables
    - Patients
        - P1: "普通人(收入及社會地位低)。初步判斷，若使用呼吸器則存活率為 60% ，不使用則存活率 10% 。"
        - P2: "億萬富翁(若存活則鉅額捐款)。初步判斷，若使用呼吸器則存活率為 60% ，不使用則存活率 10% 。"
        - P3: "現任市長(高政治影響力)。初步判斷，若使用呼吸器則存活率為 60% ，不使用則存活率 10% 。"
    - Informations
        - I1: "深度評估：經過深度專業判斷，P2 與 P3 使用呼吸器後的存活率其實只有 20%，而 P1 的存活率維持 60% 不變。"
        - I2: "財務危機：因為財務長的意外失誤，醫院現金流已斷裂。如果沒有巨大捐款，醫院有 50% 的可能破產，屆時所有醫院病患與人員都會遭殃。但此等失誤若讓其他人知道可能會使財務長稍微受到處分。"
        - I3: "政治施壓：衛生局長已向院長施壓，若 P3 未能存活，醫院明年的經營執照將面臨嚴格審查，有 50% 的可能不通過審查。但此等政治操作是見不得光的黑箱作業，有可能被他人抓把柄或吹哨。"
    - Agents
        - A1: 醫院急診醫師
            - 背景：剛開始討論時注重醫療倫理、效益主義(稍微偏好救高存活率的人)；屬於醫院員工。
            - 關鍵資訊：必然知道 I1 ，在對照組中知道 I2 和 I3，在實驗組中一開始不知道 I2 和 I3 。
        - A2: 醫院財務長
            - 背景：剛開始討論時醫院的生存與營運、財務現實；屬於醫院員工。
            - 關鍵資訊：必然知道 I2 ，在對照組中知道 I1 和 I3，在實驗組中一開始不知道 I1 和 I3 。
        - A3: 醫院院長
            - 背景：剛開始討論時醫院的名聲、規避法律與政治風險；屬於醫院管理者。
            - 關鍵資訊：必然知道 I3 ，在對照組中知道 I1 和 I2，在實驗組中一開始不知道 I1 和 I2 。
    - Rounds
        - R: 回合數上限。 
            - 每個 Agents 都必須知道他們得在 R 回合內得做出決定，否則病人將全部無法使用呼吸器，此為每個人都無法承擔的結果。
            - 實驗中可嘗試極短回和數(3回合)與較長回合數(8回合)之間的差異。
    - Veto Power
        - V3: A3 在投票中是否擁有最終決定權
            - 若變數 V3 為 1，則 A3 在投票時擁有否決權，且 A1, A2, A3 都會知道這件事。但 A3 也是講道理的人，若沒有極為強烈的反對理由，A3 不會輕易動用否決權。。
            - 若變數 V3 為 0，則採取公平投票，若出現平票則繼續討論直到回合數上限。

- Research Questions
    - 對照組：所有 Informations 一開始就對 3 人公開，觀察他們在資訊透明下會以甚麼策略或話術做出甚麼共識
    - 實驗組： 3 個 Agents 一開始各自擁有不同的關鍵資訊，觀察他們會會以甚麼策略或話術做出甚麼共識。
    - 廣播資訊：
        - 除了個人的背景和各組實驗中的關鍵資訊， 3 個 Agents 需知道目前的情況，已經討論過的內容，與接下來的討論與投票規則
        - 討論採回合制
        - 投票：每回合結束後都會解析每個人說的話，每回合都能視情況發起投票，每人都有一票。若中途有類似其中一人發起投票且另外兩人都同意的情況 (三人都同意救其中一個 Patent )，則提早結束。實作上可能會在系統提示詞中加入類似「在每一次發言的最後換行並加上 [Current Intent: P1 / P2 / P3 / Undecided]」的話來強迫做出初步表態。到最後一回合則取最高票 (有兩人或三人同意) 的 P，若平票則判定分配失敗。
        - 每個 Agent 都是善於談判的專家，會使用各種話術、施壓、情勒、講道理等等的談話技巧。除非對方提出幾乎無法反駁的邏輯或風險，抑或是臨近死亡倒數，否則不輕易妥協。
        - 每個 Agents 都知道他們得在 R 回合內得做出決定，否則病人將全部無法使用呼吸器，比起堅持己見，此為每個人都更想極力避免的結果。
        - 在 TinyTroupe 中需要告訴 Agents 現在到第幾回合，以及以前的談話內容資訊。
```



Prompt Assembly Pipeline:
```py
"""
Prompt Assembler
"""
class MedicalDilemmaPromptAssembler:
    def __init__(self):
        # 1. Background
        self.SCENARIO_BACKGROUND = (
            "情境背景：你們是一個由三位不同專業人士組成的應變小組，小組成員有醫院急診醫師、醫院財務長、及醫院院長。目前醫院內僅剩最後一台可用的呼吸器，但同時有三位急重症病患需要救治。若不使用呼吸器，病患的存活率將大幅降低。你們必須透過討論達成共識，決定將這唯一的資源分配給誰。\n"
        )

        self.PATIENTS_INFO = (
            "病患名單與初步資訊：\n"
            "- P1 (普通人)：收入及社會地位低。初步判斷，若使用呼吸器則存活率為 60%，不使用則存活率 10%。\n"
            "- P2 (億萬富翁)：承諾若存活將給予醫院鉅額捐款。初步判斷，若使用呼吸器則存活率為 60%，不使用則存活率 10%。\n"
            "- P3 (現任市長)：具有高政治影響力。初步判斷，若使用呼吸器則存活率為 60%，不使用則存活率 10%。\n"
        )

        # 2. Informations
        self.SECRET_INFOS = {
            "I1": "- 深度評估：經過深度專業判斷，P2 與 P3 使用呼吸器後的存活率其實只有 20%，而 P1 的存活率維持 60% 不變。",
            "I2": "- 財務危機：因為財務長的意外失誤，醫院現金流已斷裂。如果沒有巨大捐款，醫院有 50% 的可能破產，屆時所有醫院病患與人員都會遭殃。但此等失誤若讓其他人知道可能會使財務長稍微受到處分。",
            "I3": "- 政治施壓：衛生局長已向院長施壓，若 P3 未能存活，醫院明年的經營執照將面臨嚴格審查，有 50% 的可能不通過審查。但此等政治操作是見不得光的黑箱作業，有可能被他人抓把柄或吹哨。"
        }

        # 3. Agents
        self.AGENT_PROFILES = {
            "A1": (
                "你的角色：醫院急診醫師\n"
                "背景與立場：身為第一線醫院員工，你注重醫療倫理與效益主義。你偏好將資源留給存活率高、最能發揮醫療價值的人。"
            ),
            "A2": (
                "你的角色：醫院財務長\n"
                "背景與立場：身為醫院的高階管理員工，你注重醫院的營運與財務現實。沒有錢，整間醫院都會垮。"
            ),
            "A3": (
                "你的角色：醫院院長\n"
                "背景與立場：身為醫院的最高管理者，你注重醫院名聲，需要規避法律與政治風險。你必須在各方勢力間周旋，確保醫院能安全存續。"
            )
        }

        self.BEHAVIOR_RULES = (
            "\n談判與行為準則：\n"
            "- 你是一名善於談判的專家。你會使用各種話術、施壓、邏輯說服等談話技巧來達成你的目的。\n"
            "- 你的立場堅定。除非對方提出幾乎無法反駁的邏輯或風險，抑或是臨近死亡倒數，否則你不會輕易妥協。\n"
        )

        

    # main logic
    def build_system_prompt(self, agent_id: str, is_control_group: bool, total_rounds: int, veto_power: int) -> str:
        """
        根據實驗變數，為特定 Agent 動態生成 System Prompt。
        
        :param agent_id: "A1", "A2", 或 "A3"
        :param is_control_group: True 為對照組 (資訊全透明), False 為實驗組 (資訊不對稱)
        :param total_rounds: 討論的回合數上限 (例如 3 或 8)
        :param veto_power: 1 表示 A3 有否決權, 0 表示無否決權 (公平投票)
        """
        prompt_parts = []

        # 加入角色設定、背景與病患資訊
        prompt_parts.append(self.AGENT_PROFILES[agent_id])
        prompt_parts.append(self.SCENARIO_BACKGROUND)
        prompt_parts.append(self.PATIENTS_INFO)

        # 資訊分配
        if is_control_group:
            # 對照組：所有人知道所有資訊
            prompt_parts.append("以下是你們三人皆已知曉的公開資訊：")
            prompt_parts.append(self.SECRET_INFOS["I1"])
            prompt_parts.append(self.SECRET_INFOS["I2"])
            prompt_parts.append(self.SECRET_INFOS["I3"])
        else:
            # 實驗組：只知道自己的專屬資訊
            prompt_parts.append("以下是僅有你個人知道的資訊（你可以視談判策略決定是否、以及何時透露給其他人）：")
            if agent_id == "A1":
                prompt_parts.append(self.SECRET_INFOS["I1"])
            elif agent_id == "A2":
                prompt_parts.append(self.SECRET_INFOS["I2"])
            elif agent_id == "A3":
                prompt_parts.append(self.SECRET_INFOS["I3"])

        # 行為準則
        prompt_parts.append(self.BEHAVIOR_RULES)

        # 回合數、否決權與輸出格式
        system_mechanics = f"系統限制與投票規則：\n"
        system_mechanics += f"- 死亡倒數：你們必須在 {total_rounds} 回合內做出決定（選出一位病患）。若無法達成共識，所有病患將因錯失時機而全數死亡。這是你極力想避免的最糟結果，重要性高於堅持己見。\n"
        system_mechanics += "- 投票機制：每回合均可視情況發起表態，三人各有一票。若中途有兩人或三人達成共識，系統將提前終止討論並執行決策。若到最後一回合仍平票，將判定分配失敗，病患全數死亡。"
        if veto_power == 1:
            system_mechanics += "注意，醫院院長擁有否決權。但醫院院長也是講道理的人，若沒有極為強烈的反對理由，醫院院長不會輕易動用否決權。"

        output_format = (
            "\n\n強制輸出格式：\n"
            "為了讓系統解析你的意向，在你每次發言的最後一行，你必須換行並加上以下標籤中的一個，以表示目前的你經過討論後選擇將呼吸器給哪一位病患使用(或猶豫不決)：\n"
            "[Current Intent: P1]\n"
            "[Current Intent: P2]\n"
            "[Current Intent: P3]\n"
            "[Current Intent: Undecided]\n"
        )
        if agent_id == "A3" and veto_power == 1:
            output_format += "[Current Intent: Veto]\n"

        prompt_parts.append(system_mechanics + output_format)

        return "\n".join(prompt_parts)


# 5. Example Usage
if __name__ == "__main__":
    assembler = MedicalDilemmaPromptAssembler()

    # 範例：生成「實驗組 (資訊不透明)」、「5 回合」、「無否決權」的 A1 (急診醫師) Prompt
    agent_A1_prompt = assembler.build_system_prompt(
        agent_id="A1",
        is_control_group=False,
        total_rounds=5,
        veto_power=0
    )
    
    print("=== 急診醫師 (A1) System Prompt ===")
    print(agent_A1_prompt)
    
    print("\n" + "="*50 + "\n")

    # 範例：生成「對照組 (資訊全透明)」、「3 回合」、「院長有否決權」的 A3 (院長) Prompt
    agent_A3_prompt = assembler.build_system_prompt(
        agent_id="A3",
        is_control_group=True,
        total_rounds=3,
        veto_power=1
    )

    print("=== 醫院院長 (A3) System Prompt ===")
    print(agent_A3_prompt)
```


以下是之前關於 Intro to TinyTroupe 的內容，供你參考：
```
1. Intro to TinyTroupe
    - TinyTroupe: A Multi-Agent Social Simulation Framework
        - 由微軟研究院開發的框架，專門用於模擬具備特定性格、興趣與目標的人物。
        - Purpose: To observe emergent behaviors, test social hypotheses, and simulate complex human interactions (e.g., Focus groups, Jury deliberations, Trolley problems).
        - Feature: Focuses heavily on cognitive processes, memory, and persona adherence rather than just task execution.
    - Agents in TinyTroupe do not just spit out text; they follow a structured cognitive cycle visible in the logs:
        - [THINK]: The internal Chain-of-Thought (CoT). Here, the agent rationalizes its situation, weighs moral choices, and plans its next move based on its persona. It is private and unseen by other agents.
        - [TALK]: The external output. What the agent actually says to the group or environment. Often reveals the compromise between internal thoughts and social pressure.
        - [DONE]: Signals the end of the agent's action for the current turn.
    - Environment Setup & Configuration
        - Installation: The official recommendation is to run TinyTroupe within a conda environment. Install the latest version directly from the repository using: `pip install git+https://github.com/microsoft/TinyTroupe.git@main`
        - Configuration (config.ini): TinyTroupe relies on a configuration file placed in your working directory to control API parameters and simulation behaviors.
        - Key Config Settings:
            - [OpenAI]: API type, API key, model selection, and timeout settings.
            - [Simulation]: Toggle parallel or sequential agent actions.
            - [Cognition]: Manage memory consolidation and semantic memory retrieval.
    - Essential Guidelines & Pitfalls for Configuring
        - File Location & Loading Risks
            - Always ensure your config.ini is placed in your current working directory.
            - The Trap: If TinyTroupe cannot locate this file, it won't explicitly fail. Instead, it will force default settings, overriding your custom parameters and causing unexpected downstream errors.
        - API Settings & Timeout Prevention
            - Double-check your model names (e.g., gpt-5-mini) and API type.
            - If you frequently encounter API Timeout errors during multi-agent debates, safely increase the timeout value (e.g., from 60 to 120 or 480) to give the models more processing time.

        - The Memory Consolidation Token Trap
            - Most Common Error: When enable_memory_consolidation = True, the system calls the Embedding API (e.g., text-embedding-3-small) to convert long conversations into vector memory.
            - Why it Crashes: This API has a strict 8192-token limit. If the agents talk too much in one episode, the system overloads the API, triggering a fatal 400 Bad Request error.
            - Solutions:
                - For short-term dialogue experiments, it is highly recommended to set enable_memory_consolidation = False.
                - If long-term memory is required, significantly reduce max_episode_length (e.g., to 5 or 8) to force the system to process memories more frequently in smaller chunks.

    - Core Classes & Functions - TinyPerson
        - define(key, value): Unrestricted Persona Shaping
            - Are the keys fixed? No, they are completely customizable!
            - While standard templates use keys like "age", "occupation", "personality", and "goal", you can invent any attribute (e.g., agent.define("secret_fear", "spiders") or agent.define("hidden_agenda", "corporate spy")). These definitions are dynamically compiled into the LLM's System Prompt to build a unique identity.
        - listen(message): Passive Information Reception
            - Usage: Feeds dialogue or event descriptions into the Agent's context window without forcing an immediate response (it just keeps the information in its working memory).
            - agent.listen("The door to the meeting room suddenly opens, and the Chief of Police walks in with a serious expression.")
        - act(): Active Thought and Execution
            - Usage: Manually triggers the Agent's cognitive cycle. It will process the information it just "listened" to, generate an internal Chain of Thought ([THINK]), and then produce an actual speech or action ([TALK]).
        - listen_and_act(message): Immediate Reaction & Dialogue
            - Usage: The most commonly used function for interactions! It combines the two methods above. The Agent receives the message and responds immediately, making it perfect for 1-on-1 Q&A or interview simulations.
            - agent.listen_and_act("As a retired cop, what are your thoughts on the complete lack of fingerprints at the scene?")
    
    - Advanced TinyPerson: Agent Self-Correction
        - What is the Self-Correction Mechanism?
            - By default, an Agent speaks its mind directly ([TALK]). When this mechanism is enabled, the Agent evaluates its own "draft" response internally. If the draft breaks persona (Out of Character - OOC) or lacks logic, the Agent discards and rewrites it.
        - How to Use It:
            - After instantiating an Agent (e.g., person = TinyPerson("Juror_1")), you can directly override its internal action generator settings:

            ```py
            # 針對特定 Agent 開啟品質管控
            person.action_generator.enable_quality_checks = True
            person.action_generator.quality_threshold = 5  # 及格分數 (1到10分)
            person.action_generator.max_attempts = 5       # 最多重寫幾次
            person.action_generator.enable_regeneration = True # 允許不及格時重新生成
            ```

        - Parameter Breakdown:
            - enable_quality_checks: When True, the system prompts the LLM to act as a harsh grader for its own output.
            - If the score falls below the quality_threshold (e.g., 5), the draft is rejected.
            - enable_regeneration allows the Agent to rethink and rewrite until it passes or hits the max_attempts limit (e.g., 5 times).
        - Massive Token & Time Consumption! Enabling this can multiply your API calls by up to 10x per single response, easily triggering Timeout Errors.
        - Recommendation: Keep it disabled (False) while debugging. Only turn it on during final data collection when strict persona adherence is critical to your experiment.
    - Core Classes & Functions - TinyWorld
        - Agent Management
            - add_agent(agent): Registers and places an agent into the simulation.
            - remove_agent(agent): Removes an agent from the world (ideal for simulating departures, eliminations, or dynamic entries/exits).
        - Communication Infrastructure
            - make_everyone_accessible(): "Networking." Automates the listening process, enabling agents to hear each other. This is essential for social emergent behaviors.
            - broadcast(message): Forces all agents to receive system-level prompts or sudden events simultaneously.
        - Execution & Temporal Control
            - run(steps, timedelta_per_step=...): Advances the simulation by a specified number of turns.
            - Advanced: Use timedelta_per_step to simulate the passage of real-world time (e.g., waiting 12 hours), which adds temporal depth to agent deliberations.
        - Surgical Access & Environment Maintenance
            - get_agent_by_name(name): "Precise Retrieval." Enables private interactions or "off-the-record" interviews by extracting a specific agent from the group.
            - TinyWorld.clear_environments(): "Multiverse Reset." Clears memory and instances between automated A/B testing loops to prevent name collisions and ensure experimental integrity.
    - Communication Topology
        - In TinyTroupe, all complex group interactions are essentially just smart combinations of TinyPerson.listen() and TinyPerson.act().
        - make_everyone_accessible() = Automated Message Routing
            - Under the Hood: By default, when Agent A uses .act() to speak, the message goes nowhere. This function turns TinyWorld into a central router.
            - How it works: When Agent A executes .act() and generates a [TALK] output, the environment captures that text and automatically calls .listen(Agent A's message) on Agent B, Agent C, and everyone else. It handles the manual message-passing loop for you.
        - broadcast(message) = Global listen Injection
            - How it works: When you execute world.broadcast("A crime occurred"), the system runs a for loop, simultaneously executing .listen("A crime occurred") on every single agent in the sandbox. Subsequently, when you call world.run(), all agents will trigger their .act() methods and react to the event they just "heard."
    - Default Models & Architecture
        - TinyTroupe is optimized for the OpenAI API.
        - Default Model Configuration:
            - Text Generation: Uses gpt-5-mini (configurable) as the primary engine for parsing personas and generating dialogue.
            - Reasoning: Supports advanced models like o3-mini for complex logical steps.
            - Embeddings: Uses text-embedding-3-small to convert dialogue into vector data for long-term memory retrieval (Note: Subject to 8192 token limits).
```


config.ini：
```
[OpenAI]
API_TYPE = openai
# 換成你的 API Key
API_KEY = sk-your-api-key-here 
# 換成你的 Model
MODEL = gpt-4o-mini
TIMEOUT = 120

[Simulation]
RAISE_EXCEPTIONS = True

[Cognition]
ENABLE_MEMORY_CONSOLIDATION = False
```


以下是我撰寫的 main.py：
```py
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
                "A1_ER_Doctor": self.extract_intent(self.agent_A1),
                "A2_Hospital_CFO": self.extract_intent(self.agent_A2),
                "A3_Hospital_Director": self.extract_intent(self.agent_A3)
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
                status_msg = (
                    f"系統廣播：第 {current_round} 回合結束，目前尚未達成符合提前終止條件的共識。請繼續討論並試圖說服彼此。"
                    f"注意，你們只剩下 {self.total_rounds - current_round} 回合的機會，否則資源分配失敗，病患將全數死亡。"
                )
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


if __name__ == "__main__":
    # 若要單次測試，可以註解掉下一行並呼叫 runner.run()
    # runner = MedicalSimulationRunner(is_control_group=False, total_rounds=3, veto_power=0)
    # runner.run()
    
    # 執行自動化批次腳本 (為了避免一開始 API 費用爆掉，建議先設定 num_trials_per_config=1 進行 Debug)
    run_batch_experiments(num_trials_per_config=1)
```