export function toast(message: string) {
  window.dispatchEvent(new CustomEvent('cloudsaver-toast', { detail: message }))
}
