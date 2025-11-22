import random
import copy
import tkinter as tk
from tkinter import messagebox, font


# --- ロジッククラス (前回のコードをベースに調整) ---
class Sudoku3DLogic:
    def __init__(self, difficulty=40):
        self.size = 9
        self.layers = 9
        self.solution = self.generate_solution()
        # board: 現在の盤面, initial_board: 問題（変更不可部分）
        self.board = copy.deepcopy(self.solution)
        self.mask_board(difficulty)
        self.initial_board = copy.deepcopy(self.board)  # 初期状態を保存

    def generate_solution(self):
        # (前回のシフト法による簡易生成と同じ)
        base_layer = [[(r * 3 + r // 3 + c) % 9 + 1 for c in range(9)] for r in range(9)]
        nums = list(range(1, 10))
        random.shuffle(nums)
        mapper = {i + 1: nums[i] for i in range(9)}
        for r in range(9):
            for c in range(9):
                base_layer[r][c] = mapper[base_layer[r][c]]

        cube = []
        for z in range(9):
            layer = []
            shift = z * 3 + z  # より複雑なシフトに変更
            for r in range(9):
                row = []
                for c in range(9):
                    val = base_layer[r][c]
                    new_val = (val + shift - 1) % 9 + 1
                    row.append(new_val)
                layer.append(row)
            cube.append(layer)
        return cube

    def mask_board(self, difficulty):
        # 完全にランダムだと解けなくなる可能性があるため
        # 解答を維持しつつ、各ブロックからバランスよく消す簡易実装
        rng = random.Random()
        for z in range(self.layers):
            cells_to_remove = difficulty
            while cells_to_remove > 0:
                r, c = rng.randint(0, 8), rng.randint(0, 8)
                if self.board[z][r][c] != 0:
                    self.board[z][r][c] = 0
                    cells_to_remove -= 1

    def is_valid_move(self, z, r, c, num):
        """ルールチェック"""
        if num == 0: return True, ""

        # 1. 横(Row)
        for col_idx in range(9):
            if col_idx != c and self.board[z][r][col_idx] == num:
                return False, "横列(Row)に同じ数字があります"
        # 2. 縦(Column)
        for row_idx in range(9):
            if row_idx != r and self.board[z][row_idx][c] == num:
                return False, "縦列(Column)に同じ数字があります"
        # 3. 3x3ブロック
        box_r, box_c = (r // 3) * 3, (c // 3) * 3
        for i in range(3):
            for j in range(3):
                nr, nc = box_r + i, box_c + j
                if (nr != r or nc != c) and self.board[z][nr][nc] == num:
                    return False, "3x3ブロック内に同じ数字があります"
        # 4. 奥行き(Z軸)
        for i in range(9):
            if i != z and self.board[i][r][c] == num:
                return False, f"奥行き(Level {i + 1})の同じ場所に数字があります"

        return True, "OK"

    def get_pillar_info(self, r, c):
        """奥行きの情報を取得"""
        info = []
        for z in range(self.layers):
            val = self.board[z][r][c]
            info.append(str(val) if val != 0 else ".")
        return info


# --- GUIクラス (Tkinter) ---
class Sudoku3DGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Sudoku (9x9x9)")

        # 難易度設定（消すマスの数/層。多いほど難しい）
        self.logic = Sudoku3DLogic(difficulty=45)

        self.current_layer = 0
        self.selected_cell = None  # (row, col)

        self.setup_gui()
        self.draw_board()

    def setup_gui(self):
        # フォント設定
        self.num_font = font.Font(family="Helvetica", size=16, weight="bold")
        self.btn_font = font.Font(size=12)

        # メインコンテナ
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack()

        # --- 上部コントロールパネル ---
        control_panel = tk.Frame(main_frame)
        control_panel.pack(fill=tk.X, pady=(0, 10))

        btn_prev = tk.Button(control_panel, text="◀ Prev Layer", font=self.btn_font,
                             command=lambda: self.change_layer(-1))
        btn_prev.pack(side=tk.LEFT)

        self.layer_label = tk.Label(control_panel, text=f"Level {self.current_layer + 1} / 9", font=self.btn_font,
                                    width=15)
        self.layer_label.pack(side=tk.LEFT, padx=10)

        btn_next = tk.Button(control_panel, text="Next Layer ▶", font=self.btn_font,
                             command=lambda: self.change_layer(1))
        btn_next.pack(side=tk.LEFT)

        info_lbl = tk.Label(main_frame,
                            text="[操作] 左クリック:選択 / 数字キー(1-9):入力 / 0キー:消去 / 右クリック:奥行き確認",
                            font=("Gray", 10))
        info_lbl.pack(pady=(0, 5))

        # --- ナンプレ盤面 ---
        self.board_frame = tk.Frame(main_frame, bg="black", bd=2)  # 外枠を黒にして境界線を表現
        self.board_frame.pack()

        # 9x9のセル用ボタンを保持するリスト
        self.cells = [[None for _ in range(9)] for _ in range(9)]

        # 3x3のブロックごとにFrameを作成して太枠を表現
        for box_r in range(3):
            for box_c in range(3):
                block_frame = tk.Frame(self.board_frame, bg="white", bd=1, relief=tk.SOLID)
                block_frame.grid(row=box_r, column=box_c, padx=1, pady=1)

                for i in range(3):
                    for j in range(3):
                        r, c = box_r * 3 + i, box_c * 3 + j

                        # 各マスのボタン
                        btn = tk.Button(block_frame, text="", width=4, height=2, font=self.num_font,
                                        relief=tk.FLAT, bg="white",
                                        command=lambda r=r, c=c: self.select_cell(r, c))
                        btn.grid(row=i, column=j, padx=1, pady=1)

                        # 右クリックイベントをバインド
                        btn.bind("<Button-3>", lambda event, r=r, c=c: self.show_depth_info(r, c))

                        self.cells[r][c] = btn

        # キーイベントのバインド（ウィンドウ全体で受け取る）
        self.root.bind("<Key>", self.key_pressed)

    def change_layer(self, delta):
        """層を切り替える"""
        new_layer = self.current_layer + delta
        if 0 <= new_layer < self.logic.layers:
            self.current_layer = new_layer
            self.layer_label.config(text=f"Level {self.current_layer + 1} / 9")
            self.selected_cell = None  # レイヤー移動で選択解除
            self.draw_board()

    def draw_board(self):
        """現在の層の盤面を描画更新"""
        for r in range(9):
            for c in range(9):
                val = self.logic.board[self.current_layer][r][c]
                initial_val = self.logic.initial_board[self.current_layer][r][c]
                btn = self.cells[r][c]

                text = str(val) if val != 0 else ""
                btn.config(text=text)

                # 色の設定
                if (r, c) == self.selected_cell:
                    btn.config(bg="yellow")  # 選択中
                elif initial_val != 0:
                    btn.config(bg="#e0e0e0", fg="black")  # 初期配置（グレー）
                elif val != 0:
                    btn.config(bg="white", fg="blue")  # プレイヤー入力（青文字）
                else:
                    btn.config(bg="white")  # 空欄

    def select_cell(self, r, c):
        """セルを選択状態にする"""
        # 初期配置のセルは選択できないようにする
        if self.logic.initial_board[self.current_layer][r][c] == 0:
            self.selected_cell = (r, c)
            self.draw_board()
        else:
            # 選択解除したい場合はここを有効化
            # self.selected_cell = None
            self.draw_board()

    def key_pressed(self, event):
        """キーボード入力の処理"""
        if self.selected_cell is None:
            return

        r, c = self.selected_cell
        char = event.char
        keysym = event.keysym

        num = -1
        if '1' <= char <= '9':
            num = int(char)
        elif char == '0' or keysym in ['Delete', 'BackSpace']:
            num = 0

        if num != -1:
            # ルールチェックと入力反映
            valid, msg = self.logic.is_valid_move(self.current_layer, r, c, num)
            if valid:
                self.logic.board[self.current_layer][r][c] = num
                self.draw_board()
                # 入力成功したら選択解除するか、そのまま続けるか（好みで）
                # self.selected_cell = None
                # self.draw_board()
            else:
                messagebox.showwarning("エラー", msg)

    def show_depth_info(self, r, c):
        """右クリックで奥行き情報を表示"""
        pillar = self.logic.get_pillar_info(r, c)

        # 見やすいように整形
        info_text = f"座標 ({r + 1}, {c + 1}) の奥行き状況:\n\n"
        for z in range(9):
            mark = "← 現在地" if z == self.current_layer else ""
            info_text += f"Level {z + 1}: [ {pillar[z]} ] {mark}\n"

        info_text += "\n※同じ数字は入れられません。"
        messagebox.showinfo("奥行きチェック", info_text)


# --- メイン実行部 ---
if __name__ == "__main__":
    root = tk.Tk()
    # ウィンドウサイズが小さいと見づらいので適度に設定
    # root.geometry("600x700")
    gui = Sudoku3DGUI(root)
    root.mainloop()