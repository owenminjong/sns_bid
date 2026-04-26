// frontend/src/pages/PredictionList.jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function PredictionList() {
    const navigate = useNavigate()

    const [list, setList]           = useState([])
    const [page, setPage]           = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [total, setTotal]         = useState(0)
    const [loading, setLoading]     = useState(false)
    const [searchNo, setSearchNo]   = useState('')
    const [searchName, setSearchName] = useState('')

    const fetchList = async (p = 1) => {
        setLoading(true)
        try {
            const res = await api.get('/api/predict/list', {
                params: {
                    page:      p,
                    bidNtceNo: searchNo,
                    bidNtceNm: searchName,
                }
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
                    onClick={() => navigate('/tenders')}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition"
                >
                    입찰공고
                </button>
            </div>

            {/* 검색 */}
            <form onSubmit={handleSearch} className="flex gap-2 mb-4">
                <input
                    className="border border-gray-300 rounded-lg px-4 py-2 text-sm outline-none focus:border-blue-500 w-44"
                    type="text"
                    placeholder="공고번호"
                    value={searchNo}
                    onChange={e => setSearchNo(e.target.value)}
                />
                <input
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm outline-none focus:border-blue-500"
                    type="text"
                    placeholder="공고명 검색"
                    value={searchName}
                    onChange={e => setSearchName(e.target.value)}
                />
                <button
                    type="submit"
                    className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition"
                >
                    검색
                </button>
            </form>

            {/* 총건수 */}
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
                        <tr key={item.psn} className="border-b border-gray-100 hover:bg-gray-50 transition">
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">
                                {item.bidNtceNo}
                            </td>
                            <td className="px-3 py-3 text-gray-800">{item.bidNtceNm}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">
                                {formatAmt(item.bssamt)}
                            </td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">
                                {formatRate(item.urate)}
                            </td>
                            <td className="px-3 py-3 text-center font-medium text-blue-600 whitespace-nowrap">
                                {formatRate(item.preRate)}
                            </td>
                            <td className="px-3 py-3 text-center font-medium text-blue-700 whitespace-nowrap">
                                {formatAmt(item.preamt)}
                            </td>
                            <td className="px-3 py-3 text-center text-gray-500 whitespace-nowrap">
                                {formatMAE(item.preRate2)}
                            </td>
                            <td className="px-3 py-3 text-center text-gray-500 whitespace-nowrap">
                                {item.regdate}
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>

            {/* 페이징 */}
            <div className="flex justify-center items-center gap-4 mt-5">
                <button
                    className="px-5 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40 transition"
                    disabled={page <= 1}
                    onClick={() => fetchList(page - 1)}
                >
                    이전
                </button>
                <span className="text-sm text-gray-600">{page} / {totalPages}</span>
                <button
                    className="px-5 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40 transition"
                    disabled={page >= totalPages}
                    onClick={() => fetchList(page + 1)}
                >
                    다음
                </button>
            </div>
        </div>
    )
}