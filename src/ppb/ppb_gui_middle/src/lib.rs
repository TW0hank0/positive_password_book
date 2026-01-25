//! ppb_gui_middle 是`ppb_gui`的中間件
//use godot::classes::class_macros::private::virtuals::ProjectSettings;
use godot::prelude::*;
//use positive_tool_rs;
//use serde::{Deserialize, Serialize};
//use serde_json;
use std;
use std::path::PathBuf;
use std::process;

#[derive(Clone)]
struct ReqType {
    actions: Vec<String>,
    timestamp: u64,
}

/* #[godot_api]
impl INode for ReqType {
    fn init(base: Base<Node>) -> Self {
        Self { base }
    }
} */

impl ReqType {
    pub fn to_backend_server_text(&self) -> String {
        return format!(
            "{{\"actions\": {:?}, \"timestamp\": {}}}",
            &self.actions, &self.timestamp
        );
    }
}

struct PpbGuiMiddle;

#[gdextension]
unsafe impl ExtensionLibrary for PpbGuiMiddle {}

/* #[derive(Serialize, Deserialize, Debug)]
struct RespType {
    resp_get_data: String,
} */

/* #[derive(Serialize, Deserialize, Debug)]
struct RespGetDataType {} */

/* #[derive(GodotClass)]
#[class(base=Node)]
struct JsonFileBridge {
    base: Base<Node>,
}

#[godot_api]
impl INode for JsonFileBridge {
    fn init(base: Base<Node>) -> Self {
        Self { base }
    }
} */

#[derive(GodotClass)]
#[class(base=Node)]
struct GDMiddleApi {
    base: Base<Node>,
}

#[godot_api]
impl INode for GDMiddleApi {
    fn init(base: Base<Node>) -> Self {
        Self { base }
    }
}

#[godot_api]
impl GDMiddleApi {
    #[func]
    fn gd_text_io(
        actions: godot::builtin::Array<GString>,
        project_user_dir_path: GString,
    ) -> GString {
        godot_print!("檔案路徑：{}", project_user_dir_path);
        let backend_dir_path = PathBuf::from(project_user_dir_path.to_string())
            .join("addons")
            .join("ppb_backend")
            .canonicalize()
            .unwrap();
        let mut arg_actions: Vec<String> = Vec::new();
        for action in actions.iter_shared() {
            arg_actions.push(action.to_string());
        }
        let server_output = text_io(arg_actions, backend_dir_path);
        return server_output.to_godot();
    }

    #[func]
    fn gd_write_bin_file(file_content: godot::builtin::PackedByteArray, file_path: GString) {
        let file_path_pathbuf = PathBuf::from(file_path.to_string());
        if !file_path_pathbuf.exists() || !file_path_pathbuf.is_absolute() {
            godot_error!("檔案不存在：{}", file_path_pathbuf.display());
        }
        if write_bin_file(file_content.to_string(), file_path_pathbuf).is_err() {
            godot_error!("檔案寫入錯誤！");
        }
    }
}

fn text_io(arg_actions: Vec<String>, backend_dir_path: PathBuf) -> String {
    let actions = arg_actions;
    //let project_root_path: PathBuf = ptrs::pt::find_project_root_path("positive_password_book").unwrap();
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let req_data = ReqType {
        actions: actions,
        timestamp: timestamp,
    };
    let req_data_clone = req_data.clone();
    let req_data_str = req_data_clone.to_backend_server_text().to_string();
    let backend_file_path: PathBuf;
    #[cfg(target_os = "windows")]
    {
        backend_file_path = PathBuf::from(backend_dir_path.clone()).join("ppb_backend_win.exe");
    }
    #[cfg(target_family = "unix")]
    {
        backend_file_path = PathBuf::from(backend_dir_path.clone()).join("ppb_backend_linux.bin");
    }
    if !backend_file_path.exists() || !backend_file_path.is_absolute() {
        eprintln!("檔案不存在！路徑：{}", backend_file_path.display())
    }
    godot_print!("檔案路徑：{}", backend_file_path.display());
    let process_result = process::Command::new(backend_file_path)
        .args(["server", "--server-text-arg", &req_data_str])
        .output()
        .unwrap();
    //TODO:待完成錯誤處理
    let server_output: String = String::from_utf8_lossy(&process_result.stdout)
        .to_owned()
        .to_string();
    return server_output;
}

