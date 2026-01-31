# 📊 OpenSearch Dashboard 시각화 가이드

무신사 상품 데이터를 활용한 대시보드 시각화 설정 방법입니다.

---

## 1️⃣ Pie - 브랜드 점유율 (도넛 차트)

1. **Pie** 클릭
2. Index pattern: `musinsa_products*` 선택
3. **Metrics** → Aggregation: `Count` (기본값)
4. **Buckets** → Add → **Split slices**
   - Aggregation: `Terms`
   - Field: `brand`
   - Size: `10`
5. **Options** 탭 → ✅ Donut 체크 (도넛 모양)
6. ▶️ 재생 버튼 클릭
7. 💾 Save → 이름: `브랜드 점유율`

---

## 2️⃣ Vertical Bar - 가격대 분포 (히스토그램)

1. **Vertical Bar** 클릭
2. Index pattern: `musinsa_products*` 선택
3. **Metrics** → Aggregation: `Count` (기본값)
4. **Buckets** → Add → **X-axis**
   - Aggregation: `Histogram`
   - Field: `price`
   - Minimum interval: `10000` (1만원 단위)
5. ▶️ 재생 버튼 클릭
6. 💾 Save → 이름: `가격대 분포`

---

## 3️⃣ Data Table - 상위 판매자 리스트

> ⚠️ **주의**: Size를 11개 이상으로 설정하면 Dashboard UI가 멈추는 버그가 있을 수 있습니다.
> Dev Tools에서 직접 쿼리하면 정상 작동합니다.

1. **Data Table** 클릭
2. Index pattern: `musinsa_products*` 선택
3. **Metrics** → Aggregation: `Count` (기본값)
4. **Buckets** → Add → **Split rows**
   - Aggregation: `Terms`
   - Field: `seller_info.company`
   - Size: `10` (상위 10개 판매자)
   - Order by: `metric: Count` (내림차순)
5. ▶️ 재생 버튼 클릭
6. 💾 Save → 이름: `상위 판매자 TOP 10`

### 📌 Dev Tools 대안 쿼리 (20개 이상 조회 시)
```json
GET musinsa_products/_search
{
  "size": 0,
  "aggs": {
    "top_sellers": {
      "terms": {
        "field": "seller_info.company",
        "size": 20
      }
    }
  }
}
```

---

## 4️⃣ Metric - 핵심 숫자 (총 상품 수, 평균 가격)

1. **Metric** 클릭
2. Index pattern: `musinsa_products*` 선택
3. **Metrics** 설정:
   - Aggregation: `Count`
   - Custom label: `총 상품 수`
4. **Metrics** → **Add** 클릭:
   - Aggregation: `Average`
   - Field: `price`
   - Custom label: `평균 가격`
5. ▶️ 재생 버튼 클릭
6. 💾 Save → 이름: `핵심 지표`

---

## 5️⃣ Tag Cloud - 브랜드명 워드클라우드

1. **Tag Cloud** 클릭
2. Index pattern: `musinsa_products*` 선택
3. **Metrics** → Aggregation: `Count` (기본값)
4. **Buckets** → Add → **Tags**
   - Aggregation: `Terms`
   - Field: `brand`
   - Size: `50` (상위 50개 브랜드)
5. **Options** 탭:
   - Font size range: `18 ~ 72` (조절 가능)
6. ▶️ 재생 버튼 클릭
7. 💾 Save → 이름: `브랜드 클라우드`

---

## 6️⃣ Data Table - 브랜드별 통계 (총 상품 수 + 평균 가격)

브랜드별 비교를 깔끔하게 보여주는 테이블입니다.

| 브랜드 | 총 상품 수 | 평균 가격 |
|--------|-----------|-----------|
| 노스페이스 | 425 | 298,175 |
| 디스커버리 | 359 | 264,770 |
| ... | ... | ... |

### 설정 방법:

1. **Data Table** 클릭
2. Index pattern: `musinsa_products*` 선택
3. **Metrics** 설정:
   - Aggregation: `Count`
   - Custom label: `총 상품 수`
4. **Metrics** → **Add** 클릭:
   - Aggregation: `Average`
   - Field: `price`
   - Custom label: `평균 가격`
5. **Buckets** → Add → **Split rows**
   - Aggregation: `Terms`
   - Field: `brand`
   - Size: `10`
6. ▶️ 재생 버튼 클릭
7. 💾 Save → 이름: `브랜드별 통계`

### 💡 소수점 제거 (숫자 포맷팅)

평균 가격에서 소수점을 제거하려면:

1. **Management** → **Index Patterns** 이동
2. `musinsa_products*` 클릭
3. `price` 필드 → 연필 아이콘 (✏️ Edit) 클릭
4. **Format** → `Number` 선택
5. **Numeral.js format pattern**: `0,0` 입력
6. **Save field** 클릭

---

## 📋 필드 참조

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `brand` | keyword | 브랜드명 |
| `price` | integer | 판매가 |
| `normalPrice` | integer | 정가 |
| `saleRate` | integer | 할인율 |
| `seller_info.company` | keyword | 판매자 회사명 |
| `seller_info.ceo` | keyword | 대표자명 |
| `title` | text | 상품명 |
| `crawled_at` | date | 크롤링 시간 |