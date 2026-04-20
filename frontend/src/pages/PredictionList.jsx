// src/pages/PredictionList.jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function PredictionList() {
    const navigate = useNavigate()
    const [predictions, setPredictions] = useState([])
    const [loading, setLoading] = useState(false)

    const fetchPredictions = async () => {
        setLoading(true)
        try {
            const res = await api.get('/api/predict/list')
            setPredictions(res.data.data || [])
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { fetchPredictions() }, [])

    const formatAmt = (v) => v ? v.toLocaleString() + '원' : '-'
    const formatDate = (v) => v ? v.replace('T', ' ').slice(0, 16) : '-'

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="flex justify-between items-center mb-5">
                <h1 className="text-xl font-bold text-gray-800">예측결과 목록</h1>
                <button
                    onClick={() => navigate('/tender')}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition"
                >
                    입찰공고 목록
                </button>
            </div>

            <div className="bg-white rounded-xl shadow overflow-x-auto">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600">공고번호</th>
                        <th className="px-3 py-3 text-left font-semibold text-gray-600 min-w-64">공고명</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600">기초금액</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600">예측금액</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600">예측율</th>
                        <th className="px-3 py-3 text-center font-semibold text-gray-600">예측일시</th>
                    </tr>
                    </thead>
                    <tbody>
                    {loading ? (
                        <tr><td colSpan={6} className="text-center py-10 text-gray-400">로딩 중...</td></tr>
                    ) : predictions.length === 0 ? (
                        <tr><td colSpan={6} className="text-center py-10 text-gray-400">예측 결과가 없습니다</td></tr>
                    ) : predictions.map(p => (
                        <tr key={p.id} className="border-b border-gray-100 hover:bg-gray-50 transition">
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{p.공고번호}</td>
                            <td className="px-3 py-3 text-gray-800">{p.공고명}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatAmt(p.기초금액)}</td>
                            <td className="px-3 py-3 text-center font-semibold text-blue-600 whitespace-nowrap">{formatAmt(p.예측금액)}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{p.예측율 ? p.예측율 + '%' : '-'}</td>
                            <td className="px-3 py-3 text-center text-gray-600 whitespace-nowrap">{formatDate(p.regdate)}</td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}