fn write_bin_file(file_content: String, file_path: PathBuf) -> std::io::Result<()> {
    if !file_path.exists() {
        eprintln!("檔案不存在！")
    }
    std::fs::write(file_path, file_content)
}

/* #[godot_api]
impl JsonFileBridge {
    // Godot 呼叫：寫入請求到 JSON 檔
    #[func]
    fn write_request(&mut self, cmd: GString, data: VarDictionary, file_path: GString) -> bool {
        let mut payload_map = serde_json::Map::new();
        for key in data.keys().iter_shared() {
            let val = data.get(key.clone()).unwrap_or(Variant::nil());
            payload_map.insert(key.to_string(), variant_to_json(val));
        }

        let shared_data = SharedData {
            command: cmd.to_string(),
            payload: serde_json::Value::Object(payload_map),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs(),
        };

        match serde_json::to_string_pretty(&shared_data) {
            Ok(json_str) => {
                // 使用 std::fs 同步寫入（非主執行緒安全，但 Godot 單執行緒）
                match fs::write(Path::new(file_path.as_str()), json_str) {
                    Ok(_) => true,
                    Err(_) => false,
                }
            }
            Err(_) => false,
        }
    }

    // Godot 呼叫：從 JSON 檔讀取回應
    #[func]
    fn read_response(&mut self, file_path: GString) -> Dictionary {
        let path = Path::new(file_path.as_str());
        if !path.exists() {
            return make_error_dict("FILE_NOT_FOUND");
        }

        match fs::read_to_string(path) {
            Ok(content) => match serde_json::from_str::<SharedData>(&content) {
                Ok(shared) => {
                    let mut dict = Dictionary::new();
                    dict.insert("command".into(), shared.command.into());
                    dict.insert("payload".into(), json_to_variant(&shared.payload));
                    dict.insert("timestamp".into(), (shared.timestamp as i64).into());
                    dict
                }
                Err(_) => make_error_dict("JSON_PARSE_FAIL"),
            },
            Err(_) => make_error_dict("READ_FAIL"),
        }
    }
}

// 輔助函式：簡化錯誤回傳
fn make_error_dict(msg: &str) -> Dictionary {
    let mut dict = Dictionary::new();
    dict.insert("error".into(), msg.into());
    dict
}

// Variant 與 JSON 互轉（同前例，保留簡化版）
fn variant_to_json(var: Variant) -> serde_json::Value {
    if var.is_nil() {
        return serde_json::Value::Null;
    }
    match var.get_type() {
        VariantType::STRING => serde_json::Value::String(var.to::<GString>().to_string()),
        VariantType::INT => serde_json::Value::Number((var.to::<i64>() as i32).into()),
        VariantType::FLOAT => serde_json::Value::Number(
            serde_json::Number::from_f64(var.to::<f64>()).unwrap_or_default(),
        ),
        VariantType::BOOL => serde_json::Value::Bool(var.to::<bool>()),
        VariantType::DICTIONARY => {
            let dict = var.to::<Dictionary>();
            let mut map = serde_json::Map::new();
            for key in dict.keys().iter_shared() {
                let val = dict.get(key.clone()).unwrap_or(Variant::nil());
                map.insert(key.to_string(), variant_to_json(val));
            }
            serde_json::Value::Object(map)
        }
        _ => serde_json::Value::String("unsupported".into()),
    }
}

fn json_to_variant(value: &serde_json::Value) -> Variant {
    match value {
        serde_json::Value::Null => Variant::nil(),
        serde_json::Value::Bool(b) => (*b).into(),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                (i as i64).into()
            } else {
                n.as_f64().unwrap_or(0.0).into()
            }
        }
        serde_json::Value::String(s) => GString::from(s.as_str()).into(),
        serde_json::Value::Array(arr) => {
            let mut list = VariantArray::new();
            for item in arr {
                list.push(json_to_variant(item));
            }
            list.into()
        }
        serde_json::Value::Object(obj) => {
            let mut dict = Dictionary::new();
            for (k, v) in obj {
                dict.insert(GString::from(k.as_str()), json_to_variant(v));
            }
            dict.into()
        }
    }
}
 */
