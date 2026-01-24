#extends VBoxContainer


extends Node

func _ready():
	pass
	var gd_middle_api = GDMiddleApi.new()
	#var bridge = JsonFileBridge.new()
	#add_child(bridge)
	# 寫入請求
	#var req = {"player_id": 123, "action": "jump"}
	#var success = bridge.write_request("player_action", req, "res://shared/request.json")
	# （模擬 Python 後端處理後）讀取回應
	#var response = bridge.read_response("res://shared/response.json")
	#if response.has("error"):
		#print("Error: ", response["error"])
	#else:
		#print("Got: ", response["payload"])
