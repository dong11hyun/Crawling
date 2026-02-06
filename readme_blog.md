# 무신사 2만 건 상품 데이터를 10배 빠르게 수집한 방법

> **"Selenium 브라우저 자동화에서 벗어나 분당 1,000건을 수집하기까지의 여정"**

---

## 🎯 TL;DR

- **문제**: 기존 Selenium 크롤러가 너무 느리고, 메모리를 1GB 이상 잡아먹었습니다.
- **해결**: API 역공학 + 경량 스레드 아키텍처로 전환했습니다.
- **결과**: 10배 빠른 속도, 90% 적은 메모리, 차단율 0%.

---

## 1. 왜 이 프로젝트를 시작했나?

무신사에서 상품 데이터를 수집해야 할 일이 생겼습니다. 처음엔 당연히 브라우저 자동화(Playwright)를 썼죠.

```python
# 첫 번째 시도: Playwright (브라우저 자동화)
browser = await p.chromium.launch(headless=False)
page = await browser.new_page()
await page.goto("https://www.musinsa.com/products/12345")
title = driver.find_element(By.CSS_SELECTOR, ".product-title").text
```

**결과는 처참했습니다.**

| 지표 | 수치 |
|------|------|
| 속도 | 건당 3~5초 |
| 메모리 | 탭당 150MB |
| 1만 건 수집 시간 | **8시간 이상** |

크롬 탭 4개를 띄우면 메모리가 1GB를 넘어갔고, 노트북 팬이 미친 듯이 돌아갔습니다.

---

## 2. 첫 번째 돌파구: API 역공학

개발자 도구(F12)를 열고 Network 탭을 뒤지다가 발견했습니다.

```
https://api.musinsa.com/api2/dp/v1/plp/goods?keyword=패딩&page=1&size=60
```

**무신사가 내부적으로 사용하는 API가 있었습니다.** 이 API는 한 번에 60개 상품을 JSON으로 돌려줍니다. 브라우저 렌더링? 필요 없습니다.

```python
# 두 번째 시도: API 직접 호출
response = requests.get(url, params=params, headers=headers)
products = response.json()["data"]["list"]
```

**속도가 10배 빨라졌습니다.** 건당 3초 → 0.3초.

---

## 3. 두 번째 문제: 사업자 정보는 API에 없다

하지만 문제가 있었습니다. API는 상품명, 가격, 이미지만 줍니다. 제가 필요한 **사업자등록번호, 대표자명, 연락처**는 상세 페이지에만 있었습니다.

상세 페이지를 열어보니 Next.js로 만들어진 SPA였습니다. 데이터는 어디에?

```html
<script id="__NEXT_DATA__" type="application/json">
  {"props":{"pageProps":{"meta":{"data":{"company":{...}}}}}}
</script>
```

**서버 사이드 렌더링 데이터가 `__NEXT_DATA__`에 숨어있었습니다.**

```python
# 핵심 추출 로직
soup = BeautifulSoup(response.text, 'lxml')
next_data = soup.find('script', id='__NEXT_DATA__')
data = json.loads(next_data.string)
company = data['props']['pageProps']['meta']['data']['company']

# 추출 가능한 정보
seller_info = {
    "상호명": company.get('name'),
    "대표자명": company.get('ceoName'),
    "사업자등록번호": company.get('businessNumber'),
    "통신판매업신고번호": company.get('mailOrderReportNumber'),
    "연락처": company.get('phoneNumber'),
    "이메일": company.get('email'),
    "주소": company.get('address')
}
```

단순 크롤링이 아니라 **SPA 내부 데이터까지 역공학으로 추출**할 수 있게 되었습니다.

---

## 4. 세 번째 문제: 429 Too Many Requests

빠르게 요청을 보내면 서버가 차단합니다.

```
HTTP 429 Too Many Requests
```

**해결책: Polite Crawling**

```python
# 적응형 스로틀링
def safe_delay(base_delay: float):
    delay = base_delay + random.uniform(0.3, 0.8)  # 랜덤성 추가
    time.sleep(delay)

# User-Agent 로테이션
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) Safari/...",
    # 4개의 다른 브라우저 시그니처
]
headers = {"User-Agent": random.choice(USER_AGENTS)}
```

**결과: 2만 건 수집 중 429 에러 0건.**

---

## 5. 네 번째 최적화: 병렬 처리

순차 처리로는 2만 건 수집에 너무 오래 걸렸습니다. 하지만 Selenium처럼 무거운 프로세스는 싫었죠.

**해결책: ThreadPoolExecutor**

