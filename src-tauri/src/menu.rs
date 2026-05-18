use tauri::menu::{AboutMetadata, Menu, MenuItem, PredefinedMenuItem, Submenu};

pub fn setup_menu(app: &mut tauri::App) -> tauri::Result<()> {
    let about = PredefinedMenuItem::about(
        app,
        Some("About CloudSaver"),
        Some(AboutMetadata {
            name: Some("CloudSaver".to_string()),
            version: Some(app.package_info().version.to_string()),
            ..Default::default()
        }),
    )?;
    let preferences = MenuItem::with_id(app, "preferences", "Preferences", true, Some("CmdOrCtrl+,"))?;
    let quit = PredefinedMenuItem::quit(app, Some("Quit CloudSaver"))?;
    let app_menu = Submenu::with_items(
        app,
        "CloudSaver",
        true,
        &[&about, &PredefinedMenuItem::separator(app)?, &preferences, &quit],
    )?;

    let add_source = MenuItem::with_id(app, "add-source", "Add Source", true, Some("CmdOrCtrl+N"))?;
    let scan_all = MenuItem::with_id(
        app,
        "scan-all-sources",
        "Scan All Sources",
        true,
        Some("CmdOrCtrl+Shift+S"),
    )?;
    let export_report =
        MenuItem::with_id(app, "export-report", "Export Report", true, None::<&str>)?;
    let file_menu = Submenu::with_items(
        app,
        "File",
        true,
        &[&add_source, &scan_all, &PredefinedMenuItem::separator(app)?, &export_report],
    )?;

    let overview = MenuItem::with_id(app, "view-overview", "Overview", true, None::<&str>)?;
    let duplicates = MenuItem::with_id(app, "view-duplicates", "Duplicates", true, None::<&str>)?;
    let storage_map = MenuItem::with_id(app, "view-storage-map", "Storage Map", true, None::<&str>)?;
    let cleanup = MenuItem::with_id(app, "view-cleanup", "Cleanup Queue", true, None::<&str>)?;
    let view_menu = Submenu::with_items(
        app,
        "View",
        true,
        &[&overview, &duplicates, &storage_map, &cleanup],
    )?;

    let menu = Menu::with_items(app, &[&app_menu, &file_menu, &view_menu])?;
    app.set_menu(menu)?;
    Ok(())
}
