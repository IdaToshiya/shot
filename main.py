import pygame
import psycopg2
from pygame.locals import *
import random
import time

# PostgreSQL データベース接続
def connect_db():
    return psycopg2.connect(
        dbname="game_db", user="postgres", password="admin", host="localhost", port="5432"
    )

# プレイヤー情報をデータベースに保存
def save_player_info(player_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO players (name) VALUES (%s) RETURNING player_id", (player_name,))
    player_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return player_id

# プレイヤーの得点を更新
def update_score(player_id, score, wins):
    conn = connect_db()
    cursor = conn.cursor()
    
    # 正しいSQL文
    cursor.execute("UPDATE players SET score = %s, wins = %s WHERE player_id = %s", (score, wins, player_id))
    
    conn.commit()
    cursor.close()
    conn.close()

# 対戦結果を保存
def save_match_result(player1_id, player2_id, winner_id, score1, score2):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO matches (player_1_id, player_2_id, winner_id, score_player_1, score_player_2) VALUES (%s, %s, %s, %s, %s)",
        (player1_id, player2_id, winner_id, score1, score2)
    )
    conn.commit()
    cursor.close()
    conn.close()

# ゲームの初期化
pygame.init()

# フルスクリーン設定
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("ローカルマルチプレイヤーシューティングゲーム")
screen_width, screen_height = screen.get_size()  # 画面サイズを取得

