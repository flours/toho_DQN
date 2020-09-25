import ctypes
import time
import numpy as np
import cv2
import pyautogui

# 東方紅魔郷操作ユーティリティ


class toho_env:
    # 初期化処理
    def __init__(self, ch=1, width=84, height=84):
        # キーコード定義
        self.LEFT = 0x25
        self.UP = 0x26
        self.RIGHT = 0x27
        self.DOWN = 0x28
        self.Z = 0x5a
        self.X = 0x58
        self.SHIFT = 0x10
        # 自作スクリーンショット及び評価値生成dll読み込み
        self.libc = ctypes.WinDLL("Project5.dll")
        # メイン画面スクリーンショット読み込み用のサイズ定義
        self.x = 384 * 448 * 3
        # ライフボード(残りライフが星で表示されてる部分)受け取り用サイズ定義
        self.life_board_size = 144*48*3
        # バッファ作成
        self.UBYTE_Array = ctypes.c_ubyte * self.x
        self.Life_Board = ctypes.c_ubyte*self.life_board_size
        # dllが使用する変数初期化
        self.i_arr = [0*self.x]
        self.i_arr_c = self.UBYTE_Array(*self.i_arr)
        self.life_pointer = ctypes.c_int(0)
        self.reward_pointer = ctypes.c_int(0)
        self.done_pointer = ctypes.c_int(0)
        self.loc_x = ctypes.c_int(0)
        self.loc_y = ctypes.c_int(0)
        # step関数(project5を参照)の関数の引数及び戻り値の定義
        self.libc.step.restype = None
        self.libc.step.argtypes = (ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(
            ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        # テンプレートマッチ用の関数の引数及び戻り値の定義
        self.libc.templatematch.restype = ctypes.c_int
        self.libc.templatematch.argtypes = (ctypes.POINTER(
            ctypes.c_ubyte), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

        # 変数初期化
        self.life_board_arr = [0*self.life_board_size]
        self.life_board_arr_c = self.Life_Board(*self.life_board_arr)
        self.ch = ch
        self.width = width
        self.height = height
        self.frame_count = 0
        self.life = 2
        # マウスが端っこにいくとプログラムを終了する処理を無効化
        pyautogui.FAILSAFE = False
    # カーソルキー入力処理　押下キー文字列のリストを渡す

    def press_cursor(self, keys):
        for key in keys:
            #　キーを押す
            pyautogui.keyDown(key)
        for key in ['left', 'up', 'right', 'down']:
            if not key in keys:
                # キーを話す
                pyautogui.keyUp(key)
    # 移動する、actionは整数型、0:左 1:上 2:右 3:下 4:静止 5:左上 6:左下 7:右上 8:右下

    def action(self, action):
        keys = [['left'], ['up'], ['right'], ['down'], [], ['left', 'up'], [
            'left', 'down'], ['right', 'up'], ['right', 'down']]
        # print(keys[action[0]])
        self.press_cursor(keys[action[0]])

        # if action[1]==0:
        #     pyautogui.keyUp('z')
        # if action[1]==1:
        #     pyautogui.keyDown('z')

        # 常にZボタンを押しっぱなし
        pyautogui.keyDown('z')

    # dllの評価関数を呼び結果を返す、ゲームオーバー時はゲーム復帰処理を行う
    def step2(self, action):
        # dll関数呼び出し
        self.libc.step(action[0], self.i_arr_c, self.reward_pointer,
                       self.life_pointer, self.done_pointer)
        # dll関数のスクリーンショットをnumpy arrayにキャスト
        image = np.ctypeslib.as_array(self.i_arr_c).reshape(448, 384, 3)
        # サイズを変更
        image = cv2.resize(image, (self.width, self.height))
        # ゲームオーバー確認
        if self.done_pointer.value == 1:
            self.press_cursor([])
            pyautogui.keyUp('z')
            print('GameOver')
        # 画像、評価値、ゲームオーバーフラグ、None(なんで？)を返す
        return image, self.reward_pointer.value, self.done_pointer.value, None

    # テンプレートマッチを行う
    def temp_match(self):
        self.libc.templatematch(
            self.i_arr_c, self.reward_pointer, self.life_pointer)
        return self.reward_pointer.value, self.life_pointer.value

    # python側で評価を行う場合に使うメソッド、dll側に移行してるので使ってないと思う

    def step(self, action):
        # メイン画面取得
        self.libc.capture_foreground(self.i_arr_c)
        image = np.ctypeslib.as_array(self.i_arr_c).reshape(448, 384, 3)
        image = cv2.flip(image, 0)
        # ライフボード取得
        self.libc.capture_life_board(self.life_board_arr_c)
        life_img = np.ctypeslib.as_array(
            self.life_board_arr_c).reshape(48, 144, 3)
        life_img = cv2.flip(life_img, 0)

        life = 0
        done = False
        reward = 0

        # 特定のピクセルを確認してライフを計算(ライフボードのy座標8,x座標8+16*Nの画素値が128以上であればライフはN+1である)
        for j in range(9):
            life += life_img[8, 8 + 16 * j][2] // 128
        #　ライフに変化(extendはしたことないのでいったん無視)があった場合は評価値をマイナス
        if self.life != life:
            self.life = life
            reward -= 1
        # 生き残っているフレームが10フレームごとに評価値加算
        self.frame_count += 1
        if self.frame_count % 10 == 0:
            reward += 0.05

        # ゲームオーバーチェック、ある画素がある値のときにゲームオーバーと判定する,今コンティニュー、はいの状態かいいえの状態化で少し処理を分岐する
        if life == 0:
            if (image[283, 228] == [87, 87, 174]).all() and (image[273, 189] == [59, 59, 117]).all() and (image[203, 168] == [126, 126, 126]).all():
                self.press_cursor([])
                pyautogui.keyUp('z')
                reward -= 1
                done = True
            elif (image[251, 203] == [87, 87, 174]).all() and (image[237, 177] == [90, 90, 179]).all() and (image[249, 187] == [93, 93, 185]).all():
                self.press_cursor([])
                pyautogui.keyUp('z')
                reward -= 1
                done = True
        # 時々すでに1回zを押してしまっているのでその対策に一画面進んだ状態かどいうかをチェック(たぶん)
        elif (image[280, 348] == [187, 187, 187]).all() and (image[225, 357] == [33, 41, 45]).all():
            self.press_cursor([])
            pyautogui.keyUp('z')
            reward -= 1
            done = True
        elif (image[436, 44] == [0, 0, 0]).all() and (image[434, 25] == [0, 0, 0]).all():
            self.press_cursor([])
            pyautogui.keyUp('z')
            reward -= 1
            done = True

        # 画像をニューラルネットにかけるためにサイズ変更,channelサイズも変更する
        image = cv2.resize(image, (self.width, self.height))
        if self.ch == 1:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if not done:
            self.action(action)

        return image, reward, done, None

    # ゲームオーバー及びプログラム開始時に呼ばれる、isfirstがTrueな時は最初なのでタイトル画面から始めたい場合はisfirstのif文内でゲームスタートまで移動する処理を描く
    def reset(self, isfirst):
        self.frame_count = 0
        if isfirst:
            return
        else:
            self.GameOverAction()
    # ゲームオーバー時の処理ゲームオーバーのどの画面化を確認し、少し分岐しているKeyPressでいい感じにキーを押すはず

    def GameOverAction(self):
        self.press_cursor([])
        pyautogui.keyUp('z')
        self.libc.capture_foreground(self.i_arr_c)
        image = np.ctypeslib.as_array(self.i_arr_c).reshape(448, 384, 3)
        image = cv2.flip(image, 0)
        if (image[251, 203] == [87, 87, 174]).all() and (image[237, 177] == [90, 90, 179]).all() and (image[249, 187] == [93, 93, 185]).all():
            self.KeyPress('down', 3, 0.1, 0)
        if (image[280, 348] == [187, 187, 187]).all() and (image[225, 357] == [33, 41, 45]).all():
            pass
        else:
            self.KeyPress('z', 3, 0.2, 0.5)
        self.KeyPress('esc', 0, 0.2, 1.5)
        self.KeyPress('z', 0, 0.2, 1)
        self.KeyPress('right', 0, 0.1, 0.5)
        self.KeyPress('z', 0, 0.2, 1.5)
        self.KeyPress('z', 0, 0.2, 1.5)
        self.KeyPress('z', 0, 0.2, 1.5)
        self.KeyPress('z', 0, 0.2, 1.5)
        self.KeyPress('z', 0, 0.2, 1.5)
        self.KeyPress('z', 0, 0.2, 1.5)
    # ゲームオーバー時のキーを押す処理 ボタンを押す前にin_sleepだけ処理を待ちボタンを押してからthrow_sleepだけスリープしボタンを話してからout_sleepだけスリープする

    def KeyPress(self, input_key, in_sleep, throw_sleep, out_sleep):
        time.sleep(in_sleep)
        pyautogui.keyDown(input_key)
        time.sleep(throw_sleep)
        pyautogui.keyUp(input_key)
        time.sleep(out_sleep)
