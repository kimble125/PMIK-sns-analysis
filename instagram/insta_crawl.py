import requests
import json

access_token = "EAA00JHuld3gBPzDpvDLcxFLRFf2EHo2MaE3Ttlgr3B9yZAsu8OqLI0CB8iItYZAJx6xUlt5RKpb4kSoTaqdFDsH3tohtz6xHth7EgfHUmJycvngOfKq62Trty5KX4Uy8EiDJ9N5eBiFkH8JFiMrEpSZAOEThLKyHPQqO0iIf0HoZA11ZAgSwmUlylQkaZC"
url = f"https://graph.facebook.com/v12.0/me/accounts?access_token={access_token}"
response = requests.get(url).json()

# 응답 확인
print("API 응답:")
print(json.dumps(response, indent=2, ensure_ascii=False))

# 에러 체크
if 'error' in response:
    print(f"\n❌ API 오류 발생:")
    print(f"  - 오류 메시지: {response['error'].get('message', 'Unknown error')}")
    print(f"  - 오류 타입: {response['error'].get('type', 'Unknown type')}")
    print(f"  - 오류 코드: {response['error'].get('code', 'Unknown code')}")
    exit(1)

# 데이터 체크
if not response.get('data'):
    print("\n❌ 연결된 Facebook 페이지가 없습니다.")
    print("해결 방법:")
    print("  1. Facebook 페이지를 생성하세요")
    print("  2. 해당 페이지를 Instagram 비즈니스 계정과 연결하세요")
    print("  3. Access Token에 'pages_show_list' 권한이 있는지 확인하세요")
    exit(1)

page_id = response['data'][0]['id']
print(f"\n✅ Facebook Page ID: {page_id}")
