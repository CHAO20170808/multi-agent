import os
import litellm  # 💡 加這行
from crewai import Agent, Task, Crew, Process, LLM
# 💡 萬用解：隨便塞一個假 key 給 OpenAI 變數，堵住 LiteLLM 的檢查口
# 因為我們有明確設定 base_url，實際發出請求時會走 NVIDIA，所以這個假 key 不會影響 NVIDIA 的認證
os.environ["OPENAI_API_KEY"] = "fake-key-to-bypass-litellm-check"

# 💡 直接設定 LiteLLM 全域 timeout，這樣才會真的生效
litellm.request_timeout = 600  # 10 分鐘

# 1. 遠端設定：改成 crewai 原生支援的 deepseek 格式
remote_deepseek_llm = LLM(
    model="deepseek/deepseek-v4-flash",        # 💡 關鍵：把 openai/ 改成 deepseek/
    api_key=os.environ.get("Deepseek_API_KEY"), # 保持讀取你的 Windows 變數
    # base_url 也可以拔掉了，crewai 原生支援 deepseek 就會自己導向官方 API
    temperature=0.7
)

# 2. 本地設定：對接你的 llama-server.exe (Gemma-4-26B)
local_gemma_llm = LLM(
    model="openai/gemma-4-26b",              
    base_url="http://localhost:8080/v1",     # 指向你畫面上啟動的 8080 連接埠
    api_key="fake-key-for-local"             # llama-server 不需要 key，但欄位不能留空
)

#3.遠端設定: 使用nvidia的免費模型，nvidia/nemotron-3-ultra-550b-a55b
# 💡 新增 NVIDIA 超大模型設定：Nemotron-4 340B / Nemotron-3 (負責 Coding)
# 註：NVIDIA API 也是 OpenAI 相容格式，所以開頭一樣用 openai/
# 💡 NVIDIA 官方規格的 CrewAI 宣告方式
"""nvidia_llm = LLM(
    model="openai/nvidia/nemotron-3-ultra-550b-a55b", # 💡 換上你想用的 550b 模型 ID
    api_key=os.environ.get("NVIDIA_API_KEY"),         # 讀取 Windows 的 NVIDIA 金鑰
    base_url="https://integrate.api.nvidia.com/v1",    # NVIDIA 官方 API 端點
    temperature=0.7,                                  # 可以依官方預設調成 1.0，或 0.7 讓程式碼更穩定
    
    # 💡 關鍵：把官方規定的特殊「思考模式」參數直接塞進 extra_body
    extra_body={
        "chat_template_kwargs": {
            "enable_thinking": True
        },
        "reasoning_budget": 16384
    }
)"""

"""# 3. 遠端設定: 使用 nvidia 的免費模型
# 💡 修正後：直接給 model 名稱，並在前面加上 openai/，讓 LiteLLM 知道是 OpenAI 相容接口
# 這樣它就不會誤認為是 OpenAI 官方模型而去找 OPENAI_API_KEY 了
nvidia_llm = LLM(
    model="openai/nvidia/nemotron-3-ultra-550b-a55b", 
    api_key=os.environ.get("NVIDIA_API_KEY"),         # 保持讀取 NVIDIA 金鑰
    base_url="https://integrate.api.nvidia.com/v1",    # NVIDIA 官方 API 端點
    temperature=0.7,
    
    # 💡 如果上面依然報錯，請試著把 model 改成以下這行更純粹的 OpenAI 相容寫法：
    # model="openai/nemotron-3-ultra-550b-a55b",
    
    extra_body={
        "chat_template_kwargs": {
            "enable_thinking": True
        },
        "reasoning_budget": 16384
    }
)"""
nvidia_llm = LLM(
    model="openai/meta/llama-3.3-70b-instruct",
    api_key=os.environ.get("NVIDIA_API_KEY"),
    base_url="https://integrate.api.nvidia.com/v1",
    temperature=0.7,
    timeout=600,  # 10 分鐘
    #extra_body={
    #    "chat_template_kwargs": {"enable_thinking": True},
    #    "reasoning_budget": 2048  # 💡 從 16384 降到 2048 先測試
    #}
)





