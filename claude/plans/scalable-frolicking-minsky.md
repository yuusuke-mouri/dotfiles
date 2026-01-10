# ec-register ソースコードレビューレポート

## 概要
- **レビュー対象**: apps/ec-register/src 配下の全ソースコード
- **対象ファイル数**: 12ファイル
- **git履歴**: 3コミット

```
04fafdc feat(ec-register): 公開予定登録・商品詳細画面を追加
59f0b48 feat(ec-register): 商品一覧ページを追加
dcf8c28 feat(ec-register): Next.js 16 プロジェクト初期化
```

## レビュー観点
1. design.md との整合性
2. セキュリティ（SQLインジェクション、認証）
3. 堅牢性（エラーハンドリング、型安全性）
4. コード品質（重複、保守性）

---

## 発見された問題点

### 重大度: HIGH

#### 1. SQLインジェクション脆弱性（8箇所）

| ファイル | 行 | 問題 |
|----------|-----|------|
| `api/products/route.ts` | L31-37 | `channel`, `status`, `brand` をクエリに直接埋め込み |
| `api/products/[productCode]/route.ts` | L86 | `productCode` をクエリに直接埋め込み |
| `api/schedule/preview/route.ts` | L64, L89-91 | `channel`, `publishMonth` を直接埋め込み |
| `api/schedule/register/route.ts` | L49, L96, L127 | 同上 + INSERT文にも直接埋め込み |
| `api/schedule/copy/route.ts` | L66, L72-74 | 同上 |

**現状のコード例:**
```typescript
whereClause += ` AND s.status = '${status}'`;
```

**修正方針:** BigQueryパラメータ化クエリへ移行
```typescript
const [rows] = await bigquery.query({
  query: 'SELECT * FROM table WHERE status = @status',
  params: { status: status }
});
```

#### 2. 認証・認可の未実装

| ファイル | 状態 |
|----------|------|
| 全APIエンドポイント | 認証チェックなし |
| `products/[productCode]/page.tsx` L130-133 | `isAuthenticated: true` ハードコード |

**TODOコメントあり:**
```typescript
// TODO: Add authentication middleware here
```

---

### 重大度: MEDIUM

#### 3. エラーハンドリングの問題

| ファイル | 行 | 問題 |
|----------|-----|------|
| `api/schedule/preview/route.ts` | L85-100 | テーブル不在エラーをサイレント無視 |
| `lib/bigquery.ts` | L11-33 | `parameters`引数が未使用 |

#### 4. 型安全性の問題

- `as Channel` キャストによる型チェックスキップ
- BigQuery結果の型検証なし
- 数値型の処理不一貫（`string` vs `number`）

#### 5. コード重複

| 重複コード | 該当ファイル |
|-----------|-------------|
| `sanitizedCodes` ロジック | preview, register, copy の3ファイル |
| `codesPlaceholder` 生成 | 同上 |
| `generateMonthOptions()` | schedule/register, products の2ファイル |

---

### 重大度: LOW

#### 6. 未実装機能

| 機能 | 設計書の記載 | 実装状態 |
|------|-------------|----------|
| 一括登録ボタン | Phase 2 | UIのみ（onClick未実装） |
| copy API呼び出し | Step 6 | API実装済み、UI未連携 |

#### 7. ログ・モニタリング

- クエリのフルテキストログなし
- パラメータ値がログに出力されない

---

## design.md との整合性チェック

### 一致している点
- [x] API設計（8.1-8.5）のエンドポイント構造
- [x] BigQueryスキーマ（Section 5）との結合クエリ
- [x] 公開先定義（Section 6）の CHANNELS 定数
- [x] 画面構成（Section 7）のURL構造

### 不一致・未実装

| 設計書 | 実装 | 状態 |
|--------|------|------|
| Step 6: `/api/schedule/copy` | 実装済み | UI未連携 |
| Step 7: Firebase Auth連携 | 未実装 | TODO記載あり |

---

## 総括

| カテゴリ | 重大度 | 件数 | 対応優先度 |
|----------|--------|------|-----------|
| SQLインジェクション | HIGH | 8 | 必須 |
| 認証・認可未実装 | HIGH | 2 | 必須 |
| エラーハンドリング | MEDIUM | 3 | 推奨 |
| 型安全性 | MEDIUM | 3 | 推奨 |
| コード重複 | MEDIUM | 3 | 任意 |
| 未実装機能 | LOW | 2 | Phase 2 |

## 推奨対応（優先度順）

1. **SQLインジェクション対策** - BigQueryパラメータ化クエリへの移行
2. **認証実装** - Firebase Auth連携（design.md Step 7）
3. **入力バリデーション強化** - channel, publishMonth, status の検証
4. **共通ユーティリティ抽出** - 重複コードの解消
5. **型安全性向上** - as キャスト削除、ランタイムバリデーション追加