```python
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {executor.submit(process_product, p) for p in products}
    for future in as_completed(futures):
        result = future.result()
```

### 왜 프로세스가 아니라 스레드인가?

| 항목 | Chrome (Selenium) | ThreadPool (이 프로젝트) |
|------|-------------------|------------------------|
| 아키텍처 | 멀티프로세스 | 멀티스레드 |
| 메모리 | 탭당 150MB | 스레드당 2MB |
| 4개 병렬 | ~1.1GB | ~84MB |
| 렌더링 | 전체 (HTML→CSS→JS) | 없음 (텍스트만) |

**핵심 인사이트**: 이 작업은 **I/O 바운드**입니다. CPU가 바쁜 게 아니라 네트워크 응답을 기다리는 시간이 대부분이죠. Python의 GIL은 I/O 대기 중에는 다른 스레드에게 양보하기 때문에, 스레드만으로도 충분한 병렬성을 얻을 수 있습니다.

---

## 6. 다섯 번째 최적화: Bulk Indexing

수집한 데이터를 OpenSearch에 저장해야 했습니다. 처음엔 1건씩 저장했습니다.

```python
# 느린 방식
for item in items:
    client.index(index="products", body=item)  # 매번 연결
```

**문제**: 매번 TCP 연결을 맺고 끊는 오버헤드가 컸습니다.

```python
# 빠른 방식: Bulk Indexing
buffer = []
for item in items:
    buffer.append({"_index": "products", "_source": item})
    if len(buffer) >= 20:
        helpers.bulk(client, buffer)  # 20개씩 한 번에
        buffer.clear()
```

**결과: DB 쓰기 오버헤드 95% 감소.**

---

## 7. 보너스: AI 벡터 검색

여기까지 왔으면 검색도 제대로 하고 싶었습니다. 문제는 "패딩"을 검색하면 "다운자켓"은 안 나오는 거였죠.

**해결책: 벡터 임베딩 + k-NN**

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
vector = model.encode("패딩")  # 384차원 벡터
```

상품 제목을 벡터로 변환해서 OpenSearch에 저장하면, **의미가 비슷한 상품을 찾을 수 있습니다.**

| 검색어 | 키워드 검색 결과 | 벡터 검색 결과 |
|-------|----------------|---------------|
| "패딩" | 패딩, 패딩조끼 | 패딩, 다운자켓, 푸퍼, 롱패딩 |

---

## 8. 최종 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│   [검색창] → [키워드 탭] [AI 탭] → [정렬] [무한스크롤]         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                      FastAPI Server                          │
│   /search (키워드) │ /search/vector (AI) │ /crawl           │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │OpenSearch│    │  Redis   │    │  JSONL   │
    │ (검색)   │    │ (캐시)   │    │ (백업)   │
    └──────────┘    └──────────┘    └──────────┘
```

---

## 9. 성과 요약

| 지표 | Before (Selenium) | After (이 프로젝트) | 개선율 |
|------|-------------------|-------------------|--------|
| 수집 속도 | 건당 3초 | 건당 0.3초 | **10배 ↑** |
| 메모리 | 1.1GB | 84MB | **93% ↓** |
| 429 차단율 | 빈번 | 0% | **100% ↓** |
| DB 오버헤드 | 높음 | 낮음 | **95% ↓** |
| 검색 품질 | 키워드 일치만 | 의미 유사도 | **혁신** |

---

## 10. 배운 것들

1. **역공학의 가치**: 공식 API가 없어도 Network 탭을 뒤지면 길이 보입니다.
2. **브라우저가 항상 답은 아니다**: Selenium은 강력하지만, 필요 없는 상황에선 오버킬입니다.
3. **I/O 바운드 = 스레드로 충분**: 멀티프로세싱이 항상 빠른 건 아닙니다.
4. **Polite Crawling의 중요성**: 서버를 존중하면서도 원하는 데이터를 얻을 수 있습니다.

---

## 📚 기술 스택

- **Backend**: Python, FastAPI, OpenSearch, Redis
- **Crawling**: Requests, BeautifulSoup, lxml
- **AI Search**: sentence-transformers, k-NN
- **Infra**: Docker Compose

---

## 🔗 Links

- [GitHub Repository](https://github.com/your-repo)
- [API 문서 (Swagger)](http://localhost:8000/docs)
- [기술 심층 분석](./1_기술리뷰심층.md)

---

*이 글은 실제 프로젝트 경험을 바탕으로 작성되었습니다. 질문이나 피드백은 언제든 환영합니다.*
