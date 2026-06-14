# FlowCash 記帳 App 核心程式碼
## 1. 記帳紀錄的資料模型 (Record Model)
### record_model.dart
```dart
/// 記帳紀錄的資料模型
class RecordModel {
  /// 紀錄 ID
  String id;

  /// 交易類型 (Income/Expense)
  String type;

  /// 金額
  double amount;

  /// 日期
  String date;

  /// 分類
  String category;

  /// 備註
  String note;

  /// 建立時間
  String createdAt;

  /// 更新時間
  String updatedAt;

  RecordModel({
    required this.id,
    required this.type,
    required this.amount,
    required this.date,
    required this.category,
    required this.note,
    required this.createdAt,
    required this.updatedAt,
  });

  /// 將 JSON 轉換為 RecordModel
  factory RecordModel.fromJson(Map<String, dynamic> json) {
    return RecordModel(
      id: json['id'],
      type: json['type'],
      amount: json['amount'],
      date: json['date'],
      category: json['category'],
      note: json['note'],
      createdAt: json['createdAt'],
      updatedAt: json['updatedAt'],
    );
  }

  /// 將 RecordModel 轉換為 JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type,
      'amount': amount,
      'date': date,
      'category': category,
      'note': note,
      'createdAt': createdAt,
      'updatedAt': updatedAt,
    };
  }

  /// 將 RecordModel 轉換為 CSV
  String toCsv() {
    return '$id,$type,$amount,$date,$category,$note,$createdAt,$updatedAt';
  }

  /// 將 CSV 轉換為 RecordModel
  factory RecordModel.fromCsv(String csv) {
    final columns = csv.split(',');
    return RecordModel(
      id: columns[0],
      type: columns[1],
      amount: double.parse(columns[2]),
      date: columns[3],
      category: columns[4],
      note: columns[5],
      createdAt: columns[6],
      updatedAt: columns[7],
    );
  }
}
```

## 2. 本地資料儲存服務 (LocalStorageService)
### local_storage_service.dart
```dart
/// 本地資料儲存服務
class LocalStorageService {
  /// SQLite 資料庫
  final _database = await openDatabase('flowcash.db', version: 1);

  /// 儲存紀錄
  Future<void> saveRecord(RecordModel record) async {
    await _database.insert('records', record.toJson());
  }

  /// 取得所有紀錄
  Future<List<RecordModel>> getAllRecords() async {
    final records = await _database.query('records');
    return records.map((record) => RecordModel.fromJson(record)).toList();
  }

  /// 更新紀錄
  Future<void> updateRecord(RecordModel record) async {
    await _database.update('records', record.toJson(), where: 'id = ?', whereArgs: [record.id]);
  }

  /// 刪除紀錄
  Future<void> deleteRecord(String id) async {
    await _database.delete('records', where: 'id = ?', whereArgs: [id]);
  }

  /// 關閉資料庫
  Future<void> close() async {
    await _database.close();
  }
}
```

## 3. CSV 導出服務 (CsvExportService)
### csv_export_service.dart
```dart
/// CSV 導出服務
class CsvExportService {
  /// 導出 CSV
  Future<void> exportCsv(List<RecordModel> records) async {
    final csv = records.map((record) => record.toCsv()).join('\n');
    final file = File('records.csv');
    await file.writeAsString(csv);
  }
}
```

## 4. 使用範例
### main.dart
```dart
import 'package:flutter/material.dart';
import 'package:flowcash/record_model.dart';
import 'package:flowcash/local_storage_service.dart';
import 'package:flowcash/csv_export_service.dart';

void main() async {
  final localStorageService = LocalStorageService();
  final csvExportService = CsvExportService();

  // 儲存紀錄
  final record = RecordModel(
    id: '1',
    type: 'Income',
    amount: 100,
    date: '2023-03-01',
    category: 'Salary',
    note: 'Salary',
    createdAt: '2023-03-01 12:00:00',
    updatedAt: '2023-03-01 12:00:00',
  );
  await localStorageService.saveRecord(record);

  // 取得所有紀錄
  final records = await localStorageService.getAllRecords();
  print(records);

  // 更新紀錄
  record.amount = 200;
  await localStorageService.updateRecord(record);

  // 刪除紀錄
  await localStorageService.deleteRecord('1');

  // 導出 CSV
  final recordsForCsv = await localStorageService.getAllRecords();
  await csvExportService.exportCsv(recordsForCsv);

  // 關閉資料庫
  await localStorageService.close();
}
```