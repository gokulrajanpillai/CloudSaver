export function useApi() {
  return {
    get: async <T>(path: string): Promise<T> => {
      const response = await fetch(path)
      return response.json() as Promise<T>
    },
  }
}
