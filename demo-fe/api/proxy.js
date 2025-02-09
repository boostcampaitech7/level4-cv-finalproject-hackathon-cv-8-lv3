// 예: Vercel Serverless Function
import fetch from 'node-fetch'; 
// node-fetch가 필요할 수도 있고, 일부 환경은 fetch 내장 지원.

const SERVER_URL = import.meta.env.VITE_SERVER_URL;


export default async function handler(req, res) {
  try {
    // (1) 클라이언트로부터 요청된 데이터를 추출
    // 예: POST body, query param, etc.
    const payload = req.body;

    // (2) 백엔드(HTTP)로 요청
    const backendResponse = await fetch(`${SERVER_URL}/process_video_with_timestamps`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!backendResponse.ok) {
      return res.status(backendResponse.status).json({ error: 'Backend error' });
    }

    // (3) 백엔드 응답을 클라이언트에 반환
    const data = await backendResponse.json();
    return res.status(200).json(data);
  } catch (error) {
    console.error('Proxy error:', error);
    return res.status(500).json({ error: error.message });
  }
}
