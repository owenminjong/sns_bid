import { useState, useEffect } from "react";
import api from "../api";

export default function PredictModal({ bid, onClose }) {
    const [daeupcongList, setDaeupcongList] = useState([]);
    const [대업종, set대업종] = useState("");
    const [result, setResult] = useState(null);
    const [selectedUrate, setSelectedUrate] = useState(null);
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
        if (!bid.개찰일) {
            setError("개찰일 정보가 없습니다.");
            return;
        }
        setLoading(true);
        setError(null);
        setResult(null);
        setSaved(false);
        setSelectedUrate(null);

        try {
            const res = await api.post("/api/predict", {
                bssamt:  bid.기초금액,
                대업종:  대업종,
                예가범위: bid.예가범위 ?? "+3% ~ -3%",
                개찰일자: bid.개찰일.slice(0, 10),
            });
            setResult(res.data.data);
            setSelectedUrate(res.data.data.recommended_urate);
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
        if (!result || !selectedUrate) return;
        const selected = result.results.find(r => r.투찰률 === selectedUrate);
        if (!selected) return;

        setSaving(true);
        setError(null);
        try {
            await api.post("/api/predict/save", {
                bbscode:   String(bid.bbscode ?? ""),
                bidNtceNo: bid.공고번호,
                bidNtceNm: bid.공고명,
                bssamt:    bid.기초금액,
                Aamt:      bid.순공사원가 ?? 0,
                urate:     selectedUrate,
                preamt:    selected.predict_amt,
                preRate:   selected.predict_rate,
                preRate2:  selected.model_mae_pct,
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
    const selected = result?.results.find(r => r.투찰률 === selectedUrate);

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl mx-4 overflow-hidden">

                {/* 헤더 */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-800">낙찰가 예측</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">×</button>
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

                    {/* 에러 */}
                    {error && (
                        <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
                            {typeof error === "string" ? error : JSON.stringify(error)}
                        </p>
                    )}

                    {/* 예측 결과 - 3개 카드 */}
                    {result && (
                        <div className="space-y-2">
                            <p className="text-xs text-gray-500">투찰률을 선택하면 해당 금액으로 저장됩니다</p>
                            {result.results.map((r) => {
                                const isRecommended = r.투찰률 === result.recommended_urate;
                                const isSelected = r.투찰률 === selectedUrate;
                                return (
                                    <div
                                        key={r.투찰률}
                                        onClick={() => setSelectedUrate(r.투찰률)}
                                        className={`relative rounded-xl p-4 cursor-pointer border-2 transition-all ${
                                            isSelected
                                                ? "border-blue-500 bg-blue-50"
                                                : "border-gray-200 bg-white hover:border-blue-300"
                                        }`}
                                    >
                                        {isRecommended && (
                                            <span className="absolute top-2 right-2 text-xs bg-green-500 text-white px-2 py-0.5 rounded-full">
                                                추천
                                            </span>
                                        )}
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-semibold text-gray-700">
                                                투찰률 {r.투찰률}%
                                            </span>
                                            <span className="text-lg font-bold text-blue-700">
                                                {fmt(r.predict_amt)}원
                                            </span>
                                        </div>
                                        <div className="flex justify-between mt-1 text-xs text-gray-500">
                                            <span>예측 낙찰율 {r.predict_rate}%</span>
                                            <span>범위 {fmt(r.range.min)} ~ {fmt(r.range.max)}원</span>
                                        </div>
                                        {r.warning && (
                                            <p className="mt-1 text-xs text-amber-600">⚠️ {r.warning}</p>
                                        )}
                                    </div>
                                );
                            })}
                            <p className="text-xs text-gray-400 text-right">
                                모델 MAE ±{result.results[0]?.model_mae_pct}%
                            </p>
                            {saved && (
                                <p className="text-xs text-green-700 bg-green-50 rounded-lg px-3 py-2 text-center">
                                    ✅ 저장 완료 (투찰률 {selectedUrate}%)
                                </p>
                            )}
                        </div>
                    )}
                </div>

                {/* 푸터 */}
                <div className="flex gap-3 px-6 py-4 border-t border-gray-200">
                    <button
                        onClick={handlePredict}
                        disabled={loading}
                        className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        {loading ? "예측 중..." : "예측"}
                    </button>
                    {result && !saved && selectedUrate && (
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                            {saving ? "저장 중..." : `${selectedUrate}%로 저장`}
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