# 建立 Agents
draft_researcher = Agent(
    role="資深智慧硬體與行動應用產品經理",
    goal="將使用者模糊的產品想法，轉化為邏輯嚴密、邊界清晰的繁體中文軟體功能規格書(Functional Spec)",
    backstory="你是一位在軟體業界待了 15 年的資深 PM。你非常注重使用者體驗、異常流程處理（例如網路斷線、資料欄位空白、格式錯誤）以及資料隱私。你產出的規格書結構嚴謹，能讓工程師與測試人員完全理解開發目標。",
    verbose=True,
    llm=local_gemma_llm  
)

# 💡 工程師 (換成 NVIDIA 的 550B/340B 超大型模型！)
flutter_developer = Agent(
    role="資深 Flutter 行動開發工程師",
    goal="根據功能規格書，使用 Clean Architecture 架構，編寫出高品質、結構清晰且可測試的 Flutter 核心程式碼。",
    backstory="你是一位精通 Flutter 與 Dart 的資深工程師。你寫的程式碼完全符合 SOLID 原則，且每個 Layout 都有良好的元件拆解。",
    verbose=True,
    llm=nvidia_llm  # 💡 關鍵：直接在這裡把 model 換成 nvidia_llm！
)

senior_editor = Agent(
    role="資深軟體測試與自動化架構師",
    goal="根據 PM 提供的功能規格書，設計出覆蓋率極高的測試案例(Test Cases)，並生成對應的自動化測試腳本框架。",
    backstory="你是一位極度挑剔、專門找 Bug 的測試專家。你精通等價劃分、邊界值分析等測試理論。你擅長從規格書中找出潛在的邏輯漏洞，並能熟練運用 Python 的 pytest 或 Cypress 撰寫 E2E/整合測試腳本。",
    verbose=True,
    llm=remote_deepseek_llm  
)

# 建立 Tasks 
task1 = Task(
    # 💡 修正：讓 PM 來拆解模糊需求
    description="分析使用者的模糊想法：『我想做一個可以記錄每天生活日常收支紀錄、並能同步紀錄至雲端與導出 CSV 檔的 Flutter 行動 App。』請幫忙規劃出完整的 Functional Spec，必須包含功能模組拆解、輸入欄位驗證規則，以及異常流程處理。",
    expected_output="一份 Markdown 格式、結構清晰的繁體中文功能規格書。",
    agent=draft_researcher,
    output_file="1_functional_spec.md"  # 💡 就在這裡加這一行
)

# 💡 2.5 的 Coding 任務：完全不用改內容，它會自動交給上面的 flutter_developer (NVIDIA 模型) 執行
task_code_generation = Task(
    description=(
        "仔細閱讀 Task 1 產出的功能規格書。請為 Flutter App 實作這個記帳 App 實作出以下核心 Dart 程式碼：\n"
        "1. 記帳紀錄的資料模型 (Record Model)，包含 JSON 與 CSV 的轉換邏輯。\n"
        "2. 本地資料儲存服務 (LocalStorageService)，使用實體檔案(File)或 SQLite 處理資料增刪查改(CRUD)。\n"
        "請確保程式碼包含完整的繁體中文註解，並且將架構分開，不要全部擠在同一個程式碼區塊。"
    ),
    expected_output="一份 Markdown 檔案，裡面包含乾淨、分層的 Flutter 核心服務與模型類別(Dart Code)。",
    agent=flutter_developer,  # 💡 指向使用了 NVIDIA 模型的 Agent
    output_file="3_flutter_core_code.md"
)

task2 = Task(
# 💡 修正：明確指引 QA 同時閱讀規格書（Task 1）與程式碼（Task 2.5/code_generation）
    description="仔細閱讀 PM 的功能規格書與工程師寫出的核心程式碼。請設計出覆蓋率極高的手動測試案例清單，並針對工程師的 LocalStorageService 撰寫對應的 Python pytest 自動化單元測試程式碼骨架（包含 Mock 資料邏輯與繁體中文註解）。",
    expected_output="一份包含手動測試案例清單，以及現成可用的 pytest 自動化測試腳本內容（以 Markdown 程式碼區塊呈現）。",
    agent=senior_editor,
    output_file="2_test_cases.md"
)

# 組裝團隊
my_crew = Crew(
    agents=[draft_researcher, flutter_developer, senior_editor],
    tasks=[task1, task_code_generation, task2],
    process=Process.sequential, # 順序執行：Task 1 的結果會自動餵給 Task 2
    verbose=True
)

if __name__ == "__main__":
    print("=== CrewAI 本地/遠端/NVIDIA 三核心夢幻團隊啟動 ===")
    result = my_crew.kickoff()
    print("\n=== 任務完成 ===")