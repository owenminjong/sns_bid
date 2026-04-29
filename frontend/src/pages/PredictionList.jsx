// frontend/src/pages/PredictionList.jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

// ── 상세 모달 ─────────────────────────────────────────────
function DetailModal({ item, onClose }) {
    const fmt     = (n) => n?.toLocaleString() ?? '-'
    const fmtRate = (v) => (v != null && v > 0) ? v + '%' : '-'
    const fmtMAE  = (v) => v ? '±' + v + '%' : '-'
    const mae_amt = item.bssamt && item.preRate2
        ? Math.round(item.bssamt * item.preRate2 / 100).toLocaleString()
        : '-'
    const range_min = item.bssamt && item.preRate2 && item.preamt
        ? Math.round(item.preamt - item.bssamt * item.preRate2 / 100).toLocaleString()
        : '-'
    const range_max = item.bssamt && item.preRate2 && item.preamt
        ? Math.round(item.preamt + item.bssamt * item.preRate2 / 100).toLocaleString()
        : '-'

    useEffect(() => {
        const handler = (e) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [onClose])

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
            onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
        >
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
                {/* 헤더 */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-800">예측 상세</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">×</button>
                </div>

                <div className="px-6 py-5 space-y-4">
                    {/* 공고 정보 */}
                    <div className="bg-gray-50 rounded-xl p-4 space-y-1 text-sm">
                        <p className="font-medium text-gray-900">{item.bidNtceNm || '-'}</p>
                        <p className="text-gray-500">{item.bidNtceNo}</p>
                    </div>

                    {/* 수치 정보 */}
                    <div className="space-y-3 text-sm">
                        <div className="flex justify-between border-b border-gray-100 pb-2">
                            <span className="text-gray-500">기초금액</span>
                            <span className="font-medium text-gray-800">{fmt(item.bssamt)}원</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-2">
                            <span className="text-gray-500">A값 (순공사원가)</span>
                            <span className="font-medium text-gray-800">{fmt(item.Aamt)}원</span>
                        </div>
                        <div className="flex justify-between border-b border-gray-100 pb-2">
                            <span className="text-gray-500">투찰률</span>
                            <span className="font-medium text-gray-800">{fmtRate(item.urate)}</span>
                        </div>
                    </div>

                    {/* 예측 결과 */}
                    <div className="bg-blue-50 rounded-xl p-4 space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">예측 낙찰금액</span>
                            <span className="text-xl font-bold text-blue-700">{fmt(item.preamt)}원</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">예측 낙찰율</span>
                            <span className="text-lg font-semibold text-blue-600">{fmtRate(item.preRate)}</span>
                        </div>
                        <div className="flex justify-between items-center text-xs text-gray-500">
                            <span>±MAE {fmtMAE(item.preRate2)} ({mae_amt}원)</span>
                            <span>{range_min} ~ {range_max}원</span>
                        </div>
                    </div>

                    {/* 메타 */}
                    <div className="text-xs text-gray-400 flex justify-between">
                        <span>모델: {item.model_used ?? '-'}</span>
                        <span>저장일: {item.regdate}</span>
                    </div>
                </div>

                <div className="px-6 py-4 border-t border-gray-200">
                    <button
                        onClick={onClose}
                        className="w-full py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition"
                    >
                        닫기
                    </button>
                </div>
            </div>
        </div>
    )
}

// ── 메인 페이지 ───────────────────────────────────────────
export default function PredictionList() {
    const navigate = useNavigate()

    const [list, setList]             = useState([])
    const [page, setPage]             = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [total, setTotal]           = useState(0)
    const [loading, setLoading]       = useState(false)
    const [searchNo, setSearchNo]     = useState('')
    const [searchName, setSearchName] = useState('')
    const [selectedItem, setSelectedItem] = useState(null)  // 상세 모달

    const fetchList = async (p = 1) => {
        setLoading(true)
        try {
            const res = await api.get('/api/predict/list', {
                params: { page: p, bidNtceNo: searchNo, bidNtceNm: searchName }
            })
            setList(res.data.data)
            setTotal(res.data.total)
            setTotalPages(res.data.total_pages)
            setPage(p)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { fetchList() }, [])

    const handleSearch = (e) => {
        e.preventDefault()
        fetchList(1)
    }

    const formatAmt  = (v) => v ? (v / 100000000).toFixed(2) + '억' : '-'
    const formatRate = (v) => (v != null && v > 0) ? v + '%' : '-'
    const formatMAE  = (v) => v ? '±' + v + '%' : '-'

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            {/* 헤더 */}
            <div className="flex justify-between items-center mb-5">
                <h1 className="text-xl font-bold text-gray-800">예측 결과 목록</h1>
                <button
                    onClick={() => navigate('/tender')}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition"
                >
                    입찰공고
                </button>
            </div>

            {/* 검색 */}
            <form onSubmit={handleSearch} className="flex gap-2 mb-4">
                <input
                    className="border border-gray-300 rounded-lg px-4 py-2 text-sm outline-none focus:border-blue-500 w-44"
                    type="text" placeholder="공고번호" value={searchNo}
                    onChange={e => setSearchNo(e.target.value)}
                />
                <input
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm outline-none focus:border-blue-500"
                    type="text" placeholder="공고명 검색" value={searchName}
                    onChange={e => setSearchName(e.target.value)}
                />
                <button type="submit" className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition">
                    검색
                </button>
            </form>

            <p className="text-xs text-gray-500 mb-2">총 {total.toLocaleString()}건</p>

            {/* 테이블 */}
            <div className="bg-white rounded-xl shadow overflow-x-auto">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">공고번호</th>
                        <th className="px-3 py-3 text-left font-semibold text-gray-600 min-w-64">공고명</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">기초금액</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">투찰률</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">예측낙찰율</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">예측금액</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">±MAE</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">저장일</th>
                    </tr>
                    </thead>
                    <tbody>
                    {loading ? (
                        <tr><td colSpan={8} className="text-center py-10 text-gray-400">로딩 중...</td></tr>
                    ) : list.length === 0 ? (
                        <tr><td colSpan={8} className="text-center py-10 text-gray-400">데이터 없음</td></tr>
                    ) : list.map((item) => (
                        <tr
                            key={item.psn}
                            className="border-b border-gray-100 hover:bg-blue-50 transition cursor-pointer"
                            onClick={() => setSelectedItem(item)}
                        >
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{item.bidNtceNo}</td>
                            <td className="px-3 py-3 text-gray-800">{item.bidNtceNm}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatAmt(item.bssamt)}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatRate(item.urate)}</td>
                            <td className="px-3 py-3 text-center font-medium text-blue-600 whitespace-nowrap">{formatRate(item.preRate)}</td>
                            <td className="px-3 py-3 text-center font-medium text-blue-700 whitespace-nowrap">{formatAmt(item.preamt)}</td>
                            <td className="px-3 py-3 text-center text-gray-500 whitespace-nowrap">{formatMAE(item.preRate2)}</td>
                            <td className="px-3 py-3 text-center text-gray-500 whitespace-nowrap">{item.regdate}</td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>

            {/* 페이징 */}
            <div className="flex justify-center items-center gap-4 mt-5">
                <button
                    className="px-5 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40 transition"
                    disabled={page <= 1} onClick={() => fetchList(page - 1)}
                >이전</button>
                <span className="text-sm text-gray-600">{page} / {totalPages}</span>
                <button
                    className="px-5 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40 transition"
                    disabled={page >= totalPages} onClick={() => fetchList(page + 1)}
                >다음</button>
            </div>

            {/* 상세 모달 */}
            {selectedItem && (
                <DetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />
            )}
        </div>
    )
}