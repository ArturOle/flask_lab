const balls = [];
/* Sets the number of balls to generate */
const numBalls = 300;
/* Sets the colors chosen randomly for the balls */
const colors = ["#636363", "#b5b5b5", "#e0e0e0", "#cfc8b2", "#999999"];

for (let i = 0; i < numBalls; i++) {
    /* Create a new ball element and set its style */
    let ball = document.createElement("div");  
    ball.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    ball.style.left = `${Math.floor(Math.random() * 100)}vw`;
    ball.style.top = `${Math.floor(Math.random() * 100)}vh`;
    ball.style.transform = `scale(${Math.random()})`;
    ball.style.width = `${Math.random()}em`;
    ball.style.height = ball.style.width;  
    ball.style.position = 'absolute';
    ball.style.borderRadius = "100%";
    ball.style.opacity = 0.5;
    ball.style.zIndex = -100;
    balls.push(ball);
    document.body.append(ball);
}

balls.forEach((el, index) => {
    /* Generate random position values that will be used to move the balls around */
    let pos = { 
        x: Math.random() * (index % 2 === 0 ? -2 : 2),
        y: Math.random()
    };
    
    /* 
    ** Move each ball on their X and Y axis with the random values generated previously 
    ** and have it alternate and iterate ifinetely
    */
    let animation = el.animate(
        [
            { transform: "translate(0, 0)" },
            { transform: `translate(${pos.x}rem, ${pos.y}rem)` }
        ],
        {
            duration: (Math.random() + 1) * 2500, // random duration
            direction: "alternate",
            iterations: Infinity,
            easing: "ease-in-out",
            fill: "both"   
        }
    );
});
