1️⃣ Pie - 브랜드 점유율 (도넛 차트)
1. Pie 클릭
2. Index pattern: musinsa_products* 선택
3. Metrics → Aggregation: Count (기본값)
4. Buckets → Add → Split slices
   - Aggregation: Terms
   - Field: brand.keyword
   - Size: 10
5. Options 탭 → ✅ Donut 체크 (도넛 모양)
6. ▶️ 재생 버튼 클릭
7. 💾 Save → 이름: "브랜드 점유율"
2️⃣ Vertical Bar - 가격대 분포 (히스토그램)
1. Vertical Bar 클릭
2. Index pattern: musinsa_products* 선택
3. Metrics → Aggregation: Count (기본값)
4. Buckets → Add → X-axis
   - Aggregation: Histogram
   - Field: price
   - Minimum interval: 10000 (1만원 단위)
5. ▶️ 재생 버튼 클릭
6. 💾 Save → 이름: "가격대 분포"
3️⃣ Data Table - 상위 판매자 리스트
1. Data Table 클릭
2. Index pattern: musinsa_products* 선택
3. Metrics → Aggregation: Count (기본값)
4. Buckets → Add → Split rows
   - Aggregation: Terms
   - Field: seller_info.company.keyword
   - Size: 20 (상위 20개 판매자)
   - Order by: metric: Count (내림차순)
5. ▶️ 재생 버튼 클릭
6. 💾 Save → 이름: "상위 판매자 TOP 20"
4️⃣ Metric - 핵심 숫자 (총 상품 수, 평균 가격)
1. Metric 클릭
2. Index pattern: musinsa_products* 선택
3. Metrics → Aggregation: Count (총 상품 수)
   - Custom label: "총 상품 수"
4. Metrics → Add → Aggregation: Average
   - Field: price
   - Custom label: "평균 가격"
5. ▶️ 재생 버튼 클릭
6. 💾 Save → 이름: "핵심 지표"
5️⃣ Tag Cloud - 브랜드명 워드클라우드
1. Tag Cloud 클릭
2. Index pattern: musinsa_products* 선택
3. Metrics → Aggregation: Count (기본값)
4. Buckets → Add → Tags
   - Aggregation: Terms
   - Field: brand.keyword
   - Size: 50 (상위 50개 브랜드)
5. Options 탭 → Font size range: 18 ~ 72 (조절 가능)
6. ▶️ 재생 버튼 클릭
7. 💾 Save → 이름: "브랜드 클라우드"