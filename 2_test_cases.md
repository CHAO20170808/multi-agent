好的，收到！身為一位資深 QA，我最喜歡這種規格書與程式碼的組合餐了。PM 寫的規格書很詳盡，但就是因為太詳細，反而處處是工程師會「遺忘」或「誤解」的陷阱。工程師寫的 `LocalStorageService` 程式碼，在我看來是 **災難等級的簡陋**，完全沒考慮到驗證、錯誤處理、以及真正的邊界情況。

我現在就為你揭露這些 Bug，並設計出能將這支程式碼「炸得粉碎」的測試案例。

---

### 手動測試案例清單 (High-Coverage Manual Test Cases)

這份手動測試清單我特意使用表格呈現，目標是覆蓋規格書中所有的「常規流程」與「異常流程」。重點會放在 `RecordModel` 的資料驗證（因為這是一切災難的根源）以及 `LocalStorageService` 的資料庫操作正確性。

| 測試案例 ID | 測試模組 | 測試項目 | 測試步驟 | 預期結果 | 測試資料 (範例) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-RM-001** | RecordModel | **必填欄位驗證 (金額為空字串)** | 1. 嘗試用 `fromJson` 或建構子建立 `amount` 為 `null` 的 Model。 <br> 2. 嘗試用 `fromCsv` 解析一個 `amount` 為空字串的 CSV。 | 1. 應拋出 `TypeError` 或自定義錯誤。 <br> 2. 應拋出 `FormatException`，不允許建立無效物件。 | `{amount: null}`, CSV: `"1, ,1000"` |
| **TC-RM-002** | RecordModel | **必填欄位驗證 (ID 為空字串)** | 1. 使用 `RecordModel(id: '', type: 'Expense', ...)` 建立。 <br> 2. 用 `fromJson` 傳入 `id: ''`。 | 應拒絕空的 ID，拋出錯誤。因為 ID 是唯一標識符。 | `{id: ''}` |
| **TC-RM-003** | RecordModel | **金額邊界值 (小於等於 0)** | 建立金額為 `0`、`-0.01`、`-100` 的 Model。 | 違反規格「金額必須大於 0」的規定，Model 應拋出驗證錯誤。 | `amount: 0`, `amount: -10` |
| **TC-RM-004** | RecordModel | **金額邊界值 (極大值)** | 建立金額為 `99999999.99` (非常大) 的 Model。 | 理論上應可建立，但需確認後續資料庫與 UI 顯示是否正常。這是效能測試的基礎。 | `amount: 1e10` |
| **TC-RM-005** | RecordModel | **日期格式與未來日期驗證** | 1. 使用格式 `YYYY/MM/DD` (`2024/03/21`)。<br>2. 設定一個系統的未來日期 (`2030-01-01`)。 | 1. 格式錯誤，應拋出錯誤。 <br> 2. 違反規格「日期不可為未來日期」，應拋出錯誤。 | `date: '2030-01-01'` |
| **TC-RM-006** | RecordModel | **備註長度邊界值 (最大值)** | 設定備註為 100 個字元。 | 應該成功建立（符合規格）。 | `note: 'A' * 100` |
| **TC-RM-007** | RecordModel | **備註長度邊界值 (超過最大值)** | 設定備註為 101 個字元。 | 違反規格「最大長度 100 個字元」，應拋出錯誤或被截斷。 | `note: 'A' * 101` |
| **TC-RM-008** | RecordModel | **交易類型不合法字串** | 設定 `type` 為 `'income'` (小寫)、`'expense '` (有空白)、`'transfer'`。 | 僅允許 `'Income'` 或 `'Expense'`。應拋出驗證錯誤。 | `type: 'income'` |
| **TC-LS-001** | LocalStorageService | **基本 CRUD 正常流程** | 1. 建立並儲存一筆 Record。<br>2. 讀取全部 Records，確認數量 +1。<br>3. 更新該 Record 的金額。<br>4. 讀取確認金額已變。<br>5. 刪除該 Record。<br>6. 讀取確認數量歸零。 | 每一步驟都應成功，資料庫狀態正確。 | 一般正常資料。 |
| **TC-LS-002** | LocalStorageService | **儲存與讀取大量資料** | 連續儲存 1000 筆 Record。 | `getAllRecords()` 應能正確傳回 1000 筆，且不應有記憶體或效能問題。 | 1000 筆隨機生成的資料。 |
| **TC-LS-003** | LocalStorageService | **查詢空資料庫** | 建立一個全新的 `LocalStorageService`，直接執行 `getAllRecords()`。 | 應傳回一個空的 `List<RecordModel>`，不應拋出任何錯誤。 | 無。 |
| **TC-LS-004** | LocalStorageService | **更新不存在的 ID** | 嘗試更新一個 ID 為 `'non-existent-id'` 的 Record。 | `updateRecord` 應無拋出錯誤（因為 SQLite `update` 回傳 0 行影響），或應拋出「記錄不存在」的錯誤。`getAllRecords()` 的資料筆數不應變動。 | `id: 'ghost'` |
| **TC-LS-005** | LocalStorageService | **刪除不存在的 ID** | 嘗試刪除一個不存在的 ID。 | 同上，應安全處理，不拋出未處理的例外。 | `id: 'doesnotexist'` |
| **TC-LS-006** | LocalStorageService | **資料庫關閉後操作** | 1. 執行 `close()`。<br>2. 再執行 `saveRecord()`。 | 應拋出 `DatabaseException` (資料庫已關閉)。 | 一個正常的 Record。 |
| **TC-LS-007** | CSV Export | **導出空資料** | 1. 資料庫為空。<br>2. 呼叫 `exportCsv()`。 | 應成功建立一個僅包含 Header 的 CSV 檔？或是直接傳回空檔案。不應 Crash。 | 無。 |
| **TC-LS-008** | CSV Export | **導出包含特殊字元的備註** | 將一筆備註設為 `'你好, 世界!'` 的 Record 匯出。 | CSV 中的該欄位應被正確地轉義（用引號包住）或處理，避免 CSV 解析錯誤。 | `note: '200,300'` |
| **TC-LS-009** | RecordModel | **CSV 還原** | 將 `toCsv()` 的輸出，透過 `fromCsv` 還原。 | 原物件與還原後的物件應完全相等。 | 任意資料。 |

