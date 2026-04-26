import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import PredictModal from '../components/PredictModal'

export default function TenderNotice() {
    const navigate = useNavigate()
    const [bids, setBids] = useState([])
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [total, setTotal] = useState(0)
    const [loading, setLoading] = useState(false)
    const [searchName, setSearchName] = useState('')
    const [searchNo, setSearchNo] = useState('')
    const [selectedBid, setSelectedBid] = useState(null)   // PredictModal 연결

    const fetchBids = async (p = 1) => {
        setLoading(true)
        try {
            const res = await api.get('/api/bids', {
                params: { page: p, 공고명: searchName, 공고번호: searchNo }
            })
            setBids(res.data.data)
            setTotal(res.data.total)
            setTotalPages(res.data.total_pages)
            setPage(p)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { fetchBids() }, [])

    const handleSearch = (e) => {
        e.preventDefault()
        fetchBids(1)
    }

    const handleLogout = () => {
        localStorage.removeItem('token')
        navigate('/')
    }

    const formatAmt = (v) => v ? (v / 100000000).toFixed(1) + '억' : '-'
    const formatDate = (v) => v ? v.replace('T', ' ').slice(0, 16) : '-'
    const formatRate = (v) => (v != null && v > 0) ? v + '%' : '-'   // 100% 초과 정상 데이터 허용

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            {/* 헤더 */}
            <div className="flex justify-between items-center mb-5">
                <h1 className="text-xl font-bold text-gray-800">입찰공고 목록</h1>
                <div className="flex gap-2">
                    <button
                        onClick={() => navigate('/predictions')}
                        className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm rounded-lg transition"
                    >
                        예측결과
                    </button>
                    <button
                        onClick={handleLogout}
                        className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm rounded-lg transition"
                    >
                        로그아웃
                    </button>
                </div>
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
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">수요기관</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">지역</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">기초금액</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">추정가격</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">A값</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">순공사원가</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">투찰률</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600 whitespace-nowrap">개찰일</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600">예측</th>
                    </tr>
                    </thead>
                    <tbody>
                    {loading ? (
                        <tr><td colSpan={11} className="text-center py-10 text-gray-400">로딩 중...</td></tr>
                    ) : bids.length === 0 ? (
                        <tr><td colSpan={11} className="text-center py-10 text-gray-400">데이터 없음</td></tr>
                    ) : bids.map(bid => (
                        <tr key={bid.id} className="border-b border-gray-100 hover:bg-gray-50 transition">
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">
                                {bid.공고번호}-{bid.공고차수}
                            </td>
                            <td className="px-3 py-3 text-gray-800">{bid.공고명}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{bid.수요기관}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{bid.지역}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatAmt(bid.기초금액)}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatAmt(bid.추정가격)}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatAmt(bid.A값)}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatAmt(bid.순공사원가)}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatRate(bid.투찰률)}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatDate(bid.개찰일)}</td>
                            <td className="px-3 py-3 text-center">
                                <button
                                    onClick={() => setSelectedBid(bid)}
                                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition"
                                >
                                    예측
                                </button>
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
                    onClick={() => fetchBids(page - 1)}
                >
                    이전
                </button>
                <span className="text-sm text-gray-600">{page} / {totalPages}</span>
                <button
                    className="px-5 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40 transition"
                    disabled={page >= totalPages}
                    onClick={() => fetchBids(page + 1)}
                >
                    다음
                </button>
            </div>

            {/* PredictModal */}
            {selectedBid && (
                <PredictModal
                    bid={selectedBid}
                    onClose={() => setSelectedBid(null)}
                />
            )}
        </div>
    )
}