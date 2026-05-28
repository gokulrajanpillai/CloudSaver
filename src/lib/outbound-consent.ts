export interface OutboundConsentRequest {
  action: string
  destination: string
  dataShared: string
}

export function requestOutboundConsent(request: OutboundConsentRequest): boolean {
  const message = [
    `${request.action} will leave CloudSaver's local-only boundary.`,
    `Destination: ${request.destination}`,
    `Data shared: ${request.dataShared}`,
    'Continue?',
  ].join('\n\n')
  return window.confirm(message)
}

export function guardExternalLink(event: MouseEvent<HTMLAnchorElement>, request: OutboundConsentRequest) {
  if (!requestOutboundConsent(request)) {
    event.preventDefault()
  }
}
import type { MouseEvent } from 'react'
