import requests
import json

# Instagram Business Account ID를 직접 입력
# (Instagram 앱 → 설정 → 계정 → 비즈니스 정보에서 확인 가능)
instagram_business_account_id = "YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID"

access_token = "EAA00JHuld3gBPzDpvDLcxFLRFf2EHo2MaE3Ttlgr3B9yZAsu8OqLI0CB8iItYZAJx6xUlt5RKpb4kSoTaqdFDsH3tohtz6xHth7EgfHUmJycvngOfKq62Trty5KX4Uy8EiDJ9N5eBiFkH8JFiMrEpSZAOEThLKyHPQqO0iIf0HoZA11ZAgSwmUlylQkaZC"

# Instagram Business Account ID 찾기 (username으로)
username = "pm_international_korea"  # Instagram 사용자명
search_url = f"https://graph.facebook.com/v12.0/ig_hashtag_search?user_id={instagram_business_account_id}&q=test&access_token={access_token}"

# 또는 직접 미디어 조회
media_url = f"https://graph.facebook.com/v12.0/{instagram_business_account_id}/media?fields=id,caption,media_type,media_url,permalink,timestamp&access_token={access_token}"

response = requests.get(media_url).json()

print("API 응답:")
print(json.dumps(response, indent=2, ensure_ascii=False))

if 'error' in response:
    print(f"\n❌ API 오류:")
    print(f"  - {response['error'].get('message')}")
    print("\n해결 방법:")
    print("  1. Instagram 계정을 비즈니스 계정으로 전환하세요")
    print("  2. Facebook 페이지와 연결하세요")
    print("  3. Access Token 권한을 확인하세요")
else:
    print(f"\n✅ {len(response.get('data', []))}개의 게시물을 찾았습니다")
