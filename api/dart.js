// DART 중계 함수. 서울 리전(icn1)에서 실행된다.
//
// Streamlit Community Cloud 는 해외 리전에서 도는데 FSS 서버가 그쪽 연결을
// 받아주지 않는다. 이 함수가 중간에서 요청을 받아 DART 에서 받아 되돌려준다.
//
// 열린 프록시가 되지 않도록 대상 호스트를 DART 로만 제한한다.

const ALLOWED_HOSTS = ["opendart.fss.or.kr", "dart.fss.or.kr"];

export default async function handler(request, response) {
  const target = request.query.url;

  if (!target) {
    return response.status(400).json({ error: "url 파라미터가 필요합니다." });
  }

  let parsed;
  try {
    parsed = new URL(target);
  } catch {
    return response.status(400).json({ error: "올바른 URL이 아닙니다." });
  }

  if (parsed.protocol !== "https:" || !ALLOWED_HOSTS.includes(parsed.hostname)) {
    return response.status(403).json({ error: "허용되지 않은 대상입니다." });
  }

  try {
    const upstream = await fetch(parsed.toString(), {
      headers: {
        "User-Agent": "Mozilla/5.0",
        Referer: "https://dart.fss.or.kr/",
      },
    });

    const body = Buffer.from(await upstream.arrayBuffer());
    response.setHeader(
      "Content-Type",
      upstream.headers.get("content-type") || "application/octet-stream"
    );
    // 같은 공시는 잘 바뀌지 않으므로 짧게 캐시해 DART 부하를 줄인다.
    response.setHeader("Cache-Control", "public, max-age=300");
    return response.status(upstream.status).send(body);
  } catch (error) {
    return response.status(502).json({ error: `DART 연결 실패: ${error.name}` });
  }
}