# プレイヤー設定
player1_pos = [100, screen_height // 2]
player2_pos = [screen_width - 150, screen_height // 2]
player1_health = 100
player2_health = 100
player1_score = 0
player2_score = 0
player1_wins = 0  # プレイヤー1の勝利数
player2_wins = 0  # プレイヤー2の勝利数

# プレイヤー弾
player1_bullets = []
player2_bullets = []

# プレイヤー名入力のためのテキストボックスの設定
font = pygame.font.Font(None, 36)

input_box1 = pygame.Rect(screen_width // 4 - 150, screen_height // 2 - 50, 300, 50)
input_box2 = pygame.Rect(3 * screen_width // 4 - 150, screen_height // 2 - 50, 300, 50)

color_inactive = pygame.Color('lightskyblue3')
color_active = pygame.Color('dodgerblue2')
color = color_inactive

active1 = False
active2 = False
text1 = ''
text2 = ''
player1_name = ''
player2_name = ''

# プレイヤー情報入力関数
def draw_input_boxes():
    pygame.draw.rect(screen, color, input_box1, 2)
    pygame.draw.rect(screen, color, input_box2, 2)
    txt_surface1 = font.render(text1, True, color)
    txt_surface2 = font.render(text2, True, color)
    screen.blit(txt_surface1, (input_box1.x + 5, input_box1.y + 5))
    screen.blit(txt_surface2, (input_box2.x + 5, input_box2.y + 5))

# 合計勝利数のランキング（ベスト5）を取得
def get_player_ranking():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, SUM(total_wins) AS total_wins_sum FROM players GROUP BY name ORDER BY total_wins_sum DESC LIMIT 5")  # TOP 5を取得
    ranking = cursor.fetchall()
    cursor.close()
    conn.close()
    return ranking

# ランキングを表示
def show_ranking():
    ranking = get_player_ranking()
    font = pygame.font.Font(None, 48)

    screen.fill((0, 0, 0))
    
    # ランキングタイトル
    title = font.render("Top 5 Player Ranking", True, (255, 255, 255))
    screen.blit(title, (screen_width // 2 - title.get_width() // 2, screen_height // 4 - 50))
    ranking_text = font.render("Press Enter to Start", True, (255, 255, 255))
    screen.blit(ranking_text, (screen_width // 2 - ranking_text.get_width() // 2, screen_height // 2 + 50))

    # ランキングリストの表示
    y_offset = screen_height // 4
    for i, (name, total_wins) in enumerate(ranking):
        rank_text = font.render(f"{i+1}. {name} - Wins: {total_wins}", True, (255, 255, 255))
        screen.blit(rank_text, (screen_width // 2 - rank_text.get_width() // 2, y_offset))
        y_offset += 50  # 次の順位の位置をずらす

    pygame.display.flip()
    
    # エンターキーが押されるまで待機
    waiting_for_enter = True
    while waiting_for_enter:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                quit()

            if event.type == KEYDOWN:
                if event.key == K_RETURN:  # エンターキーが押されたら
                    waiting_for_enter = False  # 名前入力画面に移行

        pygame.time.Clock().tick(30)

# ゲーム開始前の画面
def wait_for_input():
    global active1, active2, text1, text2, player1_name, player2_name
    waiting_for_input = True

    # ランキングを表示
    show_ranking()

    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                quit()

            if event.type == MOUSEBUTTONDOWN:
                # クリックでテキストボックスをアクティブにする
                if input_box1.collidepoint(event.pos):
                    active1 = True
                    active2 = False
                    color = color_active
                elif input_box2.collidepoint(event.pos):
                    active2 = True
                    active1 = False
                    color = color_active
                else:
                    active1 = False
                    active2 = False
                    color = color_inactive

            if event.type == KEYDOWN:
                if active1:
                    if event.key == K_RETURN:
                        player1_name = text1
                        text1 = ''  # 名前が決定した後、入力フィールドをクリアしない
                        active1 = False
                    elif event.key == K_BACKSPACE:
                        text1 = text1[:-1]
                    else:
                        text1 += event.unicode

                if active2:
                    if event.key == K_RETURN:
                        player2_name = text2
                        text2 = ''  # 名前が決定した後、入力フィールドをクリアしない
                        active2 = False
                    elif event.key == K_BACKSPACE:
                        text2 = text2[:-1]
                    else:
                        text2 += event.unicode

        screen.fill((0, 0, 0))
        draw_input_boxes()

        # 名前が入力されたら画面に表示する
        font2 = pygame.font.Font(None, 48)
        text_player1 = font2.render(f"Player 1: {player1_name}" if player1_name else "Enter Player 1 Name", True, (255, 255, 255))
        text_player2 = font2.render(f"Player 2: {player2_name}" if player2_name else "Enter Player 2 Name", True, (255, 255, 255))

        screen.blit(text_player1, (screen_width // 4 - 150, screen_height // 2 + 10))
        screen.blit(text_player2, (3 * screen_width // 4 - 150, screen_height // 2 + 10))

        pygame.display.flip()

        if player1_name and player2_name:
            waiting_for_input = False

        pygame.display.flip()
        pygame.time.Clock().tick(30)

# プレイヤー情報をデータベースに保存
def start_game():
    global player1_id, player2_id
    player1_id = save_player_info(player1_name)
    player2_id = save_player_info(player2_name)

# プレイヤーの描画
def draw_player(position, color):
    pygame.draw.rect(screen, color, (position[0], position[1], 50, 50))

# 弾の描画
def draw_bullets(bullets, color):
    for bullet in bullets:
        pygame.draw.rect(screen, color, (bullet[0], bullet[1], 5, 15))

# 弾の移動
def move_bullets(bullets):
    for bullet in bullets[:]:
        bullet[0] += bullet[2]  # 弾の方向に合わせてx座標を更新
        if bullet[0] < 0 or bullet[0] > screen_width:  # 画面外に出た弾を削除
            bullets.remove(bullet)

# 衝突判定
def check_collision(bullets, player_pos):
    global player1_health, player2_health
    for bullet in bullets[:]:
        if (player_pos[0] < bullet[0] < player_pos[0] + 50) and (player_pos[1] < bullet[1] < player_pos[1] + 50):
            bullets.remove(bullet)
            return True
    return False

# ゲームの状態をリセット
def reset_game():
    global player1_health, player2_health
    player1_health = 100
    player2_health = 100

# リザルト画面
def show_result(winner):
    global player1_wins, player2_wins, player1_score, player2_score

    # 勝者IDを決定
    winner_id = player1_id if winner == "Player 1" else player2_id
    
    # 試合結果を保存
    save_match_result(player1_id, player2_id, winner_id, player1_score, player2_score)

    font = pygame.font.Font(None, 72)
    result_text = font.render(f"Winner: {winner}", True, (255, 255, 255))
    restart_text = font.render("Press R to Restart or Q to Quit", True, (255, 255, 255))
    
    screen.fill((0, 0, 0))
    screen.blit(result_text, (screen_width // 2 - result_text.get_width() // 2, screen_height // 2 - 50))
    screen.blit(restart_text, (screen_width // 2 - restart_text.get_width() // 2, screen_height // 2 + 50))
    
    if winner == "Player 1":
        player1_wins += 1
        update_score(player1_id, player1_score, player1_wins)
    else:
        player2_wins += 1
        update_score(player2_id, player2_score, player2_wins)

    pygame.display.flip()

    # 結果画面に遷移
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_r:
                    # ゲームの状態をリセットしてループを再開
                    reset_game()
                    game_loop()
                    waiting_for_input = False  # 結果画面から抜ける
                if event.key == K_q:
                    # Qが押された場合、total_winsを更新
                    update_total_wins(player1_id)  # Player 1のtotal_winsを更新
                    update_total_wins(player2_id)  # Player 2のtotal_winsを更新
                    pygame.quit()
                    quit()

        pygame.display.flip()
        pygame.time.Clock().tick(30)

# total_winsをリザルト画面で更新する
def update_total_wins(player_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    # 現在のtotal_winsを取得
    cursor.execute("SELECT total_wins, wins FROM players WHERE player_id = %s", (player_id,))
    current_total_wins, current_wins = cursor.fetchone()
    
    # 新しいtotal_winsの計算
    new_total_wins = current_total_wins + current_wins
    
    # total_winsの更新
    cursor.execute("UPDATE players SET total_wins = %s WHERE player_id = %s", (new_total_wins, player_id))
    
    conn.commit()
    cursor.close()
    conn.close()


# ゲームループ
def game_loop():
    global player1_health, player2_health, player1_score, player2_score, player1_wins, player2_wins
    player1_pos = [100, screen_height // 2]
    player2_pos = [screen_width - 150, screen_height // 2]
    player1_bullets = []
    player2_bullets = []
    player1_shooting = False
    player2_shooting = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[K_w] and player1_pos[1] > 0:
            player1_pos[1] -= 5
        if keys[K_s] and player1_pos[1] < screen_height - 50:
            player1_pos[1] += 5
        if keys[K_a] and player1_pos[0] > 0:
            player1_pos[0] -= 5
        if keys[K_d] and player1_pos[0] < screen_width - 50:
            player1_pos[0] += 5

        # プレイヤー1の弾の発射
        if keys[K_SPACE] and not player1_shooting:
            player1_bullets.append([player1_pos[0] + 50, player1_pos[1] + 20, 10])
            player1_shooting = True
        if not keys[K_SPACE]:
            player1_shooting = False

        if keys[K_i] and player2_pos[1] > 0:
            player2_pos[1] -= 5
        if keys[K_k] and player2_pos[1] < screen_height - 50:
            player2_pos[1] += 5
        if keys[K_j] and player2_pos[0] > 0:
            player2_pos[0] -= 5
        if keys[K_l] and player2_pos[0] < screen_width - 50:
            player2_pos[0] += 5

        # プレイヤー2の弾の発射（ENTERキー）
        if keys[K_RETURN] and not player2_shooting:
            player2_bullets.append([player2_pos[0], player2_pos[1] + 20, -10])
            player2_shooting = True
        if not keys[K_RETURN]:
            player2_shooting = False

        # 弾の移動
        move_bullets(player1_bullets)
        move_bullets(player2_bullets)

        # 衝突判定
        if check_collision(player1_bullets, player2_pos):
            player2_health -= 10
            player1_score += 1
        if check_collision(player2_bullets, player1_pos):
            player1_health -= 10
            player2_score += 1

        # ゲームオーバー判定
        if player1_health <= 0 or player2_health <= 0:
            winner = "Player 1" if player1_health > player2_health else "Player 2"
            show_result(winner)
            return

        screen.fill((0, 0, 0))

        # プレイヤーの描画
        draw_player(player1_pos, (255, 0, 0))
        draw_player(player2_pos, (0, 0, 255))

        # 弾の描画
        draw_bullets(player1_bullets, (255, 0, 0))
        draw_bullets(player2_bullets, (0, 0, 255))

        # スコア、HP、プレイヤー名、勝利数の表示
        font2 = pygame.font.Font(None, 36)
        player1_info = font2.render(f"{player1_name} HP: {player1_health} Score: {player1_score} Wins: {player1_wins}", True, (255, 255, 255))
        player2_info = font2.render(f"{player2_name} HP: {player2_health} Score: {player2_score} Wins: {player2_wins}", True, (255, 255, 255))
        screen.blit(player1_info, (10, 10))
        screen.blit(player2_info, (screen_width - player2_info.get_width() - 10, 10))

        pygame.display.flip()
        pygame.time.Clock().tick(60)

# ゲーム開始
wait_for_input()
start_game()
game_loop()