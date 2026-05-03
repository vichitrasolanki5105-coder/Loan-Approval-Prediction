// 🔥 LOADING
function showLoading(){
    document.getElementById("loading").style.display = "block";
}

// 🔥 CLOCK
setInterval(()=>{
    document.getElementById("datetime").innerHTML =
    new Date().toLocaleString();
},1000);


// 🔥 MATRIX EFFECT
let c = document.getElementById("matrix");
let ctx = c.getContext("2d");

c.height = window.innerHeight;
c.width = window.innerWidth;

let letters = "01";
let font_size = 14;
let columns = c.width / font_size;
let drops = [];

for(let x = 0; x < columns; x++) drops[x] = 1;

function draw(){
    ctx.fillStyle = "rgba(0,0,0,0.05)";
    ctx.fillRect(0,0,c.width,c.height);

    ctx.fillStyle = "#0f0";
    ctx.font = font_size + "px monospace";

    for(let i = 0; i < drops.length; i++){
        let text = letters[Math.floor(Math.random()*letters.length)];
        ctx.fillText(text, i*font_size, drops[i]*font_size);

        if(drops[i]*font_size > c.height && Math.random() > 0.975)
            drops[i] = 0;

        drops[i]++;
    }
}

setInterval(draw,33);


// 🔥 PIE CHART
let approved = Number("{{ approved | default(0) }}");
let rejected = Number("{{ rejected | default(0) }}");

new Chart(document.getElementById("pieChart"), {
    type:'doughnut',
    data:{
        labels:['Approved','Rejected'],
        datasets:[{data:[approved,rejected]}]
    }
});

// 🔥 CONFETTI + VOICE
let result = "{{ prediction_text }}";

if(result && result !== "" && result !== "None"){

    if(result.includes("Approved")){
        confetti();
        speechSynthesis.speak(new SpeechSynthesisUtterance("Loan Approved"));
    }
    else{
        speechSynthesis.speak(new SpeechSynthesisUtterance("Loan Rejected"));
    }
}