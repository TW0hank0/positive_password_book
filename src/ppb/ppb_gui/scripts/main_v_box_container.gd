extends Node

var counter: float = 0.0


# 預載入場景
const APP_DATA_SCENE = preload("res://app_data.tscn")
var app_datas = []

func _process(delta: float):
	if (counter + delta) > 1.0:
		counter = 0.0
		var data_string = GDMiddleApi.gd_text_io(["get_data"], ProjectSettings.globalize_path("user://"))
		var data = JSON.parse_string(data_string)
		print(data_string)
		print(data)
	else:
		counter += delta

func create_app_data_panel(acc_text: String):
	# 1. 建立場景實體
	var panel = APP_DATA_SCENE.instantiate()
	# 2. 安全取得 Label 子節點
	var acc_label = panel.get_node("item_container_acc/HBoxContainer/value")
	if acc_label == null:
		push_error("找不到 Label 節點！請確認場景結構")
		panel.queue_free()
		return null
	# 3. 修改文字
	acc_label.text = acc_text
	# 4. 加入場景樹（例如加到主 UI）
	add_child(panel)
	return panel

func _ready():
	copy_backend_file()
	_process(1)

func copy_backend_file() -> void:
	var backend_res_dir = ProjectSettings.globalize_path("res://addons/ppb_backend/")
	var backend_user_dir = ProjectSettings.globalize_path("user://addons/ppb_backend/")
	create_nested_dirs(ProjectSettings.globalize_path("user://addons/ppb_backend/"))
	if OS.has_feature("Windows"):
		var file_name = "ppb_backend_win.exe"
		var result: bool = copy_file(backend_res_dir + file_name, backend_user_dir + file_name)
		if not result:
			push_error("無法複製後端檔案！")
	elif OS.has_feature("Linux"):
		var file_name = "ppb_backend_linux"
		var result: bool = copy_file(backend_res_dir + file_name, backend_user_dir + file_name)
		if not result:
			push_error("無法複製後端檔案！")

func create_nested_dirs(dir_path: String):
	if not DirAccess.dir_exists_absolute(dir_path):
		var error = DirAccess.make_dir_recursive_absolute(dir_path)
		if error == OK:
			pass
		else:
			push_error("建立失敗，錯誤碼: %d" % [error])

# 複製單一檔案
func copy_file(src: String, dst: String) -> bool:
	var src_file = FileAccess.open(src, FileAccess.READ)
	if not src_file:
		push_error("讀取失敗: %s" % [src])
		return false
	var dst_file = FileAccess.open(dst, FileAccess.WRITE)
	if not dst_file:
		src_file.close()
		push_error("寫入失敗: %s" % [dst])
		return false
	dst_file.store_buffer(src_file.get_buffer(src_file.get_length()))
	src_file.close()
	dst_file.close()
	return true
