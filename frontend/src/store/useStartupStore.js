import { create } from 'zustand'
import * as api from '../services/api'

const useStartupStore = create((set, get) => ({
  startups: [],
  total: 0,
  loading: false,
  error: null,

  filters: {
    status: '',
    category: '',
    country: '',
    limit: 25,
    offset: 0,
  },

  setFilters: (filters) =>
    set((s) => ({
      filters: {
        ...s.filters,
        ...filters,
        offset: 0,
      },
    })),

  setOffset: (offset) =>
    set((s) => ({
      filters: {
        ...s.filters,
        offset,
      },
    })),

  fetchStartups: async () => {
    const { filters } = get()

    set({
      loading: true,
      error: null,
    })

    try {
      const params = {}

      if (filters.status) {
        params.status = filters.status
      }

      if (filters.category) {
        params.category = filters.category
      }

      if (filters.country) {
        params.country = filters.country
      }

      params.limit = filters.limit
      params.offset = filters.offset

      const { data } = await api.getStartups(params)

      set({
        startups: Array.isArray(data) ? data : [],
        total: Array.isArray(data) ? data.length : 0,
        loading: false,
      })
    } catch (e) {
      set({
        error: e.message,
        loading: false,
      })
    }
  },

  deleteStartup: async (id) => {
    await api.deleteStartup(id)
    await get().fetchStartups()
  },
}))

export default useStartupStore