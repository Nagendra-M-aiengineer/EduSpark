let currentQuestion = 1;

const totalQuestions = 5;

let timeRemaining = 600;


const questions =
    document.querySelectorAll(
        ".question-card"
    );

const questionButtons =
    document.querySelectorAll(
        ".q-btn"
    );


const currentQuestionElement =
    document.getElementById(
        "currentQuestion"
    );

const progressBar =
    document.getElementById(
        "questionProgress"
    );

const timerElement =
    document.getElementById(
        "timer"
    );



/* =====================================================
TIMER
===================================================== */

const timer =
    setInterval(() => {

        const minutes =
            Math.floor(
                timeRemaining / 60
            );

        const seconds =
            timeRemaining % 60;


        timerElement.textContent =
            `${minutes}:${seconds
                .toString()
                .padStart(2, "0")}`;


        timeRemaining--;


        if (timeRemaining < 0) {

            clearInterval(timer);

            submitTest();

        }

    }, 1000);



/* =====================================================
SHOW QUESTION
===================================================== */

function showQuestion(number) {

    currentQuestion = number;


    questions.forEach(
        question => {

            question.classList.remove(
                "active-question"
            );

        }
    );


    const question =
        document.querySelector(
            `[data-question="${number}"]`
        );


    if (question) {

        question.classList.add(
            "active-question"
        );

    }


    currentQuestionElement.textContent =
        number;


    const progress =
        (number / totalQuestions) * 100;


    progressBar.style.width =
        `${progress}%`;


    questionButtons.forEach(
        (button, index) => {

            button.classList.remove(
                "active"
            );

            if (index === number - 1) {

                button.classList.add(
                    "active"
                );

            }

        }
    );


    updateAnsweredButtons();
}


/* =====================================================
NEXT
===================================================== */

document
    .getElementById("nextBtn")
    .addEventListener(
        "click",
        () => {

            if (
                currentQuestion <
                totalQuestions
            ) {

                showQuestion(
                    currentQuestion + 1
                );

            }

            else {

                submitTest();

            }

        }
    );



/* =====================================================
PREVIOUS
===================================================== */

document
    .getElementById("previousBtn")
    .addEventListener(
        "click",
        () => {

            if (
                currentQuestion > 1
            ) {

                showQuestion(
                    currentQuestion - 1
                );

            }

        }
    );



/* =====================================================
QUESTION NAVIGATION
===================================================== */

questionButtons.forEach(
    (button, index) => {

        button.addEventListener(
            "click",
            () => {

                showQuestion(
                    index + 1
                );

            }
        );

    }
);



/* =====================================================
ANSWER STATUS
===================================================== */

function updateAnsweredButtons() {

    questionButtons.forEach(
        (button, index) => {

            const answer =
                document.querySelector(
                    `input[name="q${index + 1}"]:checked`
                );


            if (answer) {

                button.classList.add(
                    "answered"
                );

            }

            else {

                button.classList.remove(
                    "answered"
                );

            }

        }
    );
}



document
    .querySelectorAll(
        "input[type='radio']"
    )
    .forEach(
        input => {

            input.addEventListener(
                "change",
                updateAnsweredButtons
            );

        }
    );



/* =====================================================
SUBMIT
===================================================== */

async function submitTest() {

    clearInterval(timer);


    const answers = {};


    for (
        let i = 1;
        i <= totalQuestions;
        i++
    ) {

        const selected =
            document.querySelector(
                `input[name="q${i}"]:checked`
            );


        if (selected) {

            answers[i] =
                selected.value;

        }

    }


    try {

        const response =
            await fetch(
                "/api/mock-test",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        answers
                    })

                }
            );


        const result =
            await response.json();


        document
            .querySelector(".test-layout")
            .style.display = "none";


        const resultScreen =
            document.getElementById(
                "resultScreen"
            );


        resultScreen.classList.add(
            "show"
        );


        document
            .getElementById("score")
            .textContent =
            result.score;


        document
            .getElementById("percentage")
            .textContent =
            `${result.percentage}%`;

    }

    catch (error) {

        alert(
            "Unable to submit test."
        );

    }

}


/* Initial question */

showQuestion(1);