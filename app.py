import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="대학교 농구 게임 - 하드모드", layout="wide")

game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
        body { margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #2c3e50; font-family: 'Jua', sans-serif; overflow: hidden; }
        #gameContainer { position: relative; width: 1200px; height: 750px; background: #ecf0f1; border: 10px solid #34495e; border-radius: 30px; box-shadow: 0 30px 60px rgba(0,0,0,0.6); }
        canvas { border-radius: 20px; cursor: crosshair; }
        .ui-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 10; }
        #mainMenu, #gameOver { background: rgba(236, 240, 241, 0.96); border-radius: 20px; }
        h1 { font-size: 90px; color: #e67e22; margin-bottom: 20px; text-shadow: 4px 4px #d35400; }
        button { padding: 20px 70px; font-size: 40px; font-family: 'Jua'; cursor: pointer; background: #e67e22; color: white; border: none; border-radius: 60px; box-shadow: 0 8px #d35400; }
        .hidden { display: none !important; }
        #hud { position: absolute; top: 30px; width: 100%; display: flex; justify-content: space-around; pointer-events: none; }
        .stat-box { font-size: 36px; color: #2c3e50; background: rgba(255,255,255,0.8); padding: 10px 40px; border-radius: 30px; border: 3px solid #34495e; }
    </style>
</head>
<body>
<div id="gameContainer">
    <div id="hud" class="hidden">
        <div class="stat-box">점수: <span id="currentScore">0</span></div>
        <div class="stat-box" style="color: #e74c3c;">시간: <span id="timer">7.0</span></div>
        <div class="stat-box">최고기록: <span id="bestScoreDisplay">0</span></div>
    </div>
    <div id="mainMenu" class="ui-layer">
        <h1>UNIV BASKET</h1>
        <div style="font-size:30px; margin-bottom:20px;">공보다 작은 골대에 도전하세요!</div>
        <button onclick="startGame()">게임 시작</button>
    </div>
    <div id="gameOver" class="ui-layer hidden">
        <h1 style="color: #c0392b;">GAME OVER</h1>
        <div style="font-size: 45px; margin-bottom: 30px;">최종 점수: <span id="finalScore">0</span></div>
        <button onclick="startGame()">다시하기</button>
    </div>
    <canvas id="gameCanvas" width="1200" height="750"></canvas>
</div>

<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const gravity = 0.28;
const powerFactor = 0.38;

// 그룹 설정: 로고 텍스트 추가
const groups = [
    { id: 1, speed: 2.25, addTime: 6, names: ["서울대", "연세대", "고려대", "성균관대", "서강대"], logos:["S","Y","K","S","S"], color: "#ff79c6" },
    { id: 2, speed: 1.0, addTime: 4, names: ["아주대", "단국대", "항공대", "가천대", "한국공대"], logos:["A","D","K","G","K"], color: "#8be9fd" },
    { id: 3, speed: 0.6, addTime: 3, names: ["부산대", "경북대", "전남대", "충남대", "전북대"], logos:["B","K","J","C","J"], color: "#50fa7b" }
];

let score = 0, timeLeft = 7, isPlaying = false, bestScore = localStorage.getItem('univBestScore') || 0;
let firedBalls = [];
let currentBall = null;
let mousePos = {x:0, y:0};

// 골대 설정 (콩 크기의 사각형)
const hoop = { x: 1050, y: 300, w: 25, h: 15 }; // 아주 작음
const backboard = { x: 1120, y: 150, w: 15, h: 250 }; // 백보드

class Ball {
    constructor() {
        const gIdx = Math.floor(Math.random() * 3);
        const g = groups[gIdx];
        const nIdx = Math.floor(Math.random() * g.names.length);
        this.name = g.names[nIdx];
        this.logo = g.logos[nIdx];
        this.group = g;
        this.radius = 52; // 공 크기 더 키움
        this.x = 180; this.y = 580;
        this.vx = 0; this.vy = 0;
        this.isDragging = false; this.isFired = false; this.scored = false;
    }

    draw() {
        if (this.isDragging) this.drawTrajectory();
        
        ctx.save();
        // 공 본체
        ctx.beginPath(); ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.group.color; ctx.fill();
        ctx.strokeStyle = "white"; ctx.lineWidth = 5; ctx.stroke();
        
        // 대학교 로고 (가운데 큰 영문)
        ctx.fillStyle = "rgba(255,255,255,0.3)";
        ctx.font = "bold 50px Arial"; ctx.textAlign = "center";
        ctx.fillText(this.logo, this.x, this.y + 18);
        
        // 대학교 이름 (하단 텍스트)
        ctx.fillStyle = "white";
        ctx.font = "bold 22px Jua"; ctx.fillText(this.name, this.x, this.y + 5);
        ctx.restore();
    }

    drawTrajectory() {
        const tx = (this.x - mousePos.x) * powerFactor * this.group.speed;
        const ty = (this.y - mousePos.y) * powerFactor * this.group.speed;
        ctx.beginPath(); ctx.setLineDash([8, 12]); ctx.strokeStyle = "rgba(0,0,0,0.15)";
        let tempX = this.x, tempY = this.y, tempVX = tx, tempVY = ty;
        for (let i = 0; i < 45; i++) {
            ctx.moveTo(tempX, tempY);
            tempX += tempVX; tempY += tempVY; tempVY += gravity;
            ctx.lineTo(tempX, tempY);
        }
        ctx.stroke(); ctx.setLineDash([]);
    }

    update() {
        if (this.isFired) {
            this.x += this.vx; this.y += this.vy; this.vy += gravity;
            
            // 1. 백보드 충돌 (튕기기)
            if (this.x + this.radius > backboard.x && 
                this.x - this.radius < backboard.x + backboard.w &&
                this.y > backboard.y && this.y < backboard.y + backboard.h) {
                this.vx *= -0.6; // 반사 및 속도 감소
                this.x = backboard.x - this.radius; // 겹침 방지
            }

            // 2. 콩만한 골대 골인 판정
            if (!this.scored && 
                this.x > hoop.x && this.x < hoop.x + hoop.w && 
                this.y > hoop.y && this.y < hoop.y + hoop.h && this.vy > 0) {
                score++; timeLeft += this.group.addTime;
                this.scored = true;
                document.getElementById('currentScore').innerText = score;
            }
        }
    }
}

function drawHoopSystem() {
    // 백보드
    ctx.fillStyle = "#34495e";
    ctx.fillRect(backboard.x, backboard.y, backboard.w, backboard.h);
    
    // 콩만한 골대 (사각형)
    ctx.fillStyle = "#e74c3c";
    ctx.fillRect(hoop.x, hoop.y, hoop.w, hoop.h);
    
    // 골대 지지대
    ctx.fillStyle = "#7f8c8d";
    ctx.fillRect(hoop.x + hoop.w, hoop.y + 5, 45, 5);
}

function startGame() {
    score = 0; timeLeft = 7.0; isPlaying = true; firedBalls = [];
    document.getElementById('mainMenu').classList.add('hidden');
    document.getElementById('gameOver').classList.add('hidden');
    document.getElementById('hud').classList.remove('hidden');
    currentBall = new Ball();
    gameLoop();
}

// 타이머 루프 (별도 관리)
setInterval(() => {
    if(isPlaying) {
        timeLeft -= 0.1;
        document.getElementById('timer').innerText = Math.max(0, timeLeft).toFixed(1);
        if (timeLeft <= 0) endGame();
    }
}, 100);

function endGame() {
    isPlaying = false;
    if (score > bestScore) { bestScore = score; localStorage.setItem('univBestScore', bestScore); }
    document.getElementById('finalScore').innerText = score;
    document.getElementById('gameOver').classList.remove('hidden');
}

function gameLoop() {
    if (!isPlaying) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#bdc3c7"; ctx.fillRect(0, 700, 1200, 50); // 바닥
    
    drawHoopSystem();
    if (currentBall) currentBall.draw();

    for (let i = firedBalls.length - 1; i >= 0; i--) {
        firedBalls[i].update();
        firedBalls[i].draw();
        if (firedBalls[i].y > 850 || firedBalls[i].x < -100) firedBalls.splice(i, 1);
    }
    requestAnimationFrame(gameLoop);
}

canvas.addEventListener('mousedown', e => {
    if (!isPlaying || !currentBall) return;
    const rect = canvas.getBoundingClientRect();
    if (Math.hypot(e.clientX - rect.left - currentBall.x, e.clientY - rect.top - currentBall.y) < currentBall.radius) {
        currentBall.isDragging = true;
    }
});

canvas.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    mousePos.x = e.clientX - rect.left; mousePos.y = e.clientY - rect.top;
});

canvas.addEventListener('mouseup', e => {
    if (currentBall && currentBall.isDragging) {
        currentBall.vx = (currentBall.x - mousePos.x) * powerFactor * currentBall.group.speed;
        currentBall.vy = (currentBall.y - mousePos.y) * powerFactor * currentBall.group.speed;
        currentBall.isDragging = false; currentBall.isFired = true;
        firedBalls.push(currentBall);
        currentBall = new Ball();
    }
});

document.getElementById('bestScoreDisplay').innerText = bestScore;
</script>
</body>
</html>
"""

components.html(game_html, height=800)
