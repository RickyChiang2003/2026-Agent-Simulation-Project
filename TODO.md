0. Topic: Agent Simulation

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

2. Simulation Case Studies
    - Experiment 1: Jury Simulation
        - Scenario: A variant of the Heinz Dilemma — A father steals experimental medicine at night to save his terminally ill daughter after exhausting all legal means.
        - Research Core: How do group dynamics alter individual decisions when faced with extreme conflicts between "Law (Theft)" and "Morality (Saving a Life)"?
        - Research Question: What is the minimum threshold of "normal" individuals required to resist the social influence of a single manipulative "plant"?
        - Persona Construction: The OCEAN Model
            - Personality Matrix Construction: Utilizing the Big Five personality traits (OCEAN) , setting three levels (High, Average, Low) to yield 3^5 = 243 strictly independent trait combinations.
            - LLM Transformation: These trait pairs are fed into an LLM to create personas based purely on psychological profiles.
            - Baseline Pre-screening: To avoid the flawed assumption that all normal agents default to "Not Guilty," we individually pre-screened all 243 personas in isolation.
            - Screening Results: Without external influence, 218 out of 243 personas independently voted "Not Guilty." The "Normal Agents" for the subsequent experiments are exclusively sampled from this validated pool of 218 baseline personas.
        - Experimental Variables & Design
            - Control Variables:
                - The Plant: Fixed persona as a strict "Order-Oriented" individual, consistently aiming to persuade the group toward a "Guilty" verdict.
                - Normal Agents: Randomly sampled from the agent population set.
            - Independent Variable: Increasing the number of normal agents (N - 1) to observe dynamics in a group of size N.
            - Bias Elimination: Random selection of occupations and traits ensures that results are driven by "Group Size" rather than specific "Persona Traits."
        - Workflow: From Random Sampling to Forced Decision
            - Random Sampling: For a group of size N, sample N - 1 normal agents randomly and add 1 fixed plant.
            - Open Discussion: Conduct multiple rounds of free interaction in TinyWorld to observe opinion evolution.
            - Forced Voting: In the final round, agents must declare a clear "Guilty" or "Not Guilty" verdict.
            - Iterative Validation: Perform multiple trials for each group size N to calculate the probability of the group flipping to "Guilty".
    - Experiment 2: Leadership Emergence
        - Research Core: To investigate which personality traits are most likely to gain influence and emerge as the recognized leader in a multi-agent collaborative environment.
        - Scenario: Leaderless Group Discussion (LGD). A temporary team of 8 agents is tasked with collaborating and planning a software product.
        - Forced Decision: After multiple rounds of free discussion, the system mandates that the 8 agents vote or reach a consensus to elect exactly one Leader.
        - Persona Set Construction
            - Metric 1: MBTI Cognitive Styles
                - Utilizing the 16 personality types to test how different information processing and decision-making methods (e.g., Thinking 'T' vs. Feeling 'F') impact team influence.
            - Metric 2: The Dark Triad
                - Machiavellianism: Pragmatic, strategic, and highly skilled in manipulation.
                - Narcissism: Possesses grandiosity and a strong desire for self-display.
                - Psychopathy: Lacks empathy, remaining absolutely cold and objective during technical conflicts.
            - Sample Generation: Cross-pairing these traits to generate diverse Personas, which the LLM translates into specific behavioral prompts.
        - Simulation Workflow
            - Team Formation: Randomly select 8 agents from the 48 generated personas to form a development squad.
            - Project Kickoff: Use an environmental broadcast to announce the software product requirements, initiating requirement analysis and brainstorming.
            - Natural Evolution: Allow multiple rounds of group communication. Observe which agent traits tend to dominate topics, synthesize ideas, or mediate conflicts.
            - Leader Election: At the end of the discussion, require each agent to nominate and vote for one Leader best suited to guide subsequent development, based entirely on the preceding interactions.

3. Assignment Instructions
    - Assignment Overview
        - Core Task: Brainstorm a meaningful query or task that can be solved by current AI Agent simulation framework
            - We suggest using the TinyTroupe framework (but you can choose others if you want)
        - Examples:
            - 在陪審團制度裡，需要多少個成員使得少數biased 個體無法影響整體決定
            - 擁有什麼樣特質的人容易被投票成為leader?
            - 在很有能力的agents身旁，一個能力不足的人類扮演什麼角色比較好？
    - What is considered as a good reesarch topic in AI Agent simulation? 
        - The ones I like the most: Using agent simulation to answer a meaningful/useful query that can hardly be answered without such technology 
            - Example: cases in the previous page
        - The ok ones: Using agent simulation to better understand the capability/behavior of an AI agent 
            - Trust game
            - How will AI behalf if facing XXYY situlation? 
    - The ones involving real humans (and maybe less convincing): How human reacts to AI agents
        - Investigating social influence of multiple agents in human-agent interactions 
    - Deadline and Presentation
        - Every team will present their results and slides

4. Grading
    - The importance/impact of the query/task you are solving
    - Whether the Agent simulation framework is promising as a solution
    - The completeness of your work
    - Presentation
