# DART 중계 함수

Streamlit Community Cloud 는 해외 리전에서 실행되는데, FSS 서버가 해외 IP의
연결을 받아주지 않습니다. 실제로 배포 후 `ConnectTimeout` 이 났습니다.

이 디렉터리의 함수를 Vercel 서울 리전(`icn1`)에 올리면
Streamlit → Vercel(서울) → DART 순서로 요청이 나갑니다.

## 배포

1. https://vercel.com 에서 GitHub 계정으로 로그인
2. **Add New → Project** → 이 저장소(`kam_`) 선택 → **Deploy**
3. 배포 후 **Settings → Functions → Function Region** 이 **Seoul (icn1)** 인지 확인
   (`vercel.json` 에 지정해 두었지만 프로젝트 설정이 우선합니다)
4. 발급된 주소(예: `https://kam-xxxx.vercel.app`)를
   Streamlit Cloud 의 Secrets 에 추가:

   ```toml
   DART_PROXY_BASE = "https://kam-xxxx.vercel.app"
   ```

`DART_PROXY_BASE` 가 없으면 앱은 DART 로 직접 연결합니다. 로컬에서는 직접
연결이 정상 동작하므로 설정하지 않아도 됩니다.

## 동작 확인

```bash
curl -s "https://kam-xxxx.vercel.app/api/dart?url=https%3A%2F%2Fdart.fss.or.kr%2F" -o /dev/null -w "%{http_code}\n"
```

## 보안

대상 호스트를 `opendart.fss.or.kr`, `dart.fss.or.kr` 로만 제한합니다.
누구나 아무 주소나 부를 수 있는 열린 프록시가 되지 않도록 하기 위함입니다.
