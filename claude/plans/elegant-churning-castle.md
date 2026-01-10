# ヘッダUI改善

## 概要

商品一覧画面のヘッダとフィルタUIを再構成し、ユーザビリティを向上させる。

## 要件

1. **グローバルフィルタをヘッダに移動**
   - 公開先、公開月、ブランドをタイトルと同じエリアに配置
   - このエリアは固定（sticky）でスクロールしない

2. **テーブルフィルタは現在の位置を維持**
   - 公開予定日、ワークフローステータス、担当者はテーブルの直上
   - スクロール対象

3. **アクションボタンを常時表示**
   - 選択なし: disabled 状態
   - 1件以上選択: enabled 状態
   - ボタンテキストから選択件数を削除（冗長）

## 現在の構造

```
┌─────────────────────────────────────────────────────┐
│ ← ホーム  品番EC公開作業リスト    [公開状況フェッチ] [公開予定リスト登録] │  ← Sub Header
├─────────────────────────────────────────────────────┤
│ 公開先 [▼] 公開月 [▼] ブランド [▼]                                      │  ← Row 1
├─────────────────────────────────────────────────────┤
│ 公開予定日[▼] 📷[▼] ✏️[▼] 💬[▼] 📏[▼] 担当者[▼]  [更新][品番コピー]... │  ← Row 2
└─────────────────────────────────────────────────────┘
│ テーブル（スクロール対象）                                              │
```

## 改善後の構造

```
┌─────────────────────────────────────────────────────┐
│ ← ホーム  品番EC公開作業リスト                                          │
│ 公開先 [▼] 公開月 [▼] ブランド [▼]     [公開状況フェッチ] [公開予定リスト登録] │  ← Sticky Header
├─────────────────────────────────────────────────────┤
│ 公開予定日[▼] 📷[▼] ✏️[▼] 💬[▼] 📏[▼] 担当者[▼]                          │  ← テーブルフィルタ
│ [品番コピー][Shopify CSV][一括変更][一括登録]               [更新]       │  ← アクション (常時表示)
└─────────────────────────────────────────────────────┘
│ テーブル（スクロール対象）                                              │
```

## 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `apps/ec-register/src/app/products/page.tsx` | ヘッダ構成変更（lines 877-1240） |

## 実装詳細

### 1. Sticky Header（lines 878-905 を拡張）

```tsx
{/* Sticky Header */}
<div className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
  <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    {/* Row 1: Navigation + Title */}
    <div className="flex items-center justify-between py-3">
      <div className="flex items-center gap-4">
        <Link href="/" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
          ← ホーム
        </Link>
        <h1 className="text-xl font-bold text-gray-900">品番EC公開作業リスト</h1>
      </div>
      <div className="flex items-center gap-2">
        <button onClick={() => setShowFetchDialog(true)} className="...">
          公開状況フェッチ
        </button>
        <Link href="/schedule/register" className="...">
          公開予定リスト登録
        </Link>
      </div>
    </div>

    {/* Row 2: Global Filters */}
    <div className="flex items-center gap-4 border-t border-gray-100 py-3">
      {/* 公開先 - inline label */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-600">公開先</label>
        <select className="rounded-md border ...">{/* options */}</select>
      </div>
      {/* 公開月 */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-600">公開月</label>
        <select className="rounded-md border ...">{/* options */}</select>
      </div>
      {/* ブランド */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-600">ブランド</label>
        <select className="rounded-md border ...">{/* options */}</select>
      </div>
    </div>
  </div>
</div>
```

### 2. テーブルフィルタセクション（lines 944-1240 を修正）

- Row 1 のフィルタ（公開先、公開月、ブランド）を削除
- Row 2 のみ残す（公開予定日、ワークフローステータス、担当者）
- アクションボタンを常時表示に変更

```tsx
<main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
  {/* Table Filters */}
  <div className="mb-4 rounded-lg bg-white p-4 shadow">
    {/* Filters Row */}
    <div className="flex flex-wrap items-center gap-4">
      {/* 公開予定日, 📷撮影, ✏️レタッチ, 💬コメント, 📏採寸, 担当者 */}
    </div>

    {/* Actions Row (常時表示) */}
    <div className="mt-3 flex items-center gap-2 border-t border-gray-200 pt-3">
      <button disabled={selectedProducts.size === 0} className="...">
        品番コピー
      </button>
      <button disabled={selectedProducts.size === 0 || exporting} className="...">
        Shopify CSV
      </button>
      <button disabled={selectedProducts.size === 0} className="...">
        一括変更
      </button>
      <button disabled={selectedProducts.size === 0} className="...">
        一括登録
      </button>
      <button onClick={fetchProducts} className="ml-auto ...">
        更新
      </button>
    </div>
  </div>
```

### 3. ボタンのスタイル

```tsx
// disabled 時のスタイル
<button
  onClick={handleAction}
  disabled={selectedProducts.size === 0}
  className={`rounded-md px-4 py-2 text-sm font-medium ${
    selectedProducts.size === 0
      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
      : 'bg-purple-600 text-white hover:bg-purple-700'
  }`}
>
  一括変更
</button>
```

## 実装手順

1. [ ] Sticky header 構造に変更（`border-b` div に `sticky top-0 z-40` 追加）
2. [ ] グローバルフィルタ（公開先、公開月、ブランド）をヘッダ内に移動
3. [ ] テーブルフィルタセクションから Row 1 を削除
4. [ ] アクションボタンを常時表示に変更（条件分岐を削除、disabled 追加）
5. [ ] ボタンテキストから `(${selectedProducts.size})` を削除
6. [ ] 動作確認

## 検証方法

1. `cd apps/ec-register && npm run dev` で開発サーバー起動
2. 商品一覧画面を開く
3. 確認事項:
   - ヘッダ（タイトル + グローバルフィルタ）がスクロールしても固定されること
   - アクションボタンが常に表示されること
   - 選択なし時: ボタンが disabled 状態（グレーアウト）
   - 選択あり時: ボタンが enabled 状態（色付き、クリック可能）
   - ボタンに選択件数が表示されないこと
