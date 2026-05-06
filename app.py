import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="대학교 농구 게임 - 확장판", layout="wide")

# 화면 크기를 1.5배~2배 키운 1200x750 사이즈 적용
game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
        body { margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #2c3e50; font-family: 'Jua', sans-serif; overflow: hidden; }
        
        /* 화면 크기 확장: 1200x750 */
        #gameContainer { position: relative; width: 1200px; height: 750px; background: #ecf0f1; border: 10px solid #34495e; border-radius: 30px; box-shadow: 0 30px 60px rgba(0,0,0,0.6); }
        canvas { border-radius: 20px; cursor: crosshair; }
        
        .ui-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 10; }
        #mainMenu, #gameOver { background: rgba(236, 240, 241, 0.96); border-radius: 20px; }
        
        h1 { font-size: 90px; color: #e67e22; margin-bottom: 20px; text-shadow: 4px 4px #d35400; }
        .best-score { font-size: 36px; color: #7f8c8d; margin-bottom: 40px; }
        
        button { 
            padding: 20px 70px; font-size: 40px; font-family: 'Jua'; cursor: pointer;
            background: #e67e22; color: white; border: none; border-radius: 60px;
            transition: transform 0.2s, background 0.2s; box-shadow: 0 8px #d35400;
        }
        button:hover { background: #d35400; transform: scale(1.05); }
        button:active { transform: translateY(6px); box-shadow: 0 2px #d35400; }
        
        .hidden { display: none !important; }
        #hud { position: absolute; top: 30px; width: 100%; display: flex; justify-content: space-around; pointer-events: none; }
        .stat-box { font-size: 36px; color: #2c3e50; background: rgba(255,255,255,0.8); padding: 10px 40px; border-radius: 30px; border: 3px solid #34495e; }
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
        <div style="font-size: 45px; margin-bottom: 30px;">최종 점수: <span id="finalScore">0</span></div>
        <div style="display: flex; gap: 30px;">
            <button onclick="startGame()">다시하기</button>
            <button onclick="showMain()" style="background: #95a5a6; box-shadow: 0 8px #7f8c8d;">나가기</button>
        </div>
    </div>

    <canvas id="gameCanvas" width="1200" height="750"></canvas>
</div>

<script>
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const gravity = 0.25;
const powerFactor = 0.375; // 2.5배 강화된 기본 힘

// 그룹 설정 업데이트: 색상 및 시간 증가량 변경
const groups = [
    { id: 1, speed: 2.25, addTime: 6, names: ["서울대", "연세대", "고려대", "성균관대", "서강대", "한양대", "중앙대", "시립대", "경희대", "이화여대"], color: "#ff79c6" }, // 핑크 (속도 1.5*1.5=2.25)
    { id: 2, speed: 1.0, addTime: 4, names: ["아주대", "단국대", "항공대", "가천대", "한국공대"], color: "#8be9fd" }, // 하늘색
    { id: 3, speed: 0.6, addTime: 3, names: ["부산대", "경북대", "전남대", "충남대", "전북대"], color: "#50fa7b" }  // 초록색
];

let score = 0, timeLeft = 7, isPlaying = false, bestScore = localStorage.getItem('univBestScore') || 0;
let firedBalls = []; // 날아다니는 공들
let currentBall = null; // 대기 중인 공
let animationId, timerInterval, mousePos = {x:0, y:0};

class Ball {
    constructor() {
        const group = groups[Math.floor(Math.random() * 3)];
        this.name = group.names[Math.floor(Math.random() * group.names.length)];
        this.group = group;
        this.radius = 45; // 화면이 커진 만큼 공 크기도 확장
        this.x = 180;
        this.y = 580;
        this.vx = 0;
        this.vy = 0;
        this.isDragging = false;
        this.isFired = false;
        this.scored = false;
    }

    draw() {
        if (this.isDragging) this.drawTrajectory();
        
        ctx.beginPath(); ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.group.color; // 그룹별 색상 적용
        ctx.fill(); 
        ctx.strokeStyle = "white"; ctx.lineWidth = 4; ctx.stroke();
        
        // 텍스트 디자인
        ctx.fillStyle = "white";
        ctx.font = "bold 18px Jua"; 
        ctx.textAlign = "center";
        ctx.fillText(this.name, this.x, this.y + 7);
    }

    drawTrajectory() {
        const tx = (this.x - mousePos.x) * powerFactor * this.group.speed;
        const ty = (this.y - mousePos.y) * powerFactor * this.group.speed;
        ctx.beginPath(); ctx.setLineDash([8, 12]); ctx.strokeStyle = "rgba(0, 0, 0, 0.2)";
        let tempX = this.x, tempY = this.y, tempVX = tx, tempVY = ty;
        for (let i = 0; i < 40; i++) {
            ctx.moveTo(tempX, tempY);
            tempX += tempVX; tempY += tempVY; tempVY += gravity;
            ctx.lineTo(tempX, tempY);
        }
        ctx.stroke(); ctx.setLineDash([]);
    }

    update() {
        if (this.isFired) {
            this.x += this.vx; this.y += this.vy; this.vy += gravity;
            
            // 골대 충돌 판정 (확장된 화면 좌표 대응)
            if (!this.scored && this.x > 1030 && this.x < 1140 && this.y > 230 && this.y < 310 && this.vy > 0) {
                score++; 
                timeLeft += this.group.addTime;
                this.scored = true;
                document.getElementById('currentScore').innerText = score;
            }
        }
    }
}

function drawHoop() {
    // 확장된 화면의 골대 디자인
    ctx.fillStyle = "white"; ctx.fillRect(1150, 150, 15, 150); // 백보드
    ctx.strokeStyle = "#c0392b"; ctx.lineWidth = 8; ctx.strokeRect(1050, 270, 100, 8); // 림
}

function startGame() {
    score = 0; timeLeft = 7.0; isPlaying = true; firedBalls = [];
    document.getElementById('mainMenu').classList.add('hidden');
    document.getElementById('gameOver').classList.add('hidden');
    document.getElementById('hud').classList.remove('hidden');
    currentBall = new Ball();
    
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
    
    // 바닥
    ctx.fillStyle = "#bdc3c7"; ctx.fillRect(0, 680, 1200, 70);
    
    drawHoop();

    // 대기 중인 공 그리기
    if (currentBall) currentBall.draw();

    // 날아가고 있는 공들 업데이트 및 그리기
    for (let i = firedBalls.length - 1; i >= 0; i--) {
        let b = firedBalls[i];
        b.update();
        b.draw();
        // 화면 밖으로 나가면 제거
        if (b.y > 850 || b.x > 1300 || b.x < -100) {
            firedBalls.splice(i, 1);
        }
    }
    
    animationId = requestAnimationFrame(gameLoop);
}

canvas.addEventListener('mousedown', e => {
    if (!isPlaying || !currentBall) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    if (Math.hypot(mx - currentBall.x, my - currentBall.y) < currentBall.radius) {
        currentBall.isDragging = true;
    }
});

canvas.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    mousePos.x = e.clientX - rect.left;
    mousePos.y = e.clientY - rect.top;
});

canvas.addEventListener('mouseup', e => {
    if (currentBall && currentBall.isDragging) {
        // 속도 설정
        currentBall.vx = (currentBall.x - mousePos.x) * powerFactor * currentBall.group.speed;
        currentBall.vy = (currentBall.y - mousePos.y) * powerFactor * currentBall.group.speed;
        currentBall.isDragging = false;
        currentBall.isFired = true;
        
        // 날아가는 공 리스트에 추가
        firedBalls.push(currentBall);
        
        // 날리자마자 즉시 새로운 공 생성
        currentBall = new Ball();
    }
});

document.getElementById('mainBestScore').innerText = bestScore;
document.getElementById('bestScoreDisplay').innerText = bestScore;
</script>
</body>
</html>
"""

# 확장된 화면 크기에 맞춰 components.html의 높이도 조절 (800px)
components.html(game_html, height=800)
