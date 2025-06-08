import axios from 'axios';

const BACKEND_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:3000';

async function checkServer(url, name) {
  try {
    const response = await axios.get(url);
    if (response.status === 200) {
      console.log(`✅ ${name} 서버가 정상적으로 실행 중입니다.`);
      return true;
    }
  } catch (error) {
    console.error(`❌ ${name} 서버에 연결할 수 없습니다.`);
    return false;
  }
}

async function checkServers() {
  console.log('서버 상태를 확인합니다...\n');
  
  const backendStatus = await checkServer(BACKEND_URL, '백엔드');
  const frontendStatus = await checkServer(FRONTEND_URL, '프론트엔드');
  
  if (!backendStatus || !frontendStatus) {
    console.log('\n⚠️ 서버가 실행되지 않았습니다. 서버를 시작해주세요:');
    console.log('1. 백엔드 서버: ./run_app.sh');
    console.log('2. 프론트엔드 서버: cd frontend && npm run dev');
    process.exit(1);
  }
  
  console.log('\n✅ 모든 서버가 정상적으로 실행 중입니다.');
}

checkServers(); 