import { invoke } from '@tauri-apps/api/core'

const SERVICE = 'CloudSaver'

export async function setKeyringValue(key: string, value: string) {
  await invoke('plugin:keyring|set_password', {
    service: SERVICE,
    username: key,
    password: value,
  })
}

export async function getKeyringValue(key: string): Promise<string | null> {
  return invoke<string | null>('plugin:keyring|get_password', {
    service: SERVICE,
    username: key,
  })
}

export async function deleteKeyringValue(key: string) {
  await invoke('plugin:keyring|delete_password', {
    service: SERVICE,
    username: key,
  })
}
