import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import TenderNotice from './pages/TenderNotice'
import PredictionList from './pages/PredictionList'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/" replace />
}

function App() {
  return (
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/tender" element={<PrivateRoute><TenderNotice /></PrivateRoute>} />
          <Route path="/predictions" element={<PrivateRoute><PredictionList /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
  )
}

export default App