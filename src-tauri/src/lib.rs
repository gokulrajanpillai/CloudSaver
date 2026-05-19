pub mod menu;
pub mod tray;

use std::sync::Mutex;

use tauri::{AppHandle, Emitter, Listener, Manager, State};
use tauri_plugin_notification::NotificationExt;
use tauri_plugin_shell::ShellExt;

pub struct SidecarState {
    pub port: Mutex<Option<u16>>,
}

#[tauri::command]
async fn get_sidecar_port(state: State<'_, SidecarState>) -> Result<u16, String> {
    state
        .port
        .lock()
        .map_err(|_| "Sidecar state lock poisoned".to_string())?
        .ok_or_else(|| "Sidecar not ready".to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_keyring::init())
        .plugin(tauri_plugin_updater::init())
        .manage(SidecarState {
            port: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![get_sidecar_port])
        .setup(|app| {
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                spawn_sidecar(app_handle).await;
            });
            app.handle().listen("scan-complete-notify", |event| {
                let body = event.payload();
                let _ = event
                    .app_handle()
                    .notification()
                    .builder()
                    .title("CloudSaver - Scan Complete")
                    .body(body)
                    .show();
            });
            menu::setup_menu(app)?;
            tray::setup_tray(app)?;
            Ok(())
        })
        .register_uri_scheme_protocol("cloudsaver", handle_oauth_callback)
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

async fn spawn_sidecar(app: AppHandle) {
    let shell = app.shell();
    let sidecar = shell.sidecar("cloudsaver-sidecar");
    let Ok(command) = sidecar else {
        let _ = app.emit("sidecar-error", "sidecar binary not found");
        return;
    };

    let spawned = command.spawn();
    let Ok((mut rx, _child)) = spawned else {
        let _ = app.emit("sidecar-error", "failed to spawn sidecar");
        return;
    };

    while let Some(event) = rx.recv().await {
        if let tauri_plugin_shell::process::CommandEvent::Stdout(line) = event {
            let line = String::from_utf8_lossy(&line);
            if let Some(port_str) = line.strip_prefix("CLOUDSAVER_PORT=") {
                if let Ok(port) = port_str.trim().parse::<u16>() {
                    let state = app.state::<SidecarState>();
                    if let Ok(mut stored_port) = state.port.lock() {
                        *stored_port = Some(port);
                    }
                    let _ = app.emit("sidecar-ready", port);
                    break;
                }
            }
        }
    }
}

fn handle_oauth_callback(
    app: &AppHandle,
    request: tauri::http::Request<Vec<u8>>,
) -> tauri::http::Response<Vec<u8>> {
    let uri = request.uri().to_string();
    let _ = app.emit("oauth-callback", uri);
    tauri::http::Response::builder()
        .status(200)
        .body(b"Auth complete. Return to CloudSaver.".to_vec())
        .expect("failed to build OAuth callback response")
}
