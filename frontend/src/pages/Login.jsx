// src/pages/Login.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Login() {
    const navigate = useNavigate()
    const [form, setForm] = useState({ username: '', password: '' })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')
        try {
            const res = await api.post('/api/auth/login', {
                sfid: form.username,
                sfpw: form.password,
            })
            localStorage.setItem('token', res.data.data.access_token)
            navigate('/tender')
        } catch (err) {
            setError('아이디 또는 비밀번호를 확인해주세요.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
            <div className="bg-white rounded-2xl shadow-lg p-10 w-96">
                <h1 className="text-3xl font-bold text-center text-gray-800 mb-1">숭늉샘 BID</h1>
                <p className="text-sm text-center text-gray-400 mb-8">공공입찰 낙찰가 예측 시스템</p>
                <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                    <input
                        className="border border-gray-300 rounded-lg px-4 py-3 text-sm outline-none focus:border-blue-500"
                        type="text"
                        placeholder="아이디"
                        value={form.username}
                        onChange={e => setForm({ ...form, username: e.target.value })}
                        required
                    />
                    <input
                        className="border border-gray-300 rounded-lg px-4 py-3 text-sm outline-none focus:border-blue-500"
                        type="password"
                        placeholder="비밀번호"
                        value={form.password}
                        onChange={e => setForm({ ...form, password: e.target.value })}
                        required
                    />
                    {error && <p className="text-red-500 text-xs">{error}</p>}
                    <button
                        className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg mt-2 transition"
                        type="submit"
                        disabled={loading}
                    >
                        {loading ? '로그인 중...' : '로그인'}
                    </button>
                </form>
            </div>
        </div>
    )
}