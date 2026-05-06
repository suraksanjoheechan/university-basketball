import streamlit as st
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(page_title="대학교 농구 게임", layout="centered")

# HTML/CSS/JS 코드를 변수에 담습니다.
game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
        body { margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #2c3e50; font-family: 'Jua', sans-serif; overflow: hidden; }
        #gameContainer { position: relative; width: 800px; height: 500px; background: #ecf0f1; border: 8px solid #34495e; border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        canvas { border-radius: 12px; cursor: crosshair; }
        .ui-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 10; }
        #mainMenu, #gameOver { background: rgba(236, 240, 241, 0.95); border-radius: 12px; }
        h1 { font-size: 60px; color: #e67e22; margin-bottom: 10px; text-shadow: 2px 2px #d35400; }
        .best-score { font-size: 24px; color: #7f8c8d; margin-bottom: 30px; }
        button { 
            padding: 15px 50px; font-size: 28px; font-family: 'Jua'; cursor: pointer;
            background: #e67e22; color: white; border: none; border-radius: 50px;
            transition: transform 0.2s, background 0.2s; box-shadow: 0 5px #d35400;
        }
        button:hover { background: #d35400; transform: scale(1.05); }
        button:active { transform: translateY(4px); box-shadow: 0 1px #d35400; }
        .hidden { display: none !important; }
        #hud { position: absolute; top: 20px; width: 100%; display: flex; justify-content: space-around; pointer-events: none; }
        .stat-box { font-size: 24px; color: #2c3e50; background: rgba(255,255,255,0.7); padding: 5px 20px; border-radius: 20px; }
    </style>
</head>
<body>
<div id="gameContainer">
    <div id="hud" class="hidden">
        <div class="stat-box">점수: <span id="currentScore">0</span></div>
        <div class="stat-box" style="color: #e74c3c;">시간: <span id="timer">7.0</span>s</div>
        <div class="stat-box">최고기록: <span id="bestScoreDisplay">0</span></div>
    </div>
    <div id="mainMenu" class="ui-layer">
        <h1>UNIV BASKET</h1>
        <div class="best-score">최고 기록: <span id="mainBestScore">0</span></div>
        <button onclick="startGame()">게임 시작</button>
    </div>
    <div id="gameOver" class="ui-layer hidden">
        <h1 style="color: #c0392b;">GAME OVER</h1>
        <div style="font-size: 30px; margin-bottom: 20px;">최종 점수: <span id="finalScore">0</span></div>
        <div style="display: flex; gap: 20px;">
            <button onclick="startGame()">다시하기</button>
            <button onclick="showMain()" style="background: #95a5a6; box-shadow: 0 5px #7f8c8d;">나가기</button>
        </div>
    </div>
    <canvas id="gameCanvas" width="800" height="500"></canvas>
</div>
<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const groups = [
    { id: 1, speed: 1.5, addTime: 7, names: ["서울대", "연세대", "고려대", "성균관대", "서강대", "한양대", "중앙대", "시립대", "경희대", "이화여대"] },
    { id: 2, speed: 1.0, addTime: 5, names: ["아주대", "단국대", "항공대", "가천대", "한국공대"] },
    { id: 3, speed: 0.6, addTime: 4, names: ["부산대", "경북대", "전남대", "충남대", "전북대"] }
];
let score = 0, timeLeft = 7, isPlaying = false, bestScore = localStorage.getItem('univBestScore') || 0;
let ball, animationId, timerInterval;

class Ball {
    constructor() { this.reset(); }
    reset() {
        const group = groups[Math.floor(Math.random() * 3)];
        this.name = group.names[Math.floor(Math.random() * group.names.length)];
        this.group = group;
        this.radius = 35; this.x = 100; this.y = 350;
        this.vx = 0; this.vy = 0; this.isDragging = false; this.isFired = false;
    }
    draw() {
        ctx.beginPath(); ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = "#e67e22"; ctx.fill(); ctx.strokeStyle = "white"; ctx.lineWidth = 3; ctx.stroke();
        ctx.fillStyle = "white"; ctx.font = "14px Jua"; ctx.textAlign = "center";
        ctx.fillText(this.name, this.x, this.y + 5);
    }
    update() {
        if (this.isFired) {
            this.x += this.vx; this.y += this.vy; this.vy += 0.25;
            if (this.x > 680 && this.x < 760 && this.y > 180 && this.y < 220 && this.vy > 0) {
                score++; timeLeft += this.group.addTime;
                document.getElementById('currentScore').innerText = score;
                this.reset();
            }
            if (this.y > 600 || this.x > 850) this.reset();
        }
    }
}
function drawHoop() {
    ctx.strokeStyle = "#c0392b"; ctx.lineWidth = 8; ctx.strokeRect(700, 150, 80, 10);
    ctx.fillStyle = "rgba(255,255,255,0.5)"; ctx.fillRect(770, 80, 10, 100);
}
function startGame() {
    score = 0; timeLeft = 7.0; isPlaying = true;
    document.getElementById('mainMenu').classList.add('hidden');
    document.getElementById('gameOver').classList.add('hidden');
    document.getElementById('hud').classList.remove('hidden');
    ball = new Ball();
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        timeLeft -= 0.1;
        document.getElementById('timer').innerText = Math.max(0, timeLeft).toFixed(1);
        if (timeLeft <= 0) endGame();
    }, 100);
    gameLoop();
}
function endGame() {
    isPlaying = false; clearInterval(timerInterval);
    if (score > bestScore) { bestScore = score; localStorage.setItem('univBestScore', bestScore); }
    document.getElementById('finalScore').innerText = score;
    document.getElementById('gameOver').classList.remove('hidden');
}
function showMain() {
    document.getElementById('gameOver').classList.add('hidden');
    document.getElementById('mainMenu').classList.remove('hidden');
    document.getElementById('hud').classList.add('hidden');
    document.getElementById('mainBestScore').innerText = bestScore;
}
function gameLoop() {
    if (!isPlaying) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#dcdde1"; ctx.fillRect(0, 400, 800, 100);
    drawHoop();
    ball.update(); ball.draw();
    animationId = requestAnimationFrame(gameLoop);
}
canvas.addEventListener('mousedown', e => {
    if (!isPlaying || ball.isFired) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left, mouseY = e.clientY - rect.top;
    if (Math.hypot(mouseX - ball.x, mouseY - ball.y) < ball.radius) {
        ball.isDragging = true; ball.dragStartX = mouseX; ball.dragStartY = mouseY;
    }
});
canvas.addEventListener('mouseup', e => {
    if (ball.isDragging) {
        const rect = canvas.getBoundingClientRect();
        ball.vx = (ball.x - (e.clientX - rect.left)) * 0.15 * ball.group.speed;
        ball.vy = (ball.y - (e.clientY - rect.top)) * 0.15 * ball.group.speed;
        ball.isDragging = false; ball.isFired = true;
    }
});
document.getElementById('mainBestScore').innerText = bestScore;
document.getElementById('bestScoreDisplay').innerText = bestScore;
</script>
</body>
</html>
"""

# Streamlit 화면에 HTML 출력
components.html(game_html, height=550)
