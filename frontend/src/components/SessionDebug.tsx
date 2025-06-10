import React from 'react';

interface SessionDebugProps {
  sessionId: number | null;
  apiResponse: any;
  browserResponse: any;
}

const SessionDebug: React.FC<SessionDebugProps> = ({ sessionId, apiResponse, browserResponse }) => {
  return (
    <div data-testid="session-debug" className="fixed top-4 right-4 bg-white p-4 rounded-lg shadow-lg border border-gray-200 max-w-md z-50">
      <h3 className="text-lg font-semibold mb-2">세션 디버그 정보</h3>
      <div className="space-y-2">
        <div>
          <span className="font-medium">세션 ID:</span>
          <span className="ml-2">{sessionId || '없음'}</span>
        </div>
        <div>
          <span className="font-medium">API 응답:</span>
          <pre className="mt-1 p-2 bg-gray-50 rounded text-sm overflow-auto max-h-32">
            {JSON.stringify(apiResponse, null, 2)}
          </pre>
        </div>
        <div>
          <span className="font-medium">브라우저 응답:</span>
          <pre className="mt-1 p-2 bg-gray-50 rounded text-sm overflow-auto max-h-32">
            {JSON.stringify(browserResponse, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default SessionDebug; 