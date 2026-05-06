import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="대학교 농구 게임 - 불규칙 모드", layout="wide")

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
        <div class="stat-box" style="color: #e74c3c;">남은 시간: <span id="timer">15.0</span></div>
        <div class="stat-box">최고기록: <span id="bestScoreDisplay">0</span></div>
    </div>
    <div id="mainMenu" class="ui-layer">
        <h1>UNIV BASKET</h1>
        <div style="font-size:30px; margin-bottom:20px;">15초 안에 최대한 많이 넣으세요! 골대가 불규칙하게 움직입니다.</div>
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

const groups = [
    { id: 1, speed: 2.25, names: ["서울대", "연세대", "고려대", "성균관대", "서강대"], logos:["S","Y","K","S","S"], color: "#ff79c6" },
    { id: 2, speed: 1.0, names: ["아주대", "단국대", "항공대", "가천대", "한국공대"], logos:["A","D","K","G","K"], color: "#8be9fd" },
    { id: 3, speed: 0.6, names: ["부산대", "경북대", "전남대", "충남대", "전북대"], logos:["B","K","J","C","J"], color: "#50fa7b" }
];

let score = 0, timeLeft = 15.0, isPlaying = false, bestScore = localStorage.getItem('univBestScore') || 0;
let firedBalls = [];
let currentBall = null;
let mousePos = {x:0, y:0};

// 골대 상태
let hoopY = 300;
let hoopVelocity = 3; 
let isHoopStopped = false;
let stopTimer = 0;
const hoopRange = { min: 150, max: 500 }; 
const hoopWidth = 80; 
const hoopHeight = 12; // 얇고 납작하게

class Ball {
    constructor() {
        const gIdx = Math.floor(Math.random() * 3);
        const g = groups[gIdx];
        const nIdx = Math.floor(Math.random() * g.names.length);
        this.name = g.names[nIdx];
        this.logo = g.logos[nIdx];
        this.group = g;
        this.radius = 55;
        this.x = 180; this.y = 580;
        this.vx = 0; this.vy = 0;
        this.isDragging = false; this.isFired = false; this.scored = false;
    }

    draw() {
        if (this.isDragging) this.drawTrajectory();
        ctx.save();
        ctx.beginPath(); ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.group.color; ctx.fill();
        ctx.strokeStyle = "white"; ctx.lineWidth = 5; ctx.stroke();
        ctx.fillStyle = "rgba(255,255,255,0.3)";
        ctx.font = "bold 50px Arial"; ctx.textAlign = "center";
        ctx.fillText(this.logo, this.x, this.y + 18);
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
            
            // 백보드 충돌
            if (this.x + this.radius > 1120 && this.x - this.radius < 1135 && this.y > 100 && this.y < 600) {
                this.vx *= -0.6;
                this.x = 1120 - this.radius;
            }

            // 골대 접촉 판정
            if (!this.scored) {
                if (this.x + this.radius > 1040 && this.x - this.radius < 1040 + hoopWidth &&
                    this.y + this.radius > hoopY && this.y - this.radius < hoopY + hoopHeight) {
                    score++;
                    this.scored = true;
                    document.getElementById('currentScore').innerText = score;
                }
            }
        }
    }
}

function updateHoop() {
    if (isHoopStopped) {
        stopTimer--;
        if (stopTimer <= 0) isHoopStopped = false;
        return;
    }

    // 불규칙한 움직임 로직 (매우 낮은 확률)
    let rand = Math.random();
    if (rand < 0.005) { // 0.5% 확률로 갑자기 멈춤
        isHoopStopped = true;
        stopTimer = 40 + Math.random() * 40; 
    } else if (rand < 0.015) { // 1% 확률로 방향 급전환
        hoopVelocity *= -1;
    }

    hoopY += hoopVelocity;

    // 경계 도달 시 방향 전환
    if (hoopY > hoopRange.max) {
        hoopY = hoopRange.max;
        hoopVelocity = -Math.abs(hoopVelocity);
    } else if (hoopY < hoopRange.min) {
        hoopY = hoopRange.min;
        hoopVelocity = Math.abs(hoopVelocity);
    }
}

function drawHoopSystem() {
    // 백보드 지지대
    ctx.fillStyle = "#34495e";
    ctx.fillRect(1120, 100, 15, 500);

    // 골대 그물 (흰색 점선 스타일)
    ctx.beginPath();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.8)";
    ctx.lineWidth = 2;
    for(let i=0; i<=hoopWidth; i+=10) {
        ctx.moveTo(1040 + i, hoopY + hoopHeight);
        ctx.lineTo(1050 + (i*0.8), hoopY + hoopHeight + 50);
    }
    // 가로 그물망 선
    for(let j=15; j<=45; j+=15) {
        ctx.moveTo(1040 + (j/5), hoopY + hoopHeight + j);
        ctx.lineTo(1040 + hoopWidth - (j/5), hoopY + hoopHeight + j);
    }
    ctx.stroke();
    
    // 얇고 납작한 빨간 골대 림
    ctx.fillStyle = "#e74c3c";
    ctx.fillRect(1040, hoopY, hoopWidth, hoopHeight);
    
    // 지지대 연결 부위
    ctx.fillStyle = "#c0392b";
    ctx.fillRect(1040 + hoopWidth, hoopY + 2, 20, 6);
}

function startGame() {
    score = 0; timeLeft = 15.0; isPlaying = true; firedBalls = [];
    document.getElementById('mainMenu').classList.add('hidden');
    document.getElementById('gameOver').classList.add('hidden');
    document.getElementById('hud').classList.remove('hidden');
    currentBall = new Ball();
    gameLoop();
}

// 타이머
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
    ctx.fillStyle = "#bdc3c7"; ctx.fillRect(0, 700, 1200, 50); 
    
    updateHoop();
    drawHoopSystem();
    
    if (currentBall) currentBall.draw();

    for (let i = firedBalls.length - 1; i >= 0; i--) {
        firedBalls[i].update();
        firedBalls[i].draw();
        if (firedBalls[i].y > 850 || firedBalls[i].x < -100 || firedBalls[i].x > 1300) firedBalls.splice(i, 1);
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
