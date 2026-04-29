// frontend/src/components/PredictModal.jsx
import { useState, useEffect } from "react";
import api from "../api";

const URATE_OPTIONS = [86.745, 87.745, 89.745];

export default function PredictModal({ bid, onClose }) {
    const [urate, setUrate] = useState(87.745);
    const [참여업체수, set참여업체수] = useState("");
    const [daeupcongList, setDaeupcongList] = useState([]);
    const [대업종, set대업종] = useState("");
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        api.get("/api/predict/daeupcong")
            .then((res) => {
                setDaeupcongList(res.data.data);
                const matched = res.data.data.includes(bid.대업종) ? bid.대업종 : "기타";
                set대업종(matched);
            })
            .catch(() => setError("업종 목록을 불러오지 못했습니다."));
    }, []);

    useEffect(() => {
        const handler = (e) => { if (e.key === "Escape") onClose(); };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, [onClose]);

    const handlePredict = async () => {
        if (!참여업체수 || parseInt(참여업체수) <= 0) {
            setError("참여업체수를 입력해주세요.");
            return;
        }
        if (!bid.개찰일) {
            setError("개찰일 정보가 없습니다.");
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);
        setSaved(false);

        try {
            const res = await api.post("/api/predict", {
                투찰률:    urate,
                bssamt:   bid.기초금액,
                참여업체수: parseInt(참여업체수),
                대업종:   대업종,
                예가범위:  bid.예가범위 ?? "+3% ~ -3%",
                개찰일자:  bid.개찰일.slice(0, 10),
            });
            setResult(res.data.data);
        } catch (err) {
            const detail = err.response?.data?.detail;
            if (Array.isArray(detail)) {
                setError(detail.map(d => d.msg).join(", "));
            } else {
                setError(detail || "예측 중 오류가 발생했습니다.");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!result) return;
        setSaving(true);
        setError(null);

        try {
            await api.post("/api/predict/save", {
                bbscode:   String(bid.bbscode ?? ""),
                bidNtceNo: bid.공고번호,
                bidNtceNm: bid.공고명,
                bssamt:    bid.기초금액,
                Aamt:      bid.순공사원가 ?? 0,
                urate:     urate,
                preamt:    result.predict_amt,
                preRate:   result.predict_rate,
                preRate2:  result.model_mae_pct,
            });
            setSaved(true);
        } catch (err) {
            const detail = err.response?.data?.detail;
            if (Array.isArray(detail)) {
                setError(detail.map(d => d.msg).join(", "));
            } else {
                setError(detail || "저장 중 오류가 발생했습니다.");
            }
        } finally {
            setSaving(false);
        }
    };

    const fmt = (n) => n?.toLocaleString() ?? "-";
    const 예가범위Label = bid.예가범위?.includes("3%") ? 3 : 2;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">

                {/* 헤더 */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-800">낙찰가 예측</h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
                    >
                        ×
                    </button>
                </div>

                <div className="px-6 py-5 space-y-5">

                    {/* 공고 정보 */}
                    <div className="bg-gray-50 rounded-xl p-4 space-y-1 text-sm text-gray-700">
                        <p className="font-medium text-gray-900 truncate">{bid.공고명}</p>
                        <p className="text-gray-500">{bid.공고번호} · {bid.수요기관}</p>
                        <div className="flex gap-4 mt-2 text-xs text-gray-500">
                            <span>기초금액 <span className="font-medium text-gray-800">{fmt(bid.기초금액)}원</span></span>
                            <span>예가범위 <span className="font-medium text-gray-800">±{예가범위Label}%</span></span>
                            <span>개찰일 <span className="font-medium text-gray-800">{bid.개찰일?.slice(0, 10) ?? "-"}</span></span>
                        </div>
                    </div>

                    {/* 입력 영역 */}
                    <div className="space-y-3">
                        {/* 투찰률 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">투찰률</label>
                            <div className="flex gap-2">
                                {URATE_OPTIONS.map((opt) => (
                                    <button
                                        key={opt}
                                        onClick={() => setUrate(opt)}
                                        className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-colors ${
                                            urate === opt
                                                ? "bg-blue-600 text-white border-blue-600"
                                                : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                                        }`}
                                    >
                                        {opt}%
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* 대업종 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">대업종</label>
                            <select
                                value={대업종}
                                onChange={(e) => set대업종(e.target.value)}
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                {daeupcongList.map((c) => (
                                    <option key={c} value={c}>{c}</option>
                                ))}
                            </select>
                        </div>

                        {/* 참여업체수 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">참여업체수</label>
                            <input
                                type="number"
                                min="1"
                                value={참여업체수}
                                onChange={(e) => set참여업체수(e.target.value)}
                                placeholder="예: 50"
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    {/* 에러 */}
                    {error && (
                        <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
                            {typeof error === "string" ? error : JSON.stringify(error)}
                        </p>
                    )}

                    {/* 예측 결과 */}
                    {result && (
                        <div className="bg-blue-50 rounded-xl p-4 space-y-3">
                            {result.warning && (
                                <p className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                                    ⚠️ {result.warning}
                                </p>
                            )}
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-gray-600">예측 낙찰금액</span>
                                <span className="text-xl font-bold text-blue-700">
                                    {fmt(result.predict_amt)}원
                                </span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-gray-600">예측 낙찰율</span>
                                <span className="text-lg font-semibold text-blue-600">
                                    {result.predict_rate}%
                                </span>
                            </div>
                            <div className="flex justify-between items-center text-xs text-gray-500">
                                <span>예측 범위 (±MAE {result.model_mae_pct}%)</span>
                                <span>{fmt(result.range.min)} ~ {fmt(result.range.max)}원</span>
                            </div>
                            {saved && (
                                <p className="text-xs text-green-700 bg-green-50 rounded-lg px-3 py-2 text-center">
                                    ✅ 저장 완료
                                </p>
                            )}
                        </div>
                    )}
                </div>

                {/* 푸터 버튼 */}
                <div className="flex gap-3 px-6 py-4 border-t border-gray-200">
                    <button
                        onClick={handlePredict}
                        disabled={loading}
                        className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {loading ? "예측 중..." : "예측"}
                    </button>
                    {result && !saved && (
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                            {saving ? "저장 중..." : "저장"}
                        </button>
                    )}
                    <button
                        onClick={onClose}
                        className="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                    >
                        닫기
                    </button>
                </div>
            </div>
        </div>
    );
}