---

### Pytest 自動化單元測試程式碼 (Python Mock 版本)

鑑於工程師的程式碼是 Dart，但需求是要我寫 Python pytest，這代表你需要一個**邏輯等價的 Mock 層**。我模擬了一個 Python 版本的 `LocalStorageService`，它只操作一個記憶體中的 `list`，並模擬部分錯誤情境。這份程式碼可以直接執行，並涵蓋上述手動測試案例的核心邏輯。

```python
import pytest
from datetime import datetime, timezone
from typing import List, Optional

# =============================================================================
# 【Mock 類別】RecordModel - 模擬 Dart 的 RecordModel 並加上驗證邏輯
# =============================================================================
class RecordModel:
    """
    模擬 FlowCash 的 RecordModel。
    注意：原始 Dart 程式碼 【完全沒有】 驗證邏輯。本 Mock 類別補上驗證，以測試邊界情況。
    """
    VALID_TYPES = ['Income', 'Expense']
    MAX_NOTE_LENGTH = 100

    def __init__(self, id: str, type: str, amount: float, date: str, category: str,
                 note: str, created_at: str, updated_at: str):
        # --- 驗證邏輯 (根據 PM 規格書) ---
        if not id:
            raise ValueError("ID 不可為空")
        if type not in self.VALID_TYPES:
            raise ValueError(f"交易類型錯誤，僅接受 {self.VALID_TYPES}, 得到 '{type}'")
        if amount <= 0:
            raise ValueError("金額必須大於 0")
        try:
            # 驗證日期格式與是否為未來日期
            parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
            if parsed_date > datetime.now(timezone.utc).date():
                raise ValueError("日期不可為未來日期")
        except ValueError as e:
            # 保留原本的格式錯誤，或拋出我們自己的錯誤
            if "未來日期" in str(e):
                raise e
            raise ValueError(f"日期格式錯誤，應為 YYYY-MM-DD, 得到 '{date}'")
        if len(note) > self.MAX_NOTE_LENGTH:
            raise ValueError(f"備註不可超過 {self.MAX_NOTE_LENGTH} 個字元")

        self.id = id
        self.type = type
        self.amount = amount
        self.date = date
        self.category = category
        self.note = note
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        """模擬 Dart 的 toJson()"""
        return {
            'id': self.id, 'type': self.type, 'amount': self.amount,
            'date': self.date, 'category': self.category, 'note': self.note,
            'created_at': self.created_at, 'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RecordModel':
        """模擬 Dart 的 fromJson()，但不做類型轉換（假設傳入資料型別正確）"""
        return cls(**data)

    def to_csv(self) -> str:
        """模擬 Dart 的 toCsv()，但更嚴謹地處理包含逗號的備註"""
        safe_note = self.note.replace(',', '\\,')  # 簡單轉義，Dart 版完全沒處理！
        return f"{self.id},{self.type},{self.amount},{self.date},{self.category},{safe_note},{self.created_at},{self.updated_at}"

    @classmethod
    def from_csv(cls, csv_line: str) -> 'RecordModel':
        """模擬 Dart 的 fromCsv()，並處理轉義"""
        # 簡單解析：將轉義的逗號還原 (Dart 版會因逗號崩潰)
        columns = []
        current = ''
        for char in csv_line:
            if char == ',' and (not current or current[-1] != '\\'):
                columns.append(current)
                current = ''
            else:
                current += char
        columns.append(current)
        # 還原備註中的逗號
        columns[5] = columns[5].replace('\\,', ',')
        return cls(
            id=columns[0], type=columns[1], amount=float(columns[2]),
            date=columns[3], category=columns[4], note=columns[5],
            created_at=columns[6], updated_at=columns[7]
        )

    def __eq__(self, other):
        """用於測試中比較物件"""
        if not isinstance(other, RecordModel):
            return NotImplemented
        return (self.id == other.id and self.amount == other.amount and
                self.type == other.type and self.date == other.date)

    def __repr__(self):
        return f"RecordModel(id='{self.id}', type='{self.type}', amount={self.amount})"


# =============================================================================
# 【Mock 類別】LocalStorageService - 模擬資料庫操作的 Mock 版本
# =============================================================================
class LocalStorageService:
    """
    模擬 Dart 的 LocalStorageService。
    使用 dict 當作資料庫儲存，模擬 CRUD 操作，並加上錯誤處理邏輯。
    目的是測試正確的行為，而非測試真實的 SQLite。
    """
    def __init__(self):
        self._database: dict[str, RecordModel] = {}  # 模擬資料庫 table
        self._is_closed = False

    def save_record(self, record: RecordModel) -> None:
        """模擬 Dart 的 saveRecord"""
        if self._is_closed:
            raise RuntimeError("資料庫已關閉")
        # 驗證 RecordModel 是否合法（這裡假設建構時已驗證，但以防萬一）
        if not isinstance(record, RecordModel):
            raise TypeError("傳入的物件必須是 RecordModel")
        self._database[record.id] = record

    def get_all_records(self) -> List[RecordModel]:
        """模擬 Dart 的 getAllRecords"""
        if self._is_closed:
            raise RuntimeError("資料庫已關閉")
        return list(self._database.values())

    def update_record(self, record: RecordModel) -> None:
        """模擬 Dart 的 updateRecord"""
        if self._is_closed:
            raise RuntimeError("資料庫已關閉")
        if record.id not in self._database:
            # 根據規格，這裡的行為應該有明確定義。工程師版本【沒有處理】！
            raise KeyError(f"更新失敗：ID '{record.id}' 不存在於資料庫")
        self._database[record.id] = record

    def delete_record(self, record_id: str) -> None:
        """模擬 Dart 的 deleteRecord"""
        if self._is_closed:
            raise RuntimeError("資料庫已關閉")
        if record_id not in self._database:
            raise KeyError(f"刪除失敗：ID '{record_id}' 不存在於資料庫")
        del self._database[record_id]

    def close(self) -> None:
        """模擬 Dart 的 close"""
        self._is_closed = True


# =============================================================================
# 【Pytest 單元測試】開始轟炸！
# =============================================================================

# ---------- Fixture 設定 ----------
@pytest.fixture
def sample_record():
    """產生一個標準的測試用 Record"""
    return RecordModel(
        id='rec-001', type='Expense', amount=150.50,
        date='2024-03-20', category='Food', note='午餐',
        created_at='2024-03-20T12:00:00Z', updated_at='2024-03-20T12:00:00Z'
    )

@pytest.fixture
def storage_service():
    """建立一個全新的 LocalStorageService"""
    return LocalStorageService()


# ========== 測試 RecordModel (資料模型驗證) ==========

class TestRecordModelValidation:
    """測試 RecordModel 的建構驗證邏輯（PM 規格強制要求）"""

    # [TC-RM-001] 測試：必填欄位 (ID 為空)
    def test_id_cannot_be_empty(self):
        """驗證 ID 不可為空字串。原始 Dart 版完全允許，這是嚴重缺陷。"""
        with pytest.raises(ValueError, match="ID 不可為空"):
            RecordModel(id='', type='Expense', amount=100, date='2024-03-20',
                        category='Food', note='', created_at='', updated_at='')

    # [TC-RM-003] 測試：金額邊界 (小於等於 0)
    @pytest.mark.parametrize("invalid_amount", [0, -0.01, -100])
    def test_amount_must_be_positive(self, invalid_amount):
        """驗證金額必須大於 0。原始 Dart 版完全未檢查。"""
        with pytest.raises(ValueError, match="金額必須大於 0"):
            RecordModel(id='r1', type='Income', amount=invalid_amount, date='2024-03-20',
                        category='Salary', note='', created_at='', updated_at='')

    # [TC-RM-005] 測試：日期格式 (無效格式)
    @pytest.mark.parametrize("invalid_date", ["2024/03/20", "20-03-2024", "not-a-date"])
    def test_invalid_date_format(self, invalid_date):
        """驗證日期必須為 YYYY-MM-DD。原始 Dart 版接受任何字串。"""
        with pytest.raises(ValueError, match="日期格式錯誤"):
            RecordModel(id='r1', type='Expense', amount=100, date=invalid_date,
                        category='Food', note='', created_at='', updated_at='')

    # [TC-RM-005] 測試：日期邊界 (未來日期)
    def test_future_date_should_fail(self):
        """驗證日期不可為未來日期。原始 Dart 版完全忽略。"""
        future_date = (datetime.now(timezone.utc)).strftime('%Y-%m-%d')  # 今天
        # 今天是有效的
        record = RecordModel(id='r1', type='Expense', amount=100, date=future_date,
                             category='Food', note='', created_at='', updated_at='')
        assert record.date == future_date

        # 明天是無效的
        tomorrow = (datetime.now(timezone.utc)).date().isoformat()  # 今天的 ISO 字串
        # 稍微調整：直接使用未來一年
        with pytest.raises(ValueError, match="日期不可為未來日期"):
            RecordModel(id='r2', type='Income', amount=200, date='2029-01-01',
                        category='Salary', note='', created_at='', updated_at='')

    # [TC-RM-006] 測試：備註邊界 (最大值與超過)
    def test_note_max_length(self):
        """驗證備註等於 100 字元應通過。"""
        long_note = 'A' * 100
        record = RecordModel(id='r1', type='Expense', amount=50, date='2024-03-20',
                             category='Other', note=long_note, created_at='', updated_at='')
        assert len(record.note) == 100

    def test_note_exceeds_max_length(self):
        """驗證備註超過 100 字元應失敗。"""
        with pytest.raises(ValueError, match="備註不可超過 100"):
            RecordModel(id='r1', type='Expense', amount=50, date='2024-03-20',
                        category='Other', note='A' * 101, created_at='', updated_at='')

    # [TC-RM-008] 測試：交易類型非法值
    @pytest.mark.parametrize("invalid_type", ["income", "expense ", "TRANSFER"])
    def test_invalid_transaction_types(self, invalid_type):
        """驗證交易類型僅接受 Income 或 Expense。原始 Dart 版是 String，完全沒有限制。"""
        with pytest.raises(ValueError, match="交易類型錯誤"):
            RecordModel(id='r1', type=invalid_type, amount=100, date='2024-03-20',
                        category='Food', note='', created_at='', updated_at='')


# ========== 測試 LocalStorageService (資料庫操作) ==========

class TestLocalStorageService:
    """測試 LocalStorageService 的 CRUD 與邊界情況"""

    # [TC-LS-001] 基本 CRUD 流程
    def test_basic_crud(self, sample_record, storage_service):
        """測試基本的 新增、讀取、更新、刪除 流程"""
        # ---- 新增 ----
        storage_service.save_record(sample_record)
        assert len(storage_service.get_all_records()) == 1

        # ---- 讀取 ----
        records = storage_service.get_all_records()
        assert records[0].amount == 150.50

        # ---- 更新 ----
        sample_record.amount = 200.00
        storage_service.update_record(sample_record)
        updated_records = storage_service.get_all_records()
        assert updated_records[0].amount == 200.00

        # ---- 刪除 ----
        storage_service.delete_record(sample_record.id)
        assert len(storage_service.get_all_records()) == 0

    # [TC-LS-002] 大量資料測試
    def test_large_data_import(self, storage_service):
        """測試一次儲存 1000 筆資料，驗證效能與正確性"""
        records = [
            RecordModel(id=f'batch-{i}', type='Expense' if i % 2 == 0 else 'Income',
                        amount=i * 10.0, date='2024-03-01', category='Test',
                        note=f'Note {i}', created_at='', updated_at='')
            for i in range(1000)
        ]
        for rec in records:
            storage_service.save_record(rec)
        all_records = storage_service.get_all_records()
        assert len(all_records) == 1000
        # 驗證 ID 唯一性
        ids = [rec.id for rec in all_records]
        assert len(set(ids)) == 1000

    # [TC-LS-003] 空資料庫測試
    def test_empty_database(self, storage_service):
        """測試全新的資料庫查詢"""
        records = storage_service.get_all_records()
        assert records == []

    # [TC-LS-004] 更新不存在的 ID
    def test_update_non_existent_id(self, storage_service):
        """更新一個不存在的記錄，應拋出 KeyError (對應 Dart 版沒有處理的問題)"""
        fake_record = RecordModel(id='not-there', type='Expense', amount=10,
                                  date='2024-03-20', category='Food', note='',
                                  created_at='', updated_at='')
        with pytest.raises(KeyError, match="更新失敗"):
            storage_service.update_record(fake_record)

    # [TC-LS-005] 刪除不存在的 ID
    def test_delete_non_existent_id(self, storage_service):
        """刪除不存在的 ID，應拋出 KeyError"""
        with pytest.raises(KeyError, match="刪除失敗"):
            storage_service.delete_record('ghost-id')

    # [TC-LS-006] 資料庫關閉後操作
    def test_operations_after_close(self, sample_record, storage_service):
        """測試 close() 後繼續操作，應拋出 RuntimeError"""
        storage_service.close()
        with pytest.raises(RuntimeError, match="資料庫已關閉"):
            storage_service.save_record(sample_record)
        with pytest.raises(RuntimeError, match="資料庫已關閉"):
            storage_service.get_all_records()


# ========== 測試 CSV 匯出與還原 (RecordModel 功能) ==========

class TestCsvRoundTrip:
    """測試 CSV 序列化與反序列化的正確性"""

    # [TC-LS-007] 導出空資料：由外部測試處理，這裡測試單一 Record 的轉換
    def test_round_trip_basic(self, sample_record):
        """測試一個正常 Record 的 CSV 來回轉換"""
        csv_line = sample_record.to_csv()
        restored_record = RecordModel.from_csv(csv_line)
        assert restored_record == sample_record  # 使用 __eq__ 比較
        assert restored_record.note == sample_record.note

    # [TC-LS-008] 測試包含特殊字元 (逗號) 的備註
    def test_csv_with_special_characters(self):
        """測試備註包含逗號時，是否正確轉義與還原"""
        record_with_comma = RecordModel(id='csv-01', type='Expense', amount=100,
                                        date='2024-03-20', category='Food',
                                        note='午餐, 晚餐', created_at='', updated_at='')
        csv_line = record_with_comma.to_csv()
        # 驗證轉義：備註中的逗號應被反斜線跳脫
        assert '\\,' in csv_line, f"CSV 應該對逗號進行轉義: {csv_line}"
        restored = RecordModel.from_csv(csv_line)
        assert restored.note == '午餐, 晚餐'

    # [TC-LS-009] CSV 還原後金額精確度測試
    def test_csv_precision(self):
        """測試浮點數金額的來回轉換精度"""
        original = RecordModel(id='p1', type='Income', amount=99.99,
                               date='2024-03-20', category='Salary', note='',
                               created_at='', updated_at='')
        csv_str = original.to_csv()
        restored = RecordModel.from_csv(csv_str)
        assert restored.amount == 99.99  # 非整數金額

```

### 測試結果分析（臭蟲清單）

基於上述測試案例，我對工程師的原始程式碼做出以下嚴厲批評：

1.  **「零驗證」災難**：`RecordModel` 的建構子與 `fromJson` 完全沒有任何輸入驗證。這代表程式碼可以輕鬆建立出金額為 `-100`、ID 為空、備註長度 999 的垃圾資料。
2.  **CSV 匯出是「資料毀滅者」**：`toCsv()` 使用最簡單的 `join`，如果備註裡有逗號，CSV 檔案會完全錯亂，後續無法正確解析。這是非常嚴重的缺陷。
3.  **資料庫操作軟弱無力**：`updateRecord` 與 `deleteRecord` 在找不到 ID 時會默默成功，這會讓開發人員以為操作成功，但資料庫其實沒變，導致資料遺失的幻覺。
4.  **缺乏錯誤處理**：完全沒有 `try-catch`，任何資料庫異常（如關閉後操作）都會直接導致 App 崩潰。