import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


# 練習１：ビームクラス
class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__ (self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.centery = bird.rct.centery
        self.rct.left = bird.rct.right  
        # 追加機能5.1 弾チェンジ
        self.keys = pg.key.get_pressed()
        self.v = [(+10, 0), (+0.1, 0)]
        if self.keys[pg.K_x]: # 設置型用
            self.vx, self.vy = self.v[1]
        else: #連射用
            self.vx, self.vy = self.v[0]

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)    


# 追加機能5：
class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, phase: int):
        """
        phaseに基づき異なる爆弾の円をSurfaceを生成する
        引数 phase：爆弾の難易度(1~5)
        """
        # 色、点数、フェーズを同じ値を用いてあげる
        self.hp = phase
        self.score_value = phase
        self.phase = phase
        # 半径、色の変更
        rad = 10 + (phase - 1) * 2
        r = max(255 - (phase -1) * 40, 100)
        g = 0
        b = min((phase - 1) * 25, 255)
        color = (r, g, b)

        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))

        # ダメージを受けたら、白くする
        self.damage_img = pg.Surface((2*rad, 2*rad), pg.SRCALPHA) # SRCALPHAで四隅を透明に
        pg.draw.circle(self.damage_img, (255, 255,255), (rad, rad), rad)

        # ダメージ用のカウンター
        self.damage_img_f = 0

        self.rct = self.img.get_rect()
        self.rct.center = random.randint(30, WIDTH), random.randint(30, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

        # 追加機能5：ダメージエフェクトを描写の切り替え
        c_img = self.img
        if self.damage_img_f > 0:
            c_img = self.damage_img
            self.damage_img_f -= 1
                
        screen.blit(c_img, self.rct)


# 追加機能１
class Score:
    """
    スコアを表示するクラス
    """
    def __init__(self):
        """
        スコア表示の設定をする
        引数：なし
        """
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)  # 青色
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rct = self.image.get_rect()
        self.rct.center = 100, HEIGHT - 50  # 画面左下付近

    def update(self, screen: pg.Surface):
        """
        現在のスコアを左下に表示する
        引数：screen:：ゲーム画面
        """
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rct)


# 追加機能3：
class Explosion:
    """
    爆発を描写するクラス
    """
    def __init__(self, bomb: Bomb):
            """
            爆発の画像を生成する
            引数：bomb：爆発したbomb
            """
            img = pg.image.load("fig/explosion.gif")
            f_img = pg.transform.flip(img, True, True)
            self.imgs = [img, f_img]
            self.image = self.imgs[0]
            self.rct = self.image.get_rect()
            self.rct.center = bomb.rct.center  # 画面左下付近
            self.life = 10
    def update(self, screen: pg.Surface):
        """
        爆発のフレームを減少させ、画像を切り替え描写
        引数：screen:：ゲーム画面
        """
        if self.life > 0:
            self.life -= 1
            self.image = self.imgs[self.life // 5 % 2]
            screen.blit(self.image, self.rct)


#追加機能5：
class Energy:
    """
    ビームの回数を可視化する
    """
    def __init__(self):
        """
        エネルギーの表示の設定をする
        引数：なし
        """
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)  # 青色
        self.value = "EEEEE"
        
        self.image = self.font.render(f"Energy: {self.value}", 0, self.color)
        self.rct = self.image.get_rect()
        self.rct.center = WIDTH - 150 , 50  # 画面左下付近
    def update(self, screen: pg.Surface):
        """
        現在のエネルギーを右上に表示する
        引数：screen:：ゲーム画面
        """
        self.image = self.font.render(f"Energy: {self.value}", 0, self.color)
        screen.blit(self.image, self.rct)
       

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    
    # 練習５：複数の爆弾をリストで作成
    bombs = [Bomb(phase = 1) for _ in range(5)]
    # 追加機能1：スコア用
    score = Score()
    # 追加機能2：マルチビーム管理用リスト
    beams = ()
    # 追加機能3：爆発用のリスト
    exps = []
    # 追加機能4：フェーズ
    phase = 1
    # 追加機能5：エネルギー用
    eng = Energy()
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                if len(beams) < 5:
                    beams.append(Beam(bird)) # 追加機能2：beamをどんどん増やせるように処理    
                    # 追加機能5：
                    eng.value = "E" * len(beams) + "X" * (5 - len(beams))

        screen.blit(bg_img, [0, 0])

        # 練習２・５：爆弾とビームの衝突判定
        for bomb in bombs:
            for beam in beams:
                if beam is not None and bomb is not None:
                    if beam.rct.colliderect(bomb.rct):
                        if beam in beams: # 衝突したらビームを消す
                            beams.remove(beam)
                        #　追加機能5：爆弾の体力
                        bomb.hp -= 1
                        bomb.damage_img_f = 10

                        if bomb.hp <= 0: #HPが０の時
                            # 追加機能3：爆発を描写
                            exps.append(Explosion(bomb))
                            # 当たった爆弾をNoneにして無効化

                            # 同時ヒット時対策(複数被弾無効化)
                            if bomb in bombs:
                                idx = bombs.index(bomb)
                                bombs[idx] = None
                            # スコア倍率の変更
                            score.value += bomb.score_value  
                            bird.change_img(6, screen)  # 練習３：喜びを表示(爆破したときのみ)

                        pg.display.update()
                        break
            # 追加機能5：ビームが消滅次第エ年るぎーを復活させる
            eng.value = "X" * len(beams) + "E" * (5 - len(beams))

        # 練習５：爆弾リストを更新
        bombs = [bomb for bomb in bombs if bomb is not None]

        # もし爆弾が0個なら、新たに5つ補充
        if len(bombs) == 0:
            phase += 1
            if phase >= 6: #フェーズ６以降は開発中
                bombs = []
            else: # フェーズ1~5
                bombs = [Bomb(phase=phase) for _ in range(5)]

        # 追加機能2：ビームリストの更新
        beams = [beam for beam in beams if check_bound(beam.rct) == (True, True)]

        # 練習４・５：こうかとんと爆弾の衝突判定
        for bomb in bombs:
            if bomb is not None and bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                # 練習4：Gameoverを表示
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        for beam in beams:  # 追加機能2：ビームを更新・描画
            beam.update(screen) 

        # 追加機能3：爆発リストの更新・描写
        for exp in exps:
            exp.update(screen)    
        exps = [exp for exp in exps if exp.life > 0]
        
        # 練習５：爆弾を更新・描画
        for bomb in bombs:
            bomb.update(screen)

        # 追加機能1：スコア表示
        score.update(screen)
        eng.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
