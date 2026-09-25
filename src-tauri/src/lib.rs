use std::sync::Mutex;

use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::TrayIconBuilder,
    Manager, RunEvent, WindowEvent,
};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};
use tauri_plugin_shell::process::CommandChild;
#[cfg(not(debug_assertions))]
use tauri_plugin_shell::ShellExt;

struct BackendProcess(Mutex<Option<CommandChild>>);

fn reveal(app: &tauri::AppHandle, label: &str) {
    if let Some(window) = app.get_webview_window(label) {
        let _ = window.show();
        let _ = window.set_focus();
    }
}

fn toggle(app: &tauri::AppHandle, label: &str) {
    if let Some(window) = app.get_webview_window(label) {
        if window.is_visible().unwrap_or(false) {
            let _ = window.hide();
        } else {
            let _ = window.show();
            let _ = window.set_focus();
        }
    }
}

pub fn run() {
    let quick_shortcut = Shortcut::new(Some(Modifiers::CONTROL), Code::Space);
    let capture_shortcut = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::ALT), Code::KeyM);
    let quick_handler = quick_shortcut.clone();
    let capture_handler = capture_shortcut.clone();

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            None,
        ))
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(move |app, shortcut, event| {
                    if event.state() != ShortcutState::Pressed { return; }
                    if shortcut == &quick_handler { toggle(app, "quick"); }
                    if shortcut == &capture_handler { toggle(app, "capture"); }
                })
                .build(),
        )
        .setup(move |app| {
            // A shortcut may already belong to another application. The main app
            // must still start normally when Windows refuses either registration.
            let _ = app.global_shortcut().register(quick_shortcut);
            let _ = app.global_shortcut().register(capture_shortcut);

            let show = MenuItemBuilder::with_id("show", "Open Second Brain").build(app)?;
            let quit = MenuItemBuilder::with_id("quit", "Quit").build(app)?;
            let menu = MenuBuilder::new(app).items(&[&show, &quit]).build()?;
            TrayIconBuilder::new()
                .icon(app.default_window_icon().expect("application icon").clone())
                .tooltip("Second Brain")
                .menu(&menu)
                .on_menu_event(|app, event| match event.id().as_ref() {
                    "show" => reveal(app, "main"),
                    "quit" => app.exit(0),
                    _ => {}
                })
                .build(app)?;

            #[cfg(not(debug_assertions))]
            {
                let resource_dir = app.path().resource_dir()?;
                let (_events, child) = app
                    .shell()
                    .sidecar("second-brain-backend")?
                    .current_dir(resource_dir)
                    .spawn()?;
                app.manage(BackendProcess(Mutex::new(Some(child))));
            }
            #[cfg(debug_assertions)]
            app.manage(BackendProcess(Mutex::new(None)));
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                if window.label() == "main" {
                    api.prevent_close();
                    let _ = window.hide();
                }
            }
            if let WindowEvent::Focused(false) = event {
                if window.label() == "quick" || window.label() == "capture" {
                    let _ = window.hide();
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building Second Brain");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            if let Some(process) = app_handle.try_state::<BackendProcess>() {
                if let Ok(mut child) = process.0.lock() {
                    if let Some(child) = child.take() { let _ = child.kill(); }
                }
            }
        }
    });
}
