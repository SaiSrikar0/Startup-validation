import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Something went wrong'
    return Promise.reject(new Error(msg))
  }
)

// Startups
export const getStartups = (params) => api.get('/startups', { params })
export const getStartup  = (id)     => api.get(`/startups/${id}`)
export const createStartup = (data) => api.post('/startups', data)
export const updateStartup = (id, data) => api.put(`/startups/${id}`, data)
export const deleteStartup = (id)   => api.delete(`/startups/${id}`)

// Predict
export const predictSuccess = (data) => api.post('/predict/success', data)

// Competition
export const analyzeCompetition = (data) => api.post('/analysis/competition', data)

// Health
export const getHealth = () => api.get('/health')
