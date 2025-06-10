describe('Session Management', () => {
  let testSessionId: number | null = null;

  // 환경 변수 체크
  if (!Cypress.env('apiUrl')) {
    throw new Error('API URL environment variable is not set');
  }

  const API_URL = Cypress.env('apiUrl');
  if (!API_URL) {
    throw new Error('apiUrl environment variable is not set');
  }

  const API_VERSION = Cypress.env('apiVersion');
  if (!API_VERSION) {
    throw new Error('apiVersion environment variable is not set');
  }

  beforeEach(() => {
    // API 요청 모니터링 설정 (경로를 더 유연하게 변경)
    cy.intercept('POST', '**/sessions').as('createSession');
    
    // 페이지 방문
    cy.visit('/');
    
    // 세션 리스트가 로드될 때까지 대기
    cy.get('[data-testid="session-list"]').should('exist');
  });

  it('should create a new session and display debug information', () => {
    const sessionName = 'Test Session ' + new Date().toISOString();
    
    // 새 세션 버튼 클릭
    cy.get('[data-testid="create-session-button"]').should('be.visible').click();
    
    // 세션 이름 입력
    cy.get('[data-testid="new-session-input"]').should('be.visible').type(sessionName);
    
    // 세션 생성 버튼 클릭
    cy.get('[data-testid="confirm-create-button"]').should('be.visible').click();
    
    // API 응답 대기 및 세션 ID 저장 (타임아웃 증가)
    cy.wait('@createSession', { timeout: 10000 }).then((interception) => {
      // API 응답이 있는지 확인
      expect(interception.response).to.exist;
      
      // API 응답 상태 코드 확인
      if (interception.response) {
        expect(interception.response.statusCode).to.equal(200);
        
        // 응답 본문에 id가 있는지 확인
        expect(interception.response.body).to.have.property('id');
        
        // 세션 ID 저장
        testSessionId = interception.response.body.id;
        cy.log(`Created session with ID: ${testSessionId}`);
        
        // 세션 ID가 유효한지 확인
        expect(testSessionId).to.be.a('number');
      }
    });
    
    // 디버그 정보 확인
    cy.get('[data-testid="session-debug"]').within(() => {
      // 세션 ID 표시 확인
      cy.contains('세션 ID:').should('be.visible');
      cy.contains(testSessionId?.toString() || '').should('be.visible');
      
      // API 응답 확인
      cy.contains('API 응답:').should('be.visible');
      cy.get('pre').first().should('contain', testSessionId?.toString());
      
      // 브라우저 응답 확인
      cy.contains('브라우저 응답:').should('be.visible');
      cy.get('pre').last().should('contain', 'status');
    });
    
    // 세션 리스트에 새 세션이 표시되는지 확인
    cy.get('[data-testid="session-list"]')
      .should('contain', sessionName)
      .then(() => {
        cy.log(`Verified session "${sessionName}" in the list`);
      });
  });

  afterEach(() => {
    // 세션 ID가 있는 경우에만 삭제 시도
    if (testSessionId) {
      cy.log(`Attempting to delete session with ID: ${testSessionId}`);
      
      cy.request({
        method: 'DELETE',
        url: `${API_URL}/api/${API_VERSION}/sessions/${testSessionId}`,
        failOnStatusCode: false
      }).then((response) => {
        // 삭제 응답 상태 코드 확인
        expect(response.status).to.be.oneOf([200, 404]);
        cy.log(`Session deletion response status: ${response.status}`);
        
        // 세션 ID 초기화
        testSessionId = null;
      });
    } else {
      cy.log('No session ID to delete');
    }
  });
}); 