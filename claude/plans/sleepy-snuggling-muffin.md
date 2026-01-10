# 品番EC公開作業リスト フィルタ機能改善

## 概要

品番EC公開作業リストのフィルタ機能を以下のように改善する：
1. 既存の公開ステータスフィルタを工程ステータスフィルタに**置き換え**
2. 担当者フィルタを追加（いずれかの工程の担当であればマッチ）
3. 担当者リストはAPIから動的に取得

---

## 修正対象ファイル

1. `src/types/product.ts` - WorkflowStatus型に `in_progress` を追加
2. `src/app/api/products/route.ts` - 工程ステータス・担当者フィルタ追加
3. `src/app/api/assignees/route.ts` - **新規作成** 担当者一覧API
4. `src/app/products/page.tsx` - フィルタUI更新、作業中ステータスの表示対応

---

## 実装計画

### 0. 型定義更新 (`src/types/product.ts`)

```typescript
// 変更前
export type WorkflowStatus = "pending" | "done";

// 変更後
export type WorkflowStatus = "pending" | "in_progress" | "done";

export const WORKFLOW_STATUS_LABELS: Record<WorkflowStatus, string> = {
  pending: "未完了",
  in_progress: "作業中",  // 追加
  done: "完了",
};
```

**テーブル表示（page.tsx）:**
```typescript
const WORKFLOW_STATUS_DISPLAY = {
  pending: { label: "−", bgClass: "bg-gray-100", textClass: "text-gray-400" },
  in_progress: { label: "中", bgClass: "bg-yellow-100", textClass: "text-yellow-700" },  // 追加
  done: { label: "済", bgClass: "bg-green-100", textClass: "text-green-700" },
};
```

### 1. 担当者一覧API（新規）

**エンドポイント:** `GET /api/assignees`

```sql
SELECT DISTINCT assignee
FROM (
  SELECT photo_assignee AS assignee FROM `mart.ec_publish_products` WHERE photo_assignee IS NOT NULL
  UNION DISTINCT
  SELECT retouch_assignee FROM `mart.ec_publish_products` WHERE retouch_assignee IS NOT NULL
  UNION DISTINCT
  SELECT comment_assignee FROM `mart.ec_publish_products` WHERE comment_assignee IS NOT NULL
  UNION DISTINCT
  SELECT sizing_assignee FROM `mart.ec_publish_products` WHERE sizing_assignee IS NOT NULL
)
ORDER BY assignee
```

**レスポンス:**
```json
{
  "success": true,
  "data": ["田中", "佐藤", "鈴木"]
}
```

### 2. 商品一覧API修正

**変更点:**
- `status` パラメータを削除
- 以下のパラメータを追加:
  - `photoStatus`: pending/done
  - `retouchStatus`: pending/done
  - `commentStatus`: pending/done
  - `sizingStatus`: pending/done
  - `assignee`: 担当者名

**SQLフィルタ:**
```sql
-- 各工程ステータス（指定された場合のみ）
AND s.photo_status = @photoStatus
AND s.retouch_status = @retouchStatus
AND s.comment_status = @commentStatus
AND s.sizing_status = @sizingStatus

-- 担当者（いずれかの工程にマッチ）
AND (
  s.photo_assignee = @assignee
  OR s.retouch_assignee = @assignee
  OR s.comment_assignee = @assignee
  OR s.sizing_assignee = @assignee
)
```

### 3. フロントエンド修正

**状態管理:**
```typescript
// 削除: statusFilter
// 追加:
const [photoStatusFilter, setPhotoStatusFilter] = useState<string>("");
const [retouchStatusFilter, setRetouchStatusFilter] = useState<string>("");
const [commentStatusFilter, setCommentStatusFilter] = useState<string>("");
const [sizingStatusFilter, setSizingStatusFilter] = useState<string>("");
const [assigneeFilter, setAssigneeFilter] = useState<string>("");
const [assignees, setAssignees] = useState<string[]>([]);
```

**初期化時に担当者リストを取得:**
```typescript
useEffect(() => {
  fetch("/api/assignees")
    .then(res => res.json())
    .then(data => setAssignees(data.data));
}, []);
```

---

## UI設計

### フィルタセクション（変更後）
```
1行目: [公開先] [公開月] [ブランド] [担当者]
2行目: [📷] [✏️] [💬] [📏] [更新]
```

**工程フィルタの選択肢:**
- すべて（空文字）
- 未完了（pending）
- 作業中（in_progress）← **新規追加**
- 完了（done）

**担当者フィルタ:**
- すべて（空文字）
- (APIから取得したリスト)

---

## 実装ステップ

### Step 1: 型定義更新
- [ ] `src/types/product.ts` - WorkflowStatus に `in_progress` 追加
- [ ] WORKFLOW_STATUS_LABELS に「作業中」追加

### Step 2: 担当者一覧API作成
- [ ] `src/app/api/assignees/route.ts` 作成

### Step 3: 商品一覧API修正
- [ ] `status` パラメータを削除
- [ ] 工程ステータスパラメータ追加（photoStatus, retouchStatus, commentStatus, sizingStatus）
- [ ] 担当者パラメータ追加（assignee）
- [ ] SQLフィルタ条件を更新

### Step 4: フロントエンド修正
- [ ] WORKFLOW_STATUS_DISPLAY に `in_progress` 追加（黄色で「中」表示）
- [ ] 状態管理を更新（statusFilter → 工程別フィルタ）
- [ ] 担当者リスト取得処理追加
- [ ] フィルタUIを更新（2行レイアウト）
- [ ] API呼び出しを更新
