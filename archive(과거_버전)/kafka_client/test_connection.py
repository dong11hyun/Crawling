"""
Kafka 연결 테스트 스크립트
- 브로커 연결 확인
- Topic 목록 조회
- 테스트 메시지 발행/소비
"""
import sys
import json
from datetime import datetime

# kafka-python 설치 확인
try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import KafkaError
    print("✅ kafka-python 설치됨")
except ImportError:
    print("❌ kafka-python 설치 필요!")
    print("   pip install kafka-python")
    sys.exit(1)

# 설정
BOOTSTRAP_SERVERS = "localhost:9092"
TEST_TOPIC = "musinsa-products"


def test_connection():
    """브로커 연결 테스트"""
    print("\n" + "="*50)
    print("1. 브로커 연결 테스트")
    print("="*50)
    
    try:
        admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
        print(f"✅ Kafka 연결 성공: {BOOTSTRAP_SERVERS}")
        
        # 클러스터 정보
        cluster = admin.describe_cluster()
        print(f"   클러스터 ID: {cluster.get('cluster_id', 'N/A')}")
        
        admin.close()
        return True
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False


def test_list_topics():
    """Topic 목록 조회"""
    print("\n" + "="*50)
    print("2. Topic 목록 조회")
    print("="*50)
    
    try:
        consumer = KafkaConsumer(bootstrap_servers=BOOTSTRAP_SERVERS)
        topics = consumer.topics()
        
        print(f"✅ Topic 개수: {len(topics)}")
        for topic in topics:
            print(f"   - {topic}")
        
        consumer.close()
        return True
    except Exception as e:
        print(f"❌ Topic 조회 실패: {e}")
        return False


def test_produce_message():
    """테스트 메시지 발행"""
    print("\n" + "="*50)
    print("3. 메시지 발행 테스트")
    print("="*50)
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        
        # 테스트 메시지
        test_data = {
            "type": "test",
            "message": "Kafka 연결 테스트",
            "timestamp": datetime.now().isoformat(),
            "source": "test_connection.py"
        }
        
        future = producer.send(
            TEST_TOPIC,
            key="test-key",
            value=test_data
        )
        
        # 전송 완료 대기
        result = future.get(timeout=10)
        print(f"✅ 메시지 발행 성공!")
        print(f"   Topic: {result.topic}")
        print(f"   Partition: {result.partition}")
        print(f"   Offset: {result.offset}")
        
        producer.close()
        return True
    except Exception as e:
        print(f"❌ 메시지 발행 실패: {e}")
        return False


def test_consume_message():
    """테스트 메시지 소비"""
    print("\n" + "="*50)
    print("4. 메시지 소비 테스트")
    print("="*50)
    
    try:
        consumer = KafkaConsumer(
            TEST_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,  # 5초 타임아웃
            group_id='test-group'
        )
        
        print(f"✅ Consumer 생성 완료")
        print(f"   Topic: {TEST_TOPIC}")
        print(f"   대기 중... (5초 타임아웃)")
        
        count = 0
        for message in consumer:
            count += 1
            print(f"\n   📨 메시지 #{count}")
            print(f"      Partition: {message.partition}")
            print(f"      Offset: {message.offset}")
            print(f"      Key: {message.key}")
            print(f"      Value: {message.value}")
            
            if count >= 3:  # 최대 3개만 출력
                print(f"\n   (... 더 많은 메시지가 있을 수 있음)")
                break
        
        consumer.close()
        print(f"\n✅ 총 {count}개 메시지 확인")
        return True
    except Exception as e:
        print(f"❌ 메시지 소비 실패: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Kafka 연결 테스트 시작")
    print(f"   Bootstrap Servers: {BOOTSTRAP_SERVERS}")
    print(f"   Test Topic: {TEST_TOPIC}")
    
    # 테스트 실행
    results = []
    results.append(("연결 테스트", test_connection()))
    results.append(("Topic 조회", test_list_topics()))
    results.append(("메시지 발행", test_produce_message()))
    results.append(("메시지 소비", test_consume_message()))
    
    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약")
    print("="*50)
    for name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"   {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("🎉 모든 테스트 통과!" if all_passed else "⚠️ 일부 테스트 실패"))
