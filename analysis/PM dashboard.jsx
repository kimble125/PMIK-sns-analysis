import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

// 대시보드 데이터
const platformData = [
  { platform: "카카오스토리", type: "개인", posts: 4580, avgChars: 424, engagement: 5.28, hashtags: 8.4 },
  { platform: "네이버 블로그", type: "개인", posts: 2137, avgChars: 1702, engagement: 11.04, hashtags: 13.0 },
  { platform: "유튜브", type: "개인", posts: 1869, avgChars: 201, engagement: 1590, hashtags: 0 },
  { platform: "인스타그램", type: "개인", posts: 1291, avgChars: 438, engagement: 13.28, hashtags: 8.7 },
  { platform: "페이스북", type: "개인", posts: 277, avgChars: 203, engagement: 36.27, hashtags: 9.8 },
  { platform: "네이버 카페", type: "커뮤", posts: 275, avgChars: 628, engagement: 2.99, hashtags: 0 },
  { platform: "밴드", type: "커뮤", posts: 153, avgChars: 79, engagement: 0, hashtags: 0 }
];

const clusterData = [
  { platform: "네이버 블로그", normalPct: 98.7, highPct: 1.3, normalEng: 8.5, highEng: 204, multiplier: 24 },
  { platform: "유튜브", normalPct: 99.4, highPct: 0.6, normalEng: 5467, highEng: 670216, multiplier: 122 },
  { platform: "인스타그램", normalPct: 99.7, highPct: 0.3, normalEng: 12.7, highEng: 207, multiplier: 16 },
  { platform: "카카오스토리", normalPct: 92.6, highPct: 7.4, normalEng: 3.9, highEng: 22.6, multiplier: 6 }
];

const rfeData = [
  { segment: "Champions", blog: 59, kakao: 28, color: "#10b981" },
  { segment: "Loyal", blog: 151, kakao: 75, color: "#3b82f6" },
  { segment: "New Active", blog: 92, kakao: 54, color: "#8b5cf6" },
  { segment: "Potential", blog: 216, kakao: 112, color: "#f59e0b" },
  { segment: "At Risk", blog: 95, kakao: 56, color: "#ef4444" },
  { segment: "Hibernating", blog: 141, kakao: 67, color: "#6b7280" }
];

const hashtagData = [
  { tag: "독일피엠", count: 3819 },
  { tag: "액티바이즈", count: 1735 },
  { tag: "파워칵테일", count: 1563 },
  { tag: "리스토레이트", count: 1561 },
  { tag: "피엠인터내셔널", count: 1355 },
  { tag: "피트라인", count: 869 },
  { tag: "피엠주스", count: 667 },
  { tag: "건강기능식품", count: 572 }
];

const lengthEngData = {
  blog: [
    { range: "0-100", engagement: 2.75 },
    { range: "100-300", engagement: 6.22 },
    { range: "300-500", engagement: 4.86 },
    { range: "500-1K", engagement: 9.76 },
    { range: "1K-2K", engagement: 12.16 },
    { range: "2K+", engagement: 12.67 }
  ],
  kakao: [
    { range: "0-100", engagement: 5.04 },
    { range: "100-300", engagement: 3.90 },
    { range: "300-500", engagement: 3.18 },
    { range: "500-1K", engagement: 4.04 },
    { range: "1K-2K", engagement: 15.35 },
    { range: "2K+", engagement: 17.16 }
  ]
};

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6b7280'];

