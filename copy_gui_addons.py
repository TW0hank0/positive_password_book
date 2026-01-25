import os
import sys
import shutil


def main():
    target_dir = os.path.join(
        os.path.dirname(__file__),
        "ppb_gui_middle",
        "target",
        "release",
    )
    gui_middle_dir = os.path.join(
        os.path.dirname(__file__),
        "ppb_gui",
        "addons",
        "ppb_gui_middle",
    )
    match os.name:
        case "nt":
            gui_middle_file = os.path.join(
                gui_middle_dir, "ppb_gui_middle.dll"
            )
            target_file = os.path.join(
                target_dir, "ppb_gui_middle.dll"
            )
        case "posix":
            gui_middle_file = os.path.join(
                gui_middle_dir, "libppb_gui_middle.so"
            )
            target_file = os.path.join(
                target_dir, "libppb_gui_middle.so"
            )
        case _:
            print("錯誤！未知系統，僅支援nt(win), posix(linux)！")
            sys.exit(1)
    if (os.path.exists(gui_middle_file) is False) or (
        os.path.exists(target_file) is False
    ):
        print(
            f"檔案不存在 gui_middle_file：{gui_middle_file}，target_file：{target_file}"
        )
        sys.exit(1)
    else:
        shutil.copy(target_file, gui_middle_file)
        print(f"已將{target_file}複製到{gui_middle_file}")


if __name__ == "__main__":
    main()
