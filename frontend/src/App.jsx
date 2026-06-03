import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard    from './pages/Dashboard'
import Predict      from './pages/Predict'
import Compete      from './pages/Compete'
import Startups     from './pages/Startups'
import StartupDetail from './pages/StartupDetail'
import StartupForm  from './pages/StartupForm'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-7xl mx-auto px-6 pt-24 pb-16">
        <Routes>
          <Route path="/"                        element={<Dashboard />} />
          <Route path="/predict"                 element={<Predict />} />
          <Route path="/compete"                 element={<Compete />} />
          <Route path="/startups"                element={<Startups />} />
          <Route path="/startups/new"            element={<StartupForm />} />
          <Route path="/startups/:id"            element={<StartupDetail />} />
          <Route path="/startups/:id/edit"       element={<StartupForm />} />
        </Routes>
      </main>
    </div>
  )
}