const Dashboard = () => {
  const [page, setPage] = useState(1);
  
  // 요약 카드 컴포넌트
  const SummaryCard = ({ title, value, subtitle, color = "blue" }) => (
    <div className={`bg-white rounded-lg p-4 shadow border-l-4 border-${color}-500`}>
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
      {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
    </div>
  );

  // 인사이트 카드
  const InsightCard = ({ title, content, icon }) => (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
      <div className="flex items-start gap-2">
        <span className="text-xl">{icon}</span>
        <div>
          <h4 className="font-semibold text-gray-800">{title}</h4>
          <p className="text-sm text-gray-600 mt-1">{content}</p>
        </div>
      </div>
    </div>
  );

  // 페이지 1: 플랫폼 간 비교
  const Page1 = () => (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg p-6">
        <h1 className="text-2xl font-bold">PM International Korea SNS 분석 대시보드</h1>
        <p className="text-blue-100 mt-1">7개 플랫폼 · 10,582개 게시물 · 1,146명 사용자 분석</p>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard title="총 게시물" value="10,582" subtitle="개인 채널 96% | 커뮤니티 4%" />
        <SummaryCard title="개인 채널 플랫폼" value="5개" subtitle="블로그, 유튜브, 인스타, FB, 카스" color="green" />
        <SummaryCard title="커뮤니티 플랫폼" value="2개" subtitle="네이버 카페 39개 + 밴드 26개" color="purple" />
        <SummaryCard title="분석 사용자" value="1,146명" subtitle="블로거 754명 + 카스 392명" color="orange" />
      </div>

      {/* 플랫폼별 게시물 수 & 평균 글자 수 */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg p-4 shadow">
          <h3 className="font-semibold text-gray-700 mb-4">플랫폼별 게시물 수</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={platformData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="platform" type="category" width={80} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="posts" fill="#3b82f6" radius={[0, 4, 4, 0]}>
                {platformData.map((entry, index) => (
                  <Cell key={index} fill={entry.type === "커뮤" ? "#8b5cf6" : "#3b82f6"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex gap-4 justify-center mt-2 text-xs">
            <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded"></span>개인 채널</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 bg-purple-500 rounded"></span>커뮤니티</span>
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow">
          <h3 className="font-semibold text-gray-700 mb-4">플랫폼별 평균 글자 수</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={platformData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="platform" type="category" width={80} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => `${v}자`} />
              <Bar dataKey="avgChars" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-gray-500 text-center mt-2">네이버 블로그가 가장 긴 콘텐츠 (1,702자)</p>
        </div>
      </div>

      {/* K-means 클러스터 인사이트 */}
      <div className="bg-white rounded-lg p-4 shadow">
        <h3 className="font-semibold text-gray-700 mb-4">K-means 클러스터링: 고성과 콘텐츠 특성</h3>
        <div className="grid grid-cols-4 gap-4">
          {clusterData.map((item, idx) => (
            <div key={idx} className="border rounded-lg p-3 bg-gray-50">
              <h4 className="font-medium text-gray-800">{item.platform}</h4>
              <div className="mt-2 space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">일반 콘텐츠</span>
                  <span className="font-medium">{item.normalPct}%</span>
                </div>
                <div className="flex justify-between text-blue-600">
                  <span>고성과 콘텐츠</span>
                  <span className="font-bold">{item.highPct}%</span>
                </div>
                <div className="pt-2 border-t">
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    {item.multiplier}배 engagement
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 핵심 인사이트 */}
      <div className="grid grid-cols-3 gap-4">
        <InsightCard 
          icon="🏷️" 
          title="해시태그 역설" 
          content="많은 해시태그 ≠ 높은 engagement. 고성과 콘텐츠는 오히려 적은 해시태그 (0~9개) 사용"
        />
        <InsightCard 
          icon="📊" 
          title="파레토 법칙" 
          content="유튜브에서 상위 0.6%가 122배 조회수 달성. 극단적 성과 집중 현상"
        />
        <InsightCard 
          icon="📝" 
          title="콘텐츠 길이" 
          content="네이버 블로그 1,000~2,000자, 카카오스토리 2,000자+에서 최고 engagement"
        />
      </div>
    </div>
  );

  // 페이지 2: 통합 인사이트
  const Page2 = () => (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg p-6">
        <h1 className="text-2xl font-bold">통합 인사이트 & 전략 제안</h1>
        <p className="text-purple-100 mt-1">RFE 세그먼트 · 해시태그 분석 · 콘텐츠 믹스</p>
      </div>

      {/* RFE 세그먼트 분포 */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg p-4 shadow">
          <h3 className="font-semibold text-gray-700 mb-4">RFE 세그먼트 분포 (네이버 블로그)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={rfeData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                dataKey="blog"
                label={({ segment, blog }) => `${segment}: ${blog}`}
                labelLine={false}
              >
                {rfeData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 justify-center mt-2">
            {rfeData.map((item, idx) => (
              <span key={idx} className="text-xs flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></span>
                {item.segment}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow">
          <h3 className="font-semibold text-gray-700 mb-4">콘텐츠 길이별 Engagement</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={lengthEngData.blog}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="engagement" stroke="#3b82f6" strokeWidth={2} name="네이버 블로그" dot={{ fill: '#3b82f6' }} />
            </LineChart>
          </ResponsiveContainer>
          <p className="text-xs text-gray-500 text-center">1,000자 이상에서 engagement 급상승</p>
        </div>
      </div>

      {/* 해시태그 TOP 8 */}
      <div className="bg-white rounded-lg p-4 shadow">
        <h3 className="font-semibold text-gray-700 mb-4">통합 해시태그 TOP 8</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={hashtagData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="tag" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={60} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 콘텐츠 믹스 & 전략 */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg p-4 shadow">
          <h3 className="font-semibold text-gray-700 mb-4">콘텐츠 믹스 (80/20 Rule)</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>네이버 블로그</span>
                <span className="text-green-600 font-medium">✓ 적정</span>
              </div>
              <div className="flex h-6 rounded-full overflow-hidden">
                <div className="bg-blue-500 flex items-center justify-center text-white text-xs" style={{ width: '32.4%' }}>32%</div>
                <div className="bg-green-500 flex items-center justify-center text-white text-xs" style={{ width: '67.6%' }}>68%</div>
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>프로모션</span>
                <span>가치 제공</span>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>카카오스토리</span>
                <span className="text-green-600 font-medium">✓ 적정</span>
              </div>
              <div className="flex h-6 rounded-full overflow-hidden">
                <div className="bg-blue-500 flex items-center justify-center text-white text-xs" style={{ width: '32.9%' }}>33%</div>
                <div className="bg-green-500 flex items-center justify-center text-white text-xs" style={{ width: '67.1%' }}>67%</div>
              </div>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4">* 권장: 프로모션 20~30% / 가치 70~80%</p>
        </div>

        <div className="bg-white rounded-lg p-4 shadow">
          <h3 className="font-semibold text-gray-700 mb-4">전략적 제안</h3>
          <div className="space-y-3 text-sm">
            <div className="flex gap-2">
              <span className="text-green-500 font-bold">1.</span>
              <span>해시태그 수 줄이기 (13개→9개 이하)</span>
            </div>
            <div className="flex gap-2">
              <span className="text-green-500 font-bold">2.</span>
              <span>장문 콘텐츠 강화 (1,000자+ 목표)</span>
            </div>
            <div className="flex gap-2">
              <span className="text-green-500 font-bold">3.</span>
              <span>At Risk 세그먼트 재활성화 (95명)</span>
            </div>
            <div className="flex gap-2">
              <span className="text-green-500 font-bold">4.</span>
              <span>Champions 콘텐츠 패턴 분석 및 공유</span>
            </div>
            <div className="flex gap-2">
              <span className="text-green-500 font-bold">5.</span>
              <span>커뮤니티 플랫폼 활성화 필요</span>
            </div>
          </div>
        </div>
      </div>

      {/* 커뮤니티 플랫폼 현황 */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-100">
        <h3 className="font-semibold text-gray-700 mb-3">커뮤니티 플랫폼 현황</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-purple-700">네이버 카페</h4>
            <p className="text-2xl font-bold text-gray-800">39개</p>
            <p className="text-xs text-gray-500">275개 게시물 · 평균 628자</p>
          </div>
          <div>
            <h4 className="text-sm font-medium text-pink-700">밴드</h4>
            <p className="text-2xl font-bold text-gray-800">26개</p>
            <p className="text-xs text-gray-500">153개 게시물 · 평균 79자</p>
          </div>
        </div>
        <p className="text-xs text-gray-600 mt-3 bg-white p-2 rounded">
          💡 커뮤니티 플랫폼은 전체의 4%에 불과하나, 충성 고객 그룹 내 구전 효과가 강함. 활성화 전략 필요
        </p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* 페이지 네비게이션 */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setPage(1)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              page === 1 ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            Page 1: 플랫폼 비교
          </button>
          <button
            onClick={() => setPage(2)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              page === 2 ? 'bg-purple-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            Page 2: 통합 인사이트
          </button>
        </div>

        {/* 페이지 콘텐츠 */}
        {page === 1 ? <Page1 /> : <Page2 />}
        
        {/* 푸터 */}
        <div className="mt-6 text-center text-xs text-gray-400">
          PM International Korea SNS Analysis Dashboard · 2024.12